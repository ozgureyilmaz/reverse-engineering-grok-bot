"""Checks that do not rewrite v1. Run after `make` has rebuilt v2 outputs."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from .normalize import corpus_tables
from .paths import NORMALIZED, V2
from .schedule import SCHEDULE_FIELDS, load_prereg, tier_sizes, write_schedule

EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)


def check() -> list[str]:
    problems = []
    runs, products, _queries = corpus_tables()
    shopping = [row for row in products if row["role"] == "shopping"]
    if sum(1 for row in runs if row["role"] == "shopping") != 49:
        problems.append("expected 49 shopping replies")
    if len(shopping) != 228:
        problems.append(f"expected 228 shopping products, got {len(shopping)}")
    cfg = load_prereg()
    sizes = tier_sizes(cfg)
    summary = json.loads((NORMALIZED / "schedule_counts.json").read_text(encoding="utf-8"))
    if summary["schedule_rows"]["full"] != _expected_rows(cfg, sizes, "full"):
        problems.append("full schedule row count does not match the preregistered sizes")
    if summary["schedule_rows"]["mve"] != _expected_rows(cfg, sizes, "mve"):
        problems.append("mve schedule row count does not match the preregistered sizes")
    suffix = cfg["receipt_suffix"].strip()
    seen = set()
    for tier in ("full", "mve"):
        with (NORMALIZED / f"schedule_{tier}.csv").open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        if rows and list(rows[0].keys()) != SCHEDULE_FIELDS:
            problems.append(f"{tier} schedule columns drifted")
        for row in rows:
            if row["run_id"] in seen:
                problems.append(f"duplicate run_id {row['run_id']}")
            seen.add(row["run_id"])
            if not row["prompt_text"].endswith(suffix):
                problems.append(f"{row['run_id']} is missing the receipt suffix")
            if not re.fullmatch(r"FRESH-(US|TR)-\d{3}", row["bot_slot"]):
                problems.append(f"bad bot slot {row['bot_slot']}")
            if row["market"] not in {"US", "TR"}:
                problems.append(f"bad market {row['run_id']}")
    analysis = json.loads((NORMALIZED / "analysis.json").read_text(encoding="utf-8"))
    if analysis["corpus"]["shopping_products"] != 228:
        problems.append("analysis.json shopping product count drifted")
    claims = json.loads((NORMALIZED / "evidence_matrix.json").read_text(encoding="utf-8"))
    matrix = (V2 / "EVIDENCE_MATRIX.md").read_text(encoding="utf-8")
    known_runs = {row["run_id"] for row in runs}
    for claim in claims:
        if claim["id"] not in matrix:
            problems.append(f"{claim['id']} missing from the evidence matrix")
        for token in re.findall(r"`([^`]+)`", claim["ids"]):
            if token in known_runs or token.startswith(("E0", "DOC-", "v1:", "CHECKOUT-", "full-", "mve-")):
                continue
            if "__" in token or token.startswith(("EL", "FA", "GR", "HO", "GI", "np-")):
                problems.append(f"{claim['id']} cites unknown run {token}")
    required = [
        "ARCHITECTURE_ANALYSIS.md", "RANKING_ANALYSIS.md", "RETAILER_BIAS_ANALYSIS.md",
        "EXPERIMENTAL_METHODOLOGY.md", "EVIDENCE_MATRIX.md", "FINAL_FINDINGS.md",
        "figures/architecture.png", "figures/merchant-mix.png", "figures/top1-wilson.png",
        "figures/stability.png", "figures/hhi.png", "figures/price-rank.png",
        "figures/verification.png", "figures/power-curve.png",
        "normalized/schedule_full.csv", "normalized/schedule_mve.csv",
        "normalized/operator_status.json", "normalized/baseline_status.json",
    ]
    for rel in required:
        if not (V2 / rel).exists():
            problems.append(f"missing {rel}")
    operator = json.loads((NORMALIZED / "operator_status.json").read_text(encoding="utf-8"))
    if operator["status"] != "UNEXECUTED":
        problems.append("operator corpus should still be UNEXECUTED")
    for path in V2.rglob("*"):
        if not path.is_file():
            continue
        if "raw" in path.parts or path.suffix not in {".md", ".py", ".yaml", ".yml"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if EMAIL.search(text):
            problems.append(f"email in {path.relative_to(V2)}")
        if UUID.search(text):
            problems.append(f"uuid in {path.relative_to(V2)}")
    write_schedule(cfg, NORMALIZED)
    return problems


def _expected_rows(cfg: dict, sizes: dict, tier: str) -> int:
    total = 0
    n_for = sizes[tier]
    for experiment in cfg["experiments"]:
        families = experiment.get("families") or [{"prompts": experiment["prompts"]}]
        for family in families:
            total += n_for[experiment["role"]] * len(family["prompts"])
    return total


def main() -> int:
    problems = check()
    if problems:
        print("\n".join(problems))
        return 1
    print("v2 ok")
    return 0
