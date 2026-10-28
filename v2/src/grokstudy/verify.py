"""Polite, robots-respecting fetch of product URLs.

This is the independently observed evidence. The bot's receipt is not an input
to the HTTP result except as the list of URLs to request.

Rules:
- Honest User-Agent. No search-engine impersonation.
- http and https only. Private, loopback, and link-local addresses are refused.
- robots.txt is fetched first. A disallow skips the product URL.
- A missing robots.txt (404/410) is treated as allowed.
- A robots.txt of 401/403, or a robots.txt that cannot be fetched, skips the
  product URL. The skip is the observation.
- Crawl-delay is honored up to 8 seconds. A larger delay skips the host.
- At least 1.5 seconds between requests to the same host.
- Response Set-Cookie headers are not stored.
- Stored bodies are capped. The sha256 covers the bytes that were read.
"""
from __future__ import annotations

import gzip
import hashlib
import ipaddress
import json
import re
import socket
import ssl
import threading
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser

USER_AGENT = (
    "GrokShoppingStudy/2.0 "
    "(black-box research; rate-limited; +https://github.com/ozgureyilmaz)"
)
MIN_HOST_DELAY = 1.5
MAX_HONORED_CRAWL_DELAY = 8.0
TIMEOUT = 12
MAX_READ = 1_500_000
STORE_CAP = 250_000
MAX_REDIRECTS = 5

_JSONLD = re.compile(
    r"<script[^>]+type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>",
    re.I | re.S,
)
_META_PRICE = re.compile(
    r"<meta[^>]+(?:property|name)=[\"'](?:product:price:amount|og:price:amount)[\"'][^>]*>",
    re.I,
)
_META_CCY = re.compile(
    r"<meta[^>]+(?:property|name)=[\"'](?:product:price:currency|og:price:currency)[\"'][^>]*>",
    re.I,
)
_CONTENT = re.compile(r"content=[\"']([^\"']+)[\"']", re.I)
_CHALLENGE = re.compile(
    r"(captcha|are you a human|access denied|robot check|cf-challenge|"
    r"just a moment|verify you are human|bot detection)",
    re.I,
)


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.title_parts: list[str] = []
        self._in_title = False
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self._skip += 1
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"} and self._skip:
            self._skip -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._skip:
            return
        if self._in_title:
            self.title_parts.append(data)
        if data.strip():
            self.parts.append(data.strip())


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _public_host(host: str) -> tuple[bool, str]:
    if not host:
        return False, "missing host"
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        return False, f"dns:{exc}"
    addresses = []
    for info in infos:
        ip_text = info[4][0]
        try:
            ip = ipaddress.ip_address(ip_text)
        except ValueError:
            continue
        addresses.append(ip)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return False, f"non_public:{ip}"
    if not addresses:
        return False, "no address"
    return True, ""


def _opener():
    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    return urllib.request.build_opener(_NoRedirect)


def _read_response(response, limit: int) -> tuple[int, dict, bytes]:
    status = getattr(response, "status", None) or response.getcode()
    headers = {k.lower(): v for k, v in response.headers.items()}
    body = response.read(limit + 1)
    return status, headers, body


def _request(url: str, timeout: int) -> tuple[int, dict, bytes, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "identity",
            "Accept-Language": "en",
        },
        method="GET",
    )
    opener = _opener()
    try:
        with opener.open(req, timeout=timeout) as response:
            status, headers, body = _read_response(response, MAX_READ)
            return status, headers, body, ""
    except urllib.error.HTTPError as exc:
        body = exc.read(MAX_READ + 1) if exc.fp else b""
        headers = {k.lower(): v for k, v in exc.headers.items()} if exc.headers else {}
        return exc.code, headers, body, ""
    except Exception as exc:
        return 0, {}, b"", f"{type(exc).__name__}: {exc}"


class _HostGate:
    def __init__(self, min_delay: float) -> None:
        self.min_delay = min_delay
        self._lock = threading.Lock()
        self._next: dict[str, float] = defaultdict(float)
        self._delay: dict[str, float] = {}

    def set_delay(self, host: str, delay: float) -> None:
        with self._lock:
            self._delay[host] = max(self.min_delay, delay)

    def wait(self, host: str) -> None:
        with self._lock:
            delay = self._delay.get(host, self.min_delay)
            now = time.monotonic()
            start = max(now, self._next[host])
            self._next[host] = start + delay
        pause = start - time.monotonic()
        if pause > 0:
            time.sleep(pause)


class _RobotsCache:
    def __init__(self, gate: _HostGate, timeout: int) -> None:
        self.gate = gate
        self.timeout = timeout
        self._lock = threading.Lock()
        self._host_locks: dict[str, threading.Lock] = {}
        self._cache: dict[str, dict] = {}

    def _host_lock(self, host: str) -> threading.Lock:
        with self._lock:
            lock = self._host_locks.get(host)
            if lock is None:
                lock = threading.Lock()
                self._host_locks[host] = lock
            return lock

    def decision(self, url: str) -> dict:
        host = (urlsplit(url).hostname or "").lower()
        with self._host_lock(host):
            record = self._cache.get(host)
            if record is None:
                record = self._fetch(host)
                self._cache[host] = record
        parser = record.get("parser")
        if record["status"] in {"allowed", "robots_unverified"} and parser is not None:
            allowed = bool(parser.can_fetch(USER_AGENT, url))
        else:
            allowed = False
        return {**record, "allowed": allowed}

    def _fetch(self, host: str) -> dict:
        public, why = _public_host(host)
        if not public:
            return {"status": "robots_error", "detail": why, "parser": None, "sha256": "", "http_status": 0}
        robots_url = f"https://{host}/robots.txt"
        status, headers, body, error = 0, {}, b"", ""
        for attempt in range(2):
            self.gate.wait(host)
            status, headers, body, error = _request(robots_url, max(self.timeout, 20))
            if not error and status not in {0, 500, 502, 503, 504}:
                break
        if error:
            parser = RobotFileParser()
            parser.parse([])
            return {
                "status": "robots_unverified",
                "detail": f"{error}; one product fetch attempted",
                "parser": parser,
                "sha256": "",
                "http_status": 0,
            }
        if status in {404, 410}:
            parser = RobotFileParser()
            parser.parse([])
            return {"status": "allowed", "detail": f"no robots.txt ({status})", "parser": parser, "sha256": sha256_bytes(body), "http_status": status}
        if status in {401, 403}:
            return {"status": "robots_forbidden", "detail": f"robots.txt HTTP {status}", "parser": None, "sha256": sha256_bytes(body), "http_status": status}
        if status != 200:
            if status in {500, 502, 503, 504} or status == 0:
                parser = RobotFileParser()
                parser.parse([])
                return {
                    "status": "robots_unverified",
                    "detail": f"robots.txt HTTP {status} after retry; one product fetch attempted",
                    "parser": parser,
                    "sha256": sha256_bytes(body),
                    "http_status": status,
                }
            return {"status": "robots_error", "detail": f"robots.txt HTTP {status}", "parser": None, "sha256": sha256_bytes(body), "http_status": status}
        text = body[:500_000].decode("utf-8", "replace")
        parser = RobotFileParser()
        parser.parse(text.splitlines())
        delay = parser.crawl_delay(USER_AGENT) or parser.crawl_delay("*")
        if delay and delay > MAX_HONORED_CRAWL_DELAY:
            return {
                "status": "robots_error",
                "detail": f"crawl-delay {delay} exceeds {MAX_HONORED_CRAWL_DELAY}s; host skipped",
                "parser": None,
                "sha256": sha256_bytes(body),
                "http_status": status,
            }
        if delay:
            self.gate.set_delay(host, float(delay))
        return {"status": "allowed", "detail": "robots.txt fetched", "parser": parser, "sha256": sha256_bytes(body), "http_status": status}


def _walk_jsonld(node, found: list[dict]) -> None:
    if isinstance(node, list):
        for item in node:
            _walk_jsonld(item, found)
        return
    if not isinstance(node, dict):
        return
    typ = node.get("@type", "")
    types = typ if isinstance(typ, list) else [typ]
    types = [str(t).lower() for t in types]
    if "product" in types or "offer" in types or "aggregateoffer" in types:
        found.append(node)
    for value in node.values():
        if isinstance(value, (dict, list)):
            _walk_jsonld(value, found)


def _offer_price(node: dict) -> tuple[float | None, str, str]:
    offers = node.get("offers", node)
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    if not isinstance(offers, dict):
        return None, "", ""
    raw = offers.get("price", offers.get("lowPrice"))
    currency = str(offers.get("priceCurrency") or "")
    availability = str(offers.get("availability") or "")
    if raw is None and isinstance(offers.get("priceSpecification"), dict):
        spec = offers["priceSpecification"]
        raw = spec.get("price")
        currency = currency or str(spec.get("priceCurrency") or "")
    try:
        price = float(str(raw).replace(",", "")) if raw not in (None, "") else None
    except ValueError:
        price = None
    return price, currency.upper(), availability


def parse_page(body: bytes, content_type: str) -> dict:
    """Extract price, availability, title, and a sponsored flag from HTML bytes."""
    if not body:
        return {
            "price": None, "currency": "", "availability": "", "title": "",
            "sponsored_label": None, "page_kind": "empty", "parse_notes": "empty body",
        }
    text = body.decode("utf-8", "replace")
    prices: list[tuple[float, str, str]] = []
    for match in _JSONLD.finditer(text):
        raw = match.group(1).strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        nodes: list[dict] = []
        _walk_jsonld(data, nodes)
        for node in nodes:
            price, currency, availability = _offer_price(node)
            if price is not None:
                prices.append((price, currency, availability))
    if not prices:
        meta = _META_PRICE.search(text)
        if meta:
            content = _CONTENT.search(meta.group(0))
            if content:
                try:
                    prices.append((float(content.group(1).replace(",", "")), "", ""))
                except ValueError:
                    pass
        meta_c = _META_CCY.search(text)
        if meta_c and prices and not prices[0][1]:
            content = _CONTENT.search(meta_c.group(0))
            if content:
                price, _, availability = prices[0]
                prices[0] = (price, content.group(1).upper(), availability)
    extractor = _TextExtractor()
    try:
        extractor.feed(text[:200_000])
    except Exception:
        pass
    title = re.sub(r"\s+", " ", " ".join(extractor.title_parts)).strip()[:200]
    visible = " ".join(extractor.parts[:40])[:1500]
    challenge = bool(_CHALLENGE.search(title + " " + visible))
    # Absence of the word is not coded as "not sponsored". Product pages
    # usually do not label an ordinary listing, and a challenge page is not a look.
    sponsored = True if re.search(r"\b(sponsored|sponsorlu)\b", visible, re.I) else None
    kind = "challenge" if challenge else "html"
    if content_type and "html" not in content_type and "xml" not in content_type and "text" not in content_type:
        kind = "non_html"
    note = "json-ld" if prices else "no structured price"
    price, currency, availability = prices[0] if prices else (None, "", "")
    if availability and "/" in availability:
        availability = availability.rsplit("/", 1)[-1]
    return {
        "price": price,
        "currency": currency,
        "availability": availability[:80],
        "title": title,
        "sponsored_label": sponsored,
        "page_kind": kind,
        "parse_notes": note,
    }


def _store_body(directory: Path, data: bytes) -> dict:
    directory.mkdir(parents=True, exist_ok=True)
    read = data[:MAX_READ]
    truncated_read = len(data) > MAX_READ
    stored = read[:STORE_CAP]
    digest = sha256_bytes(read)
    stored_digest = sha256_bytes(stored)
    path = directory / f"{digest}.gz"
    if not path.exists():
        path.write_bytes(gzip.compress(stored))
    return {
        "body_sha256": digest,
        "stored_sha256": stored_digest,
        "bytes_read": len(read),
        "read_truncated": truncated_read,
        "store_truncated": len(read) > STORE_CAP,
        "stored_path": str(path.name),
    }


def verify_one(url: str, robots: _RobotsCache, gate: _HostGate, bodies: Path, timeout: int) -> dict:
    fetched_at = now_iso()
    base = {
        "url": url,
        "fetched_at": fetched_at,
        "user_agent": USER_AGENT,
        "evidence_class": "independently_observed",
    }
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"}:
        return {**base, "fetch_status": "error", "error": "unsupported scheme", "http_status": 0}
    public, why = _public_host(parts.hostname or "")
    if not public:
        return {**base, "fetch_status": "error", "error": why, "http_status": 0}
    decision = robots.decision(url)
    if not decision.get("allowed"):
        return {
            **base,
            "fetch_status": "skipped_robots",
            "robots_status": decision.get("status"),
            "robots_detail": decision.get("detail", ""),
            "robots_sha256": decision.get("sha256", ""),
            "http_status": 0,
            "error": "",
        }
    current = url
    hops: list[str] = []
    status = 0
    headers: dict = {}
    body = b""
    error = ""
    for _ in range(MAX_REDIRECTS + 1):
        host = (urlsplit(current).hostname or "").lower()
        public, why = _public_host(host)
        if not public:
            error = why
            break
        hop_decision = robots.decision(current)
        if not hop_decision.get("allowed"):
            return {
                **base,
                "fetch_status": "skipped_robots",
                "robots_status": hop_decision.get("status"),
                "robots_detail": hop_decision.get("detail", ""),
                "robots_sha256": hop_decision.get("sha256", ""),
                "redirect_hops": hops,
                "http_status": status,
                "error": "redirect target disallowed",
            }
        gate.wait(host)
        status, headers, body, error = _request(current, timeout)
        if error:
            break
        if status in {301, 302, 303, 307, 308} and headers.get("location"):
            hops.append(current)
            current = urljoin(current, headers["location"])
            continue
        break
    else:
        error = error or "too many redirects"
    content_type = headers.get("content-type", "")
    stored = _store_body(bodies, body) if body else {
        "body_sha256": "", "stored_sha256": "", "bytes_read": 0,
        "read_truncated": False, "store_truncated": False, "stored_path": "",
    }
    parsed = parse_page(body, content_type) if body and not error else {
        "price": None, "currency": "", "availability": "", "title": "",
        "sponsored_label": None, "page_kind": "empty" if not error else "error",
        "parse_notes": error,
    }
    return {
        **base,
        "fetch_status": "error" if error and status == 0 else "fetched",
        "robots_status": decision.get("status"),
        "robots_detail": decision.get("detail", ""),
        "robots_sha256": decision.get("sha256", ""),
        "http_status": status,
        "final_url": current,
        "redirect_hops": hops,
        "content_type": content_type.split(";")[0][:80],
        "error": error,
        **stored,
        **parsed,
    }


def verify_urls(
    urls: list[str],
    out_dir: Path,
    *,
    workers: int = 4,
    timeout: int = TIMEOUT,
    min_delay: float = MIN_HOST_DELAY,
    resume: bool = True,
) -> list[dict]:
    """Fetch each URL once. Already-indexed URLs are kept when resume is set."""
    out_dir.mkdir(parents=True, exist_ok=True)
    bodies = out_dir / "bodies"
    index_path = out_dir / "index.jsonl"
    done: dict[str, dict] = {}
    if resume and index_path.exists():
        for line in index_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            done[row["url"]] = row
    pending = [url for url in urls if url and url not in done]
    gate = _HostGate(min_delay)
    robots = _RobotsCache(gate, timeout)
    lock = threading.Lock()
    results = list(done.values())

    def _run(url: str) -> dict:
        record = verify_one(url, robots, gate, bodies, timeout)
        with lock:
            with index_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        return record

    if pending:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(_run, url) for url in pending]
            finished = 0
            for future in as_completed(futures):
                results.append(future.result())
                finished += 1
                if finished % 10 == 0 or finished == len(pending):
                    print(f"verified {finished}/{len(pending)} new urls", flush=True)
    return results


def load_index(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows
