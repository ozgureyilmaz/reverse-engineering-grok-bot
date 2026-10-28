"""Check the published files against the receipts and the manifest.

    python3 code/check.py
    python3 code/check.py --write-manifest

Standard library, plus the parser in this directory. Nothing in evidence/ is executed.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from analyze import build_stats
from receipts import load_runs, record_dict, RECORD_FIELDS
import csv
import io

ROOT = Path(__file__).resolve().parents[1]
SKIP_MANIFEST = {"MANIFEST.sha256"}
CITY = re.compile(r"İzmir|Izmir|izmir|İZMİR")
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)
EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
PHONE_WORD = re.compile(r"\b(?:phone|e-mail|email)\b", re.I)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def tracked_files(*, include_v2: bool = False) -> list[Path]:
    """Files attested by the v1 manifest.

    The v2 study lives under v2/ and keeps its own raw files and manifest.
    It is not part of the v1 hash list, so adding v2 does not rewrite the
    published v1 checksums. Redaction scanning can still see v2 source.
    """
    files = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if rel.name in SKIP_MANIFEST:
            continue
        if any(part in {".git", "__pycache__", ".pytest_cache", ".venv"} for part in rel.parts):
            continue
        if "v2" in rel.parts:
            if not include_v2:
                continue
            # Fetched pages and operator replies are third-party or future
            # input. v2/src/grokstudy/check_v2.py scans authored v2 files.
            if "raw" in rel.parts:
                continue
        files.append(path)
    return files


def write_manifest() -> None:
    lines = []
    for path in tracked_files():
        rel = path.relative_to(ROOT).as_posix()
        lines.append(f"{sha256_file(path)}  {rel}")
    (ROOT / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


def check_manifest() -> list[str]:
    manifest = ROOT / "MANIFEST.sha256"
    if not manifest.exists():
        return ["MANIFEST.sha256 is missing"]
    problems = []
    seen = set()
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, rel = line.split("  ", 1)
        seen.add(rel)
        path = ROOT / rel
        if not path.exists():
            problems.append(f"missing {rel}")
            continue
        got = sha256_file(path)
        if got != digest:
            problems.append(f"hash mismatch {rel}")
    expected = {p.relative_to(ROOT).as_posix() for p in tracked_files()}
    for rel in sorted(expected - seen):
        problems.append(f"not in manifest {rel}")
    return problems


def records_text(runs) -> str:
    buf = io.StringIO()
    rows = [record_dict(r, p) for r in runs for p in r.products]
    writer = csv.DictWriter(buf, fieldnames=RECORD_FIELDS, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buf.getvalue()


def check_data() -> list[str]:
    problems = []
    runs = load_runs(ROOT / "evidence" / "transcripts")
    fresh = records_text(runs)
    saved = (ROOT / "data" / "records.csv").read_text(encoding="utf-8")
    if fresh != saved.replace("\r\n", "\n"):
        problems.append("data/records.csv does not match a fresh parse of evidence/transcripts")
    stats = build_stats(runs)
    saved_stats = json.loads((ROOT / "data" / "stats.json").read_text(encoding="utf-8"))
    for key in ("shopping_runs", "shopping_product_rows", "repeat_link_mean", "repeat_brand_mean"):
        if stats[key] != saved_stats[key]:
            problems.append(f"stats.json {key} is stale")
    if stats["pilot_five"]["products"] != 20 or stats["pilot_five"]["hhi"] != 0.08:
        problems.append("pilot slice changed")
    if len(stats["catalog_runs"]) != 3:
        problems.append("expected 3 catalog replies")
    if any(row["day"] != "2026-10-28" for row in stats["catalog_runs"]):
        problems.append("a catalog reply is not dated 28 October")
    for name in (
        "pipeline.png", "domain-mix.png", "overlap-heatmap.png",
        "perturbation-effects.png", "price-spread.png", "query-style.png",
    ):
        if not (ROOT / "figures" / name).exists():
            problems.append(f"missing figures/{name}")
    return problems


def check_redaction() -> list[str]:
    problems = []
    if (ROOT / "CONTEXT_HANDOFF.md").exists():
        problems.append("CONTEXT_HANDOFF.md must not be published")
    for path in tracked_files(include_v2=True):
        rel = path.relative_to(ROOT).as_posix()
        # The scanner itself has to name what it scans for.
        if rel == "code/check.py":
            continue
        if path.suffix not in {".md", ".csv", ".json", ".jsonl", ".py", ".txt"} and path.name != "REDACTIONS.json":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if CITY.search(text):
            problems.append(f"city name in {rel}")
        if UUID.search(text) and path.name != "REDACTIONS.json":
            problems.append(f"uuid in {rel}")
        if EMAIL.search(text):
            problems.append(f"email address in {rel}")
        if "checkout" in path.parts and PHONE_WORD.search(text):
            problems.append(f"phone or email word in {rel}")
    return problems


def main() -> int:
    if "--write-manifest" in sys.argv:
        write_manifest()
        print(f"wrote MANIFEST.sha256 ({len(tracked_files())} files)")
        return 0
    problems = check_redaction() + check_data() + check_manifest()
    if problems:
        print("\n".join(problems))
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
