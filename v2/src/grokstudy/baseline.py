"""Independent search baseline.

No search-engine scrape is performed. A free search API is used only when a
credential is already in the environment. In this study environment none was
present, so the comparison is UNEXECUTED and the file format below is the
harness an operator can fill without this code calling a search engine.

Drop one JSON file per quoted query at v2/raw/baseline/<query_sha256>.json:

    {
      "query": "the quoted string",
      "source": "name of the result list and why its terms allow this use",
      "retrieved_at": "2026-10-28T00:00:00+00:00",
      "results": [{"rank": 1, "url": "https://...", "title": "..."}]
    }

`python -m grokstudy.cli baseline` then joins those lists to the bot's product
URLs for that run. It does not invent ranks.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from .paths import BASELINE_DIR, NORMALIZED

API_ENV = (
    "BRAVE_API_KEY",
    "BRAVE_SEARCH_API_KEY",
    "SERPAPI_API_KEY",
    "SERPAPI_KEY",
    "BING_SEARCH_KEY",
    "GOOGLE_API_KEY",
    "GOOGLE_CSE_ID",
)


def baseline_files(directory: Path | None = None) -> list[Path]:
    root = directory or BASELINE_DIR
    if not root.exists():
        return []
    return sorted(path for path in root.glob("*.json") if path.is_file())


def write_baseline_status(out_dir: Path | None = None) -> dict:
    present = [name for name in API_ENV if os.environ.get(name)]
    files = baseline_files()
    if present:
        source = "credential_present_not_called"
        detail = (
            "A search-API environment variable is set. This harness does not "
            "call it automatically. Put result JSON files in v2/raw/baseline/ "
            "if the API's terms allow the comparison."
        )
    elif files:
        source = "operator_files"
        detail = "Joining operator-supplied result lists. This process did not contact a search engine."
    else:
        source = "none"
        detail = (
            "No compliant search API credential is available in this environment, "
            "and v2/raw/baseline/ has no operator-supplied result lists. "
            "Public result pages were not scraped."
        )
    overlaps = []
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        overlaps.append({
            "file": path.name,
            "query": payload.get("query", ""),
            "source": payload.get("source", ""),
            "n_results": len(payload.get("results") or []),
            "status": "UNJOINED_UNTIL_ANALYSIS",
        })
    status = {
        "evidence_class": "independently_observed" if files else "inferred_model",
        "status": "READY" if files else "UNEXECUTED",
        "source": source,
        "detail": detail,
        "api_env_names_present": present,
        "operator_files": len(files),
        "overlaps": overlaps,
        "file_name_rule": "sha256 of the query UTF-8, plus .json",
        "example_name_for_empty": hashlib.sha256(b"").hexdigest() + ".json",
    }
    out = out_dir or NORMALIZED
    out.mkdir(parents=True, exist_ok=True)
    (out / "baseline_status.json").write_text(
        json.dumps(status, indent=2) + "\n", encoding="utf-8"
    )
    return status
