"""Parse a saved Grok Bot shopping reply into products and searches.

The source of a product row is the reply's RECEIPT, not every URL in the prose.
Pages the bot opened and then dropped stay in the search section. Lines the bot
marks as mentioned but not shown are not rows. Names are HTML-unescaped; the
evidence file keeps the original text.
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path

from domains import classify_store, domain_of, link_key

# Public labels. Transcripts in evidence/ already use these labels.
# Study codenames are accepted so an unredacted header still parses.
BOT_NAMES = {
    "grs-r3-us-fresh": "bot-us-4",
    "grs-np-us-r2": "bot-us-2",
    "grs-r3-us": "bot-us-3",
    "grs-np-us": "bot-us-1",
    "grs-pref-us": "bot-us-pref",
    "grs-r3-tr-fresh": "bot-tr-4",
    "grs-np-tr-r2": "bot-tr-2",
    "grs-r3-tr": "bot-tr-3",
    "grs-np-tr": "bot-tr-1",
    "grs-pref-tr": "bot-tr-pref",
}

# Prompts that were actually sent. Budgets are the figure in the prompt ("under X").
PROMPTS = {
    "EL01-US": ("electronics", "EL01", "US", None, ""),
    "EL01-TR": ("electronics", "EL01", "TR", None, ""),
    "EL02-US": ("electronics", "EL02", "US", 150, "USD"),
    "EL02-TR": ("electronics", "EL02", "TR", 5000, "TRY"),
    "FA01-US": ("fashion", "FA01", "US", None, ""),
    "FA01-TR": ("fashion", "FA01", "TR", None, ""),
    "GR01-US": ("grocery", "GR01", "US", None, ""),
    "GR01-TR": ("grocery", "GR01", "TR", None, ""),
    "HO01-US": ("home", "HO01", "US", None, ""),
    "HO01-TR": ("home", "HO01", "TR", None, ""),
    "GI01-US": ("gifts", "GI01", "US", None, ""),
    "GI01-TR": ("gifts", "GI01", "TR", None, ""),
}
PERTURBATIONS = {
    "FA01-US-X4": ("FA01-US", "budget", 60, "USD"),
    "EL02-US-X3": ("EL02-US", "brand", 150, "USD"),
    "HO01-US-X4": ("HO01-US", "material", None, ""),
    "EL01-US-X2": ("EL01-US", "wording", None, ""),
    "HO01-US-X3": ("HO01-US", "budget", 30, "USD"),
    "EL02-US-X5": ("EL02-US", "store", 150, "USD"),
    "FA01-US-X3": ("FA01-US", "wording", None, ""),
    "EL01-US-X3": ("EL01-US", "urgency", None, ""),
    "GI01-US-X1": ("GI01-US", "budget", 50, "USD"),
    "FA01-TR-X2": ("FA01-TR", "budget", 2000, "TRY"),
    "EL02-TR-X2": ("EL02-TR", "brand", 5000, "TRY"),
    "HO01-TR-X2": ("HO01-TR", "material", None, ""),
    "FA01-TR-X3": ("FA01-TR", "wording", None, ""),
    "EL02-TR-X1": ("EL02-TR", "store", 5000, "TRY"),
    "GR01-TR-X1": ("GR01-TR", "store", None, ""),
    "HO01-TR-X3": ("HO01-TR", "brand", None, ""),
    "EL01-TR-X1": ("EL01-TR", "urgency", None, ""),
}
STORE_REQUIRED = {
    "EL02-US-X5": "bestbuy.com",
    "EL02-TR-X1": "trendyol.com",
    "GR01-TR-X1": "getir.com",
}
BRAND_REQUIRED = {
    "EL02-US-X3": "sony",
    "EL02-TR-X2": "sony",
    "HO01-TR-X3": "tefal",
}

_URL = re.compile(r"https?://[^\s<>\"')\]]+")
_ITEM = re.compile(r"^\s*(?:(\d+)\.\s+|[-•]\s+)(.*\S)\s*$")
_SEARCH_HEADER = re.compile(
    r"(?i)^(?:\d\)\s*)?(?:websites|searches|sites)(?:\s+and\s+(?:searches|sites)|\s+used)\b"
)
_STOP_PRODUCTS = re.compile(
    r"(?i)^(?:also mentioned|mentioned but|\(?mentioned but|also checked)\b"
)
_FULL_CACHE = re.compile(
    r"(?i)no new search|ran no new search|did not run a new search|didn't run a new search|reused the results|reused the earlier"
)
_PRICE = re.compile(
    r"""(?ix)
    (?:from\s+)?
    (?:
        (?P<sym>US\$|\$|₺)\s*
        (?P<n1>[0-9][0-9.,]*)
        (?:\s*[–—-]\s*(?P<n1b>[0-9][0-9.,]*))?
        (?:\s*(?P<c1>USD|TRY|TL|EUR|GBP))?
      |
        (?P<c3>USD|TRY|EUR|GBP)\s*
        (?P<n3>[0-9][0-9.,]*)
        (?:\s*[–—-]\s*(?P<n3b>[0-9][0-9.,]*))?
      |
        (?P<n2>[0-9][0-9.,]*)
        (?:\s*[–—-]\s*(?P<n2b>[0-9][0-9.,]*))?
        \s*(?P<c2>USD|TRY|TL|EUR|GBP|₺)
    )
    """
)
def parse_number(raw: str) -> float | None:
    """'1.299,90' -> 1299.9 ; '1,299.90' -> 1299.9 ; '5.000' -> 5000 ; '49.99' -> 49.99."""
    s = (raw or "").replace(" ", "").replace("\u00a0", "")
    s = re.sub(r"[.,]+$", "", s)
    if not s:
        return None
    if "," in s and "." in s:
        dec = "," if s.rfind(",") > s.rfind(".") else "."
        thou = "." if dec == "," else ","
        s = s.replace(thou, "").replace(dec, ".")
    elif "," in s:
        head, _, tail = s.rpartition(",")
        s = s.replace(",", "") if len(tail) == 3 else head.replace(",", "") + "." + tail
    elif "." in s:
        head, _, tail = s.rpartition(".")
        if len(tail) == 3 and len(head.replace(".", "")) <= 3 * s.count("."):
            s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return None


def _currency(sym: str, code: str) -> str:
    token = (code or sym or "").upper().replace("US$", "USD")
    if token in {"$", "USD"}:
        return "USD"
    if token in {"₺", "TL", "TRY"}:
        return "TRY"
    if token == "EUR" or sym == "€":
        return "EUR"
    if token == "GBP" or sym == "£":
        return "GBP"
    return token


def find_price(text: str) -> tuple[float | None, float | None, str, str]:
    """First currency-anchored amount. Returns low, high, currency, qualifier.

    A match preceded by 'was' or '+' is skipped (a crossed-out price or shipping).
    """
    if not text:
        return None, None, "", ""
    for m in _PRICE.finditer(text):
        prefix = text[max(0, m.start() - 8):m.start()].lower()
        if re.search(r"(?:was|\+)\s*$", prefix):
            continue
        if m.group("sym"):
            low_s, high_s, cur_s, sym = m.group("n1"), m.group("n1b"), m.group("c1"), m.group("sym")
        elif m.group("c3"):
            low_s, high_s, cur_s, sym = m.group("n3"), m.group("n3b"), m.group("c3"), ""
        else:
            low_s, high_s, cur_s, sym = m.group("n2"), m.group("n2b"), m.group("c2"), ""
        low = parse_number(low_s)
        high = parse_number(high_s) if high_s else None
        if low is None:
            continue
        qual = "range" if high is not None else ""
        window = text[max(0, m.start() - 6):m.start()].lower()
        if re.match(r"(?i)from\s", m.group(0) or ""):
            qual = "from" if qual != "range" else "range"
        return low, high, _currency(sym, cur_s or ""), qual
    return None, None, "", ""


def _urls(text: str) -> list[str]:
    out = []
    for raw in _URL.findall(text or ""):
        url = raw.rstrip(".,;:!?")
        if url not in out:
            out.append(url)
    return out


def _split_commas(text: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "(":
            depth += 1
            buf.append(ch)
        elif ch == ")":
            depth = max(0, depth - 1)
            buf.append(ch)
        elif ch == "," and depth == 0 and i + 1 < len(text) and text[i + 1] == " ":
            parts.append("".join(buf).strip())
            buf = []
            i += 1
        else:
            buf.append(ch)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)
    return [p for p in parts if p]


def norm_brand(brand: str) -> str:
    b = re.sub(r"\s+", " ", (brand or "")).strip(" .")
    b = re.sub(r"\s*\(target\)\s*$", "", b, flags=re.I).strip()
    key = b.lower()
    aliases = {
        "anker": "Anker",
        "anker soundcore": "Anker",
        "anker (soundcore)": "Anker",
        "soundcore by anker": "Anker",
        "soundcore": "Anker",
        "a new day": "A New Day",
        "lcw everyday (lc waikiki)": "LC Waikiki",
        "lc waikiki": "LC Waikiki",
        "lcw": "LC Waikiki",
        "t-fal": "Tefal",
        "tefal": "Tefal",
        "brand/publisher not shown on card": "",
    }
    if key in aliases:
        return aliases[key]
    if not b or key in {"unknown", "n/a", "none"}:
        return ""
    return b


_MODEL = re.compile(
    r"""(?ix)
    \b(
        wh-?ch?-?\d{3,}[a-z0-9]* |
        wf-?\d{3,}[a-z0-9]* |
        wh-?\d{3,}[a-z0-9]* |
        a\d{4} |
        q\d{2}i? |
        airpods(?:\s+pro)?(?:\s+\d)?
    )\b
    """
)
_KEY_STOP = {
    "the", "and", "with", "for", "from", "wireless", "bluetooth", "noise",
    "cancelling", "canceling", "over", "ear", "ears", "headphone", "headphones",
    "kulaklik", "kulaklık", "siyah", "black", "white", "beyaz", "kablosuz",
    "women", "womens", "woman", "kadin", "kadın", "elbise", "tava", "inch",
    "cm", "pack", "set", "size", "color", "colour",
}


def product_key(name: str, brand: str) -> str:
    """A coarse identity for the same model across two listings."""
    blob = html.unescape(name or "")
    found = _MODEL.findall(blob)
    b = norm_brand(brand).lower() or "unknown"
    if found:
        tokens = [re.sub(r"[^a-z0-9]", "", m.lower()) for m in found]
        token = max(tokens, key=len)
        return f"{b}|{token}"
    tokens = [
        t for t in re.findall(r"[a-z0-9]+", blob.lower())
        if t not in _KEY_STOP and len(t) > 2
    ]
    return f"{b}|{'-'.join(tokens[:5])}" if tokens else b


@dataclass
class Product:
    rank: int
    product: str
    brand: str
    price: float | None
    price_high: float | None
    currency: str
    price_qualifier: str
    url: str
    alt_urls: str
    domain: str
    store_type: str
    link_key: str
    product_key: str


@dataclass
class Run:
    run_id: str
    source_file: str
    round: str
    role: str
    condition: str
    bot: str
    prompt_id: str
    perturbation: str
    perturbation_id: str
    category: str
    family: str
    intended_market: str
    market: str
    budget: float | None
    budget_currency: str
    store_required: str
    brand_required: str
    sent: str
    received: str
    has_receipt: bool
    carryover: str
    retrieval: str
    searches: list[str] = field(default_factory=list)
    n_steps: int = 0
    n_searches: int = 0
    products: list[Product] = field(default_factory=list)
    bot_text: str = ""
    driver_notes: str = ""
    same_chat_as: str = ""
    warnings: list[str] = field(default_factory=list)


def bot_only(text: str) -> tuple[str, str]:
    """Split operator '## Driver notes' blocks from the bot's own text."""
    bot_lines: list[str] = []
    note_lines: list[str] = []
    skip = False
    for line in text.splitlines(keepends=True):
        if line.startswith("## Driver notes"):
            skip = True
            note_lines.append(line)
            continue
        if skip and line.startswith("## "):
            skip = False
        if skip:
            note_lines.append(line)
        else:
            bot_lines.append(line)
    return "".join(bot_lines), "".join(note_lines)


def _round_of(path: Path) -> str:
    for part in path.parts:
        if part == "round1":
            return "1"
        if part == "round2":
            return "2"
        if part == "round3":
            return "3"
        if part == "checkout":
            return "checkout"
    return ""


def _role_of(path: Path) -> str:
    name = path.name.lower()
    if "memory" in name:
        return "memory"
    if "profile" in name or "setup" in name:
        return "setup"
    if "checkout" in name:
        return "checkout"
    return "shopping"


def _bot_from_header(header: str) -> str:
    """Read the bot from the header line only.

    Driver notes name other bots. A shorter label such as bot-us-3 must not
    win just because it also occurs later in the file.
    """
    m = re.search(r"(?im)^[ \t>*-]*bot:\s*(.+)$", header)
    field = m.group(1) if m else header.split("\n", 1)[0]
    for name in sorted(BOT_NAMES, key=len, reverse=True):
        if re.search(rf"\b{re.escape(name)}\b", field):
            return BOT_NAMES[name]
    for label in sorted(set(BOT_NAMES.values()), key=len, reverse=True):
        if re.search(rf"\b{re.escape(label)}\b", field):
            return label
    return ""


def _ids_from_stem(stem: str) -> tuple[str, str, str]:
    """Return prompt_id, perturbation_id, condition prefix guess."""
    stem = stem.replace("__r1fresh", "").replace("__r2fresh", "")
    stem = re.sub(r"__r\d+$", "", stem)
    if stem.startswith("CHECKOUT-"):
        return stem, "", ""
    if "__" in stem:
        cond, prompt = stem.split("__", 1)
        return prompt, "", cond
    if stem in PERTURBATIONS:
        return PERTURBATIONS[stem][0], stem, ""
    return stem, "", ""


def _condition(prefix: str, prompt_id: str, perturbation_id: str) -> str:
    if prefix in {"np-us", "np-tr", "pref-tr", "pref-us"}:
        return prefix
    blob = " ".join(x for x in (prompt_id, perturbation_id) if x)
    if "-TR" in blob or blob.endswith("TR"):
        return "np-tr"
    if "-US" in blob or blob.endswith("US"):
        return "np-us"
    return prefix


def _step_lines(section: str) -> list[str]:
    lines = []
    for line in section.splitlines():
        if _ITEM.match(line):
            lines.append(line.strip())
    return lines


def _queries(section: str) -> list[str]:
    """Quoted search text. An inch mark (11") is not the start of a query."""
    text = section.replace("“", '"').replace("”", '"').replace("«", '"').replace("»", '"')
    found = []
    for match in re.finditer(r'"([^"]{2,200})"', text):
        prev = text[match.start() - 1:match.start()]
        if prev.isdigit():
            continue
        query = match.group(1).strip()
        if query:
            found.append(query)
    return found


def _retrieval(section: str, queries: list[str]) -> str:
    low = section.lower()
    if re.search(r"product catalog|catalog search|\(catalog", low):
        return "catalog"
    steps = _step_lines(section)
    first = steps[0].lower() if steps else low[:240]
    if "web search" in first:
        if queries and _editorial(queries[0]):
            return "editorial_web"
        return "web"
    if "web search" in low:
        return "web_and_store"
    if section.strip():
        return "store_site"
    return "none"


def _editorial(query: str) -> bool:
    return bool(re.search(
        r"(?i)\b(best|review|reviews|wirecutter|rtings|soundguys|serious eats|well reviewed|en iyi)\b",
        query or "",
    ))


def _parse_product_line(line: str, rank: int) -> Product | None:
    body = _ITEM.match(line)
    text = body.group(2) if body else line.strip()
    if not text:
        return None
    urls = _urls(text)
    bare = _URL.sub(" ", text)
    price, price_high, currency, qual = find_price(bare)
    if not urls and price is None:
        return None
    name, brand = _name_brand(bare, price is not None)
    if not name:
        name = urls[0] if urls else "(unnamed)"
    url = urls[0] if urls else ""
    alt = " ".join(urls[1:])
    dom = domain_of(url)
    brand_n = norm_brand(brand)
    return Product(
        rank=rank,
        product=re.sub(r"\s+", " ", name).strip(" -–—:|"),
        brand=brand.strip(" .") if brand else "",
        price=None if price is None else round(price, 2),
        price_high=None if price_high is None else round(price_high, 2),
        currency=currency,
        price_qualifier=qual,
        url=url,
        alt_urls=alt,
        domain=dom,
        store_type=classify_store(dom, brand or brand_n),
        link_key=link_key(url),
        product_key=product_key(name, brand),
    )


def _name_brand(bare: str, has_price: bool) -> tuple[str, str]:
    text = bare.strip()
    text = re.sub(r"\s+", " ", text).strip(" |")
    if text.count(" | ") >= 2:
        parts = [p.strip() for p in text.split(" | ")]
        name = parts[0]
        brand = parts[1]
        if brand.lower().startswith("http"):
            brand = ""
        return _clean_name(name), _clean_brand(brand)
    if text.count(" — ") >= 2:
        parts = [p.strip() for p in text.split(" — ")]
        return _clean_name(parts[0]), _clean_brand(parts[1])
    cut = text
    m = _PRICE.search(text)
    if m:
        cut = text[:m.start()]
    parts = _split_commas(cut.strip(" ,"))
    while parts and parts[-1].lower() in {"from", "at"}:
        parts.pop()
    if len(parts) >= 2 and re.match(r"(?i)by\s+\S", parts[-1]):
        brand = re.sub(r"(?i)^by\s+", "", parts[-1]).strip(" .")
        name = ", ".join(parts[:-1])
        return _clean_name(name), _clean_brand(brand)
    if len(parts) >= 2:
        return _clean_name(", ".join(parts[:-1])), _clean_brand(parts[-1])
    if parts:
        return _clean_name(parts[0]), ""
    return _clean_name(text), ""


def _clean_name(name: str) -> str:
    name = re.sub(r"[*_`]+", "", name or "")
    name = re.sub(r"\s+", " ", name).strip(" -–—:|,")
    return name[:300]


def _clean_brand(brand: str) -> str:
    brand = re.sub(r"\s+", " ", brand or "").strip(" -–—:|,")
    brand = re.sub(r"(?i)^by\s+", "", brand)
    return brand[:120]


def _products_from_receipt(receipt: str) -> tuple[list[Product], str, list[str]]:
    lines = receipt.splitlines()
    start = 0
    for i, line in enumerate(lines):
        if re.search(r"(?i)products shown", line):
            start = i + 1
            break
    search_at = len(lines)
    for i in range(start, len(lines)):
        if _SEARCH_HEADER.match(lines[i].strip()):
            search_at = i
            break
    products: list[Product] = []
    warnings: list[str] = []
    for line in lines[start:search_at]:
        if not line.strip():
            continue
        if _STOP_PRODUCTS.match(line.strip()):
            break
        if re.match(r"(?i)^\d\)\s", line.strip()):
            continue
        item = _ITEM.match(line)
        if not item and "http" not in line and find_price(line)[0] is None:
            continue
        rank = int(item.group(1)) if item and item.group(1) else len(products) + 1
        parsed = _parse_product_line(line, rank)
        if parsed is None:
            if line.strip() and not line.strip().endswith(":"):
                warnings.append(f"unparsed product line: {line.strip()[:160]}")
            continue
        products.append(parsed)
    search = "\n".join(lines[search_at:])
    return products, search, warnings


def parse_text(text: str, source_file: str = "", run_id: str = "") -> Run:
    raw = text.replace("\r\n", "\n")
    bot, notes = bot_only(raw)
    bot = html.unescape(bot)
    header = bot.split("##", 1)[0]
    stem = Path(source_file).stem if source_file else run_id
    # Filenames keep the study run id, including __r2fresh.
    file_stem = Path(source_file).name[:-3] if source_file.endswith(".md") else stem
    if not run_id:
        run_id = file_stem
    prompt_id, pert_id, prefix = _ids_from_stem(file_stem)
    if pert_id:
        base, variable, p_budget, p_ccy = PERTURBATIONS[pert_id]
        prompt_id = base
    else:
        variable, p_budget, p_ccy = "", None, ""
    meta = PROMPTS.get(prompt_id)
    category, family, locale, b_budget, b_ccy = meta if meta else ("", "", "", None, "")
    budget = p_budget if p_budget is not None else b_budget
    budget_ccy = p_ccy or b_ccy
    role = _role_of(Path(source_file or run_id))
    rnd = _round_of(Path(source_file or ""))
    if role == "checkout":
        prompt_id = file_stem
        variable = "checkout"
        locale = "US" if "US" in file_stem else "TR" if "TR" in file_stem else locale
        category = "checkout"
    condition = _condition(prefix, prompt_id if role != "checkout" else file_stem, pert_id)
    if role == "checkout":
        condition = "np-us" if locale == "US" else "np-tr" if locale == "TR" else condition
    if role in {"memory", "setup"}:
        condition = ""
    sent = _field(header, "sent")
    received = _field(header, "received")
    if not received:
        found = re.search(r"(20\d\d-\d\d-\d\d)", header)
        received = found.group(1) if found else ""
    bot_name = _bot_from_header(header)
    same = ""
    m_same = re.search(r"same chat as ([A-Z0-9_-]+)", header, re.I)
    if m_same:
        same = m_same.group(1)
    receipt_m = re.search(r"(?m)^RECEIPT\s*$", bot)
    has_receipt = receipt_m is not None
    warnings: list[str] = []
    products: list[Product] = []
    search = ""
    if has_receipt:
        products, search, warnings = _products_from_receipt(bot[receipt_m.end():])
    queries = _queries(search) if has_receipt else []
    steps = _step_lines(search) if has_receipt else []
    blob = (search or "") + "\n" + bot[:400]
    if not has_receipt and _FULL_CACHE.search(bot):
        carry = "full"
    elif _FULL_CACHE.search(search or bot):
        carry = "full"
    elif re.search(r"(?i)\bearlier\b", search or ""):
        carry = "partial"
    else:
        carry = "none"
    retrieval = _retrieval(search, queries) if has_receipt else ("none" if carry == "full" else "none")
    currencies = [p.currency for p in products if p.currency]
    observed = ""
    if currencies and len(set(currencies)) == 1:
        observed = "US" if currencies[0] == "USD" else "TR" if currencies[0] == "TRY" else ""
    market = observed or locale
    # A US prompt that comes back entirely in TRY is the location-default confound,
    # not a US observation. EL01-US-X3__r2fresh is the saved case.
    if locale == "US" and observed == "TR" and role == "shopping":
        condition = "location-default"
        market = "TR"
    if not bot_name and condition == "location-default":
        bot_name = "bot-us-4"
    run = Run(
        run_id=run_id,
        source_file=source_file,
        round=rnd,
        role=role,
        condition=condition,
        bot=bot_name,
        prompt_id=prompt_id,
        perturbation=variable,
        perturbation_id=pert_id,
        category=category,
        family=family,
        intended_market=locale,
        market=market,
        budget=budget,
        budget_currency=budget_ccy,
        store_required=STORE_REQUIRED.get(pert_id, ""),
        brand_required=BRAND_REQUIRED.get(pert_id, ""),
        sent=sent,
        received=received,
        has_receipt=has_receipt,
        carryover=carry,
        retrieval=retrieval,
        searches=queries,
        n_steps=0 if carry == "full" and not steps else len(steps),
        n_searches=0 if carry == "full" and not queries else len(queries),
        products=products,
        bot_text=bot,
        driver_notes=notes,
        same_chat_as=same,
        warnings=warnings,
    )
    if carry == "full":
        # Quoted strings in a no-new-search reply name the earlier queries.
        run.searches = []
        run.n_searches = 0
        run.n_steps = 0
        run.retrieval = "cached"
    return run


def _field(header: str, name: str) -> str:
    m = re.search(rf"(?im)^-?\s*{name}:\s*(.+)$", header)
    if not m:
        m = re.search(rf"(?i)\b{name}:\s*([^;\n]+)", header)
    return m.group(1).strip() if m else ""


def parse_file(path: Path, root: Path | None = None) -> Run:
    text = path.read_text(encoding="utf-8")
    rel = str(path.relative_to(root)) if root else str(path)
    return parse_text(text, source_file=rel, run_id=path.stem)


def iter_transcripts(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.md") if p.is_file())


def load_runs(root: Path) -> list[Run]:
    return [parse_file(p, root) for p in iter_transcripts(root)]


RECORD_FIELDS = [
    "run_id", "round", "condition", "bot", "prompt_id", "perturbation", "rank",
    "product", "brand", "price", "currency", "domain", "url", "searches",
    "n_steps", "n_searches", "market", "intended_market", "category", "family",
    "role", "perturbation_id", "brand_norm", "price_high", "price_qualifier",
    "store_type", "link_key", "product_key", "alt_urls", "retrieval",
    "carryover", "budget", "budget_currency", "received", "source_file",
]


def record_dict(run: Run, product: Product) -> dict:
    searches = " || ".join(run.searches)
    return {
        "run_id": run.run_id,
        "round": run.round,
        "condition": run.condition,
        "bot": run.bot,
        "prompt_id": run.prompt_id,
        "perturbation": run.perturbation,
        "rank": product.rank,
        "product": product.product,
        "brand": product.brand,
        "price": "" if product.price is None else f"{product.price:.2f}",
        "currency": product.currency,
        "domain": product.domain,
        "url": product.url,
        "searches": searches,
        "n_steps": run.n_steps,
        "n_searches": run.n_searches,
        "market": run.market,
        "intended_market": run.intended_market,
        "category": run.category,
        "family": run.family,
        "role": run.role,
        "perturbation_id": run.perturbation_id,
        "brand_norm": norm_brand(product.brand),
        "price_high": "" if product.price_high is None else f"{product.price_high:.2f}",
        "price_qualifier": product.price_qualifier,
        "store_type": product.store_type,
        "link_key": product.link_key,
        "product_key": product.product_key,
        "alt_urls": product.alt_urls,
        "retrieval": run.retrieval,
        "carryover": run.carryover,
        "budget": "" if run.budget is None else run.budget,
        "budget_currency": run.budget_currency,
        "received": run.received,
        "source_file": run.source_file,
    }


def run_dict(run: Run) -> dict:
    data = asdict(run)
    data.pop("products", None)
    data.pop("bot_text", None)
    data.pop("driver_notes", None)
    data["n_products"] = len(run.products)
    data["searches"] = " || ".join(run.searches)
    data["domains"] = " ".join(sorted({p.domain for p in run.products if p.domain}))
    data["warnings"] = " | ".join(run.warnings)
    return data
