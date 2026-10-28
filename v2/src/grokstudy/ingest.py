"""Ingest operator replies saved as v2/raw/replies/<run_id>.md.

An empty replies directory is the expected state until the operator runs the
schedule. That state is UNEXECUTED, not a zero effect.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from .paths import NORMALIZED, V1_CODE

if str(V1_CODE) not in sys.path:
    sys.path.insert(0, str(V1_CODE))

from receipts import parse_file  # noqa: E402

LOG_FIELDS = [
    "run_id", "experiment_id", "bot_slot", "market", "market_cue", "sent_at",
    "received_at", "wording_variant", "time_block", "date_stratum",
    "preference_outcome", "operator_notes",
]


def read_run_log(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as handle:
        return {row["run_id"]: row for row in csv.DictReader(handle) if row.get("run_id")}


def ingest_replies(replies_dir: Path, run_log_path: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(
        path for path in replies_dir.glob("*.md")
        if path.is_file() and path.name.lower() != "readme.md"
    )
    log = read_run_log(run_log_path)
    rows = []
    warnings = []
    for path in files:
        run = parse_file(path, replies_dir)
        logged = log.get(run.run_id)
        if logged is None:
            warnings.append(f"{run.run_id} has no run-log row")
        rows.append({
            "run_id": run.run_id,
            "source_file": path.name,
            "n_products": len(run.products),
            "has_receipt": run.has_receipt,
            "retrieval": run.retrieval,
            "sent_at": (logged or {}).get("sent_at", ""),
            "received_at": (logged or {}).get("received_at", ""),
            "bot_slot": (logged or {}).get("bot_slot", ""),
            "market_cue": (logged or {}).get("market_cue", ""),
            "experiment_id": (logged or {}).get("experiment_id", ""),
            "evidence_class": "bot_self_report",
            "corpus": "v2_operator",
        })
    status = {
        "status": "UNEXECUTED" if not files else "INGESTED",
        "n_replies": len(files),
        "n_with_receipt": sum(1 for row in rows if row["has_receipt"]),
        "warnings": warnings,
        "evidence_class": "bot_self_report",
        "note": "No operator reply is analysed as a v2 result until it is in this directory.",
    }
    (out_dir / "operator_status.json").write_text(
        json.dumps(status, indent=2) + "\n", encoding="utf-8"
    )
    with (out_dir / "operator_runs.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = list(rows[0].keys()) if rows else [
            "run_id", "source_file", "n_products", "has_receipt", "retrieval",
            "sent_at", "received_at", "bot_slot", "market_cue", "experiment_id",
            "evidence_class", "corpus",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return status
