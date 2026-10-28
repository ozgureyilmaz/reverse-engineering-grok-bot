"""Command line for the v2 study. `python -m grokstudy.cli <command>`."""
from __future__ import annotations

import csv
import json
import sys

from .paths import (
    NORMALIZED,
    REPLIES,
    RUN_LOG,
    V1_RECORDS,
    VERIFICATION,
    VERIFICATION_INDEX,
)
from .schedule import write_schedule


def _product_urls() -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    with V1_RECORDS.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("role") not in {"shopping", "checkout"}:
                continue
            url = (row.get("url") or "").strip()
            if url and url not in seen:
                seen.add(url)
                ordered.append(url)
    return ordered


def cmd_schedule() -> int:
    summary = write_schedule()
    print(json.dumps(summary["schedule_rows"]))
    print(f"per-cell sizes {summary['sizes_per_market_cell']}")
    return 0


def cmd_verify() -> int:
    from .verify import verify_urls

    urls = _product_urls()
    print(f"unique product urls {len(urls)}", flush=True)
    verify_urls(urls, VERIFICATION, workers=4, resume=True)
    print(f"index {VERIFICATION_INDEX}")
    return 0


def cmd_normalize() -> int:
    from .normalize import write_normalized
    write_normalized()
    return 0


def cmd_ingest() -> int:
    from .ingest import ingest_replies
    summary = ingest_replies(REPLIES, RUN_LOG, NORMALIZED)
    print(json.dumps(summary))
    return 0


def cmd_baseline() -> int:
    from .baseline import write_baseline_status
    print(json.dumps(write_baseline_status()))
    return 0


def cmd_analyze() -> int:
    from .analysis import write_analysis
    write_analysis()
    return 0


def cmd_figures() -> int:
    from .figures import draw_all
    draw_all()
    return 0


def cmd_report() -> int:
    from .reports import write_reports
    write_reports()
    return 0


def cmd_check() -> int:
    from .check_v2 import main as check_main
    return check_main()


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    commands = {
        "schedule": cmd_schedule,
        "verify": cmd_verify,
        "normalize": cmd_normalize,
        "ingest": cmd_ingest,
        "baseline": cmd_baseline,
        "analyze": cmd_analyze,
        "figures": cmd_figures,
        "report": cmd_report,
        "check": cmd_check,
    }
    if not argv or argv[0] not in commands:
        print("usage: python -m grokstudy.cli " + "|".join(commands))
        return 2
    return commands[argv[0]]()


if __name__ == "__main__":
    raise SystemExit(main())
