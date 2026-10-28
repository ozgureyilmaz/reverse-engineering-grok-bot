"""Turn the preregistration into a deterministic run schedule.

The stimuli are fixed in the YAML. This module randomises order and deals
time blocks and date strata. The same seed reproduces the same files.
"""
from __future__ import annotations

import csv
import hashlib
import json
import random
from pathlib import Path

import yaml

from .paths import NORMALIZED, PREREG
from .power import expected_half_width, n_for_difference, n_for_proportion

SCHEDULE_FIELDS = [
    "tier", "run_id", "experiment_id", "experiment_title", "bot_slot", "market",
    "market_cue", "prompt_text", "setup_prompt", "wording_variant", "time_block",
    "date_stratum", "bot_preparation", "family", "specificity", "constraint",
    "negative_control", "open_ended", "supports", "operator_rule",
]


def load_prereg(path: Path | None = None) -> dict:
    return yaml.safe_load((path or PREREG).read_text(encoding="utf-8"))


def tier_sizes(cfg: dict) -> dict[str, dict[str, int]]:
    """Map tier -> role -> number of runs per market cell."""
    spec = cfg["sample_size"]
    p = float(spec["worst_case_p"])
    out = {}
    for tier in ("full", "mve"):
        block = spec[tier]
        out[tier] = {
            "primary": n_for_proportion(float(block["primary_half_width"]), p=p),
            "secondary": n_for_proportion(float(block["secondary_half_width"]), p=p),
            "probe": int(block["probe_n"]),
        }
    ref = spec["difference_reference"]
    out["difference_per_arm"] = n_for_difference(
        float(ref["delta"]),
        p1=float(ref["p1"]),
        p2=float(ref["p2"]),
        power=float(ref["power"]),
        alpha=float(ref["alpha"]),
    )
    out["half_widths"] = {
        tier: {
            role: None if role == "probe" else expected_half_width(n, p=p)
            for role, n in sizes.items()
        }
        for tier, sizes in out.items()
        if tier in {"full", "mve"}
    }
    return out


def _rng(seed: int, *parts: str) -> random.Random:
    text = "|".join([str(seed), *parts])
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return random.Random(int(digest[:16], 16))


def _cells(experiment: dict) -> list[dict]:
    """One dict per family inside an experiment. Single-family experiments wrap themselves."""
    if experiment.get("families"):
        cells = []
        for family in experiment["families"]:
            cells.append({
                "family": family["id"],
                "open_ended": bool(family.get("open_ended", False)),
                "prompts": family["prompts"],
            })
        return cells
    return [{
        "family": experiment["family"],
        "open_ended": bool(experiment.get("open_ended", False)),
        "prompts": experiment["prompts"],
    }]


def _deal(labels: list[str], n: int, rng: random.Random) -> list[str]:
    seq: list[str] = []
    while len(seq) < n:
        batch = list(labels)
        rng.shuffle(batch)
        seq.extend(batch)
    return seq[:n]


def build_tier(cfg: dict, tier: str) -> list[dict]:
    sizes = tier_sizes(cfg)
    n_for = sizes[tier]
    seed = int(cfg["seed"])
    suffix = cfg["receipt_suffix"].strip()
    groups: dict[str, list[dict]] = {}
    for experiment in cfg["experiments"]:
        role = experiment["role"]
        n = n_for[role]
        supports = "|".join(experiment.get("supports") or [])
        for cell in _cells(experiment):
            for market, prompt in cell["prompts"].items():
                key = f"{experiment['id']}|{cell['family']}|{market}"
                rng = _rng(seed, tier, key)
                blocks = _deal(list(cfg["time_blocks"]), n, rng)
                dates = (
                    _deal(list(cfg["date_strata"]), n, rng)
                    if experiment.get("assign_date_strata")
                    else [""] * n
                )
                rows = []
                for index in range(n):
                    run_id = f"{tier}-{experiment['id']}-{cell['family']}-{market}-{index + 1:03d}"
                    text = prompt["text"].strip() + "\n\n" + suffix
                    setup = ""
                    if experiment.get("preparation") == "save_preference_note":
                        setup = (experiment.get("setup_prompts") or {}).get(market, "").strip()
                    rows.append({
                        "tier": tier,
                        "run_id": run_id,
                        "experiment_id": experiment["id"],
                        "experiment_title": experiment["title"],
                        "bot_slot": "",
                        "market": market,
                        "market_cue": prompt["market_cue"],
                        "prompt_text": text,
                        "setup_prompt": setup,
                        "wording_variant": experiment.get("wording", ""),
                        "time_block": blocks[index],
                        "date_stratum": dates[index],
                        "bot_preparation": experiment.get("preparation", "blank"),
                        "family": cell["family"],
                        "specificity": experiment.get("specificity", ""),
                        "constraint": experiment.get("constraint", ""),
                        "negative_control": bool(experiment.get("negative_control", False)),
                        "open_ended": cell["open_ended"],
                        "supports": supports,
                        "operator_rule": experiment.get("operator_rule", ""),
                    })
                rng.shuffle(rows)
                groups[key] = rows
    keys = sorted(groups)
    _rng(seed, tier, "order").shuffle(keys)
    ordered: list[dict] = []
    pointers = {key: 0 for key in keys}
    remaining = sum(len(rows) for rows in groups.values())
    while remaining:
        for key in keys:
            index = pointers[key]
            if index < len(groups[key]):
                ordered.append(groups[key][index])
                pointers[key] = index + 1
                remaining -= 1
    counters = {"US": 0, "TR": 0}
    for row in ordered:
        counters[row["market"]] += 1
        row["bot_slot"] = f"FRESH-{row['market']}-{counters[row['market']]:03d}"
    return ordered


def write_schedule(cfg: dict | None = None, out_dir: Path | None = None) -> dict:
    cfg = cfg or load_prereg()
    out_dir = out_dir or NORMALIZED
    out_dir.mkdir(parents=True, exist_ok=True)
    sizes = tier_sizes(cfg)
    counts = {"full": 0, "mve": 0, "by_experiment": {}}
    for tier in ("full", "mve"):
        rows = build_tier(cfg, tier)
        path = out_dir / f"schedule_{tier}.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=SCHEDULE_FIELDS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        counts[tier] = len(rows)
        for row in rows:
            bucket = counts["by_experiment"].setdefault(tier, {})
            bucket[row["experiment_id"]] = bucket.get(row["experiment_id"], 0) + 1
    contrasts = []
    for item in cfg.get("analysis_only", []):
        contrasts.append({
            "experiment_id": item["id"],
            "title": item["title"],
            "uses": item["uses"],
            "estimand": item["estimand"],
            "extra_runs": 0,
            "status": "UNEXECUTED",
        })
    (out_dir / "contrasts.json").write_text(
        json.dumps(contrasts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    summary = {
        "evidence_class": "inferred_model",
        "sizes_per_market_cell": {tier: sizes[tier] for tier in ("full", "mve")},
        "difference_per_arm_reference": sizes["difference_per_arm"],
        "expected_half_width_at_p_0_5": sizes["half_widths"],
        "schedule_rows": {"full": counts["full"], "mve": counts["mve"]},
        "rows_by_experiment": counts["by_experiment"],
        "status": "UNEXECUTED",
        "note": "These runs have not been sent. The CSVs are the operator schedule.",
    }
    (out_dir / "schedule_counts.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary
