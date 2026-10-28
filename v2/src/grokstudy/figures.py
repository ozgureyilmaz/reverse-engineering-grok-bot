"""Figures for the v2 reanalysis. Every series is read from normalized JSON."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

from .paths import FIGURES, NORMALIZED
from .power import expected_half_width, n_for_proportion

INK = "#1c1917"
MUTED = "#57534e"
NAVY = "#1e3a4c"
RUST = "#b85c38"
TEAL = "#2f6f5e"
GOLD = "#a6843d"
SAND = "#e7e0d4"

COHORT_LABELS = {
    "us-r1": "US first",
    "us-r2": "US fresh",
    "tr-r1": "TR first",
    "tr-r2": "TR fresh",
    "pref-tr": "TR pref",
    "round3-oct22": "Perturb 22",
    "round3-oct28": "Perturb 28",
    "location-default": "No-country",
}
MERCHANT_COLOR = {
    "retailer": NAVY,
    "marketplace": RUST,
    "brand_site": TEAL,
    "price_comparison": GOLD,
    "editorial": "#7c6f64",
    "unknown": SAND,
}


def _font() -> None:
    regular = Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf")
    if regular.exists():
        font_manager.fontManager.addfont(str(regular))
        plt.rcParams["font.family"] = "Liberation Serif"
    plt.rcParams.update({
        "axes.edgecolor": INK,
        "axes.labelcolor": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "text.color": INK,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    })


def _save(fig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=140, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _footer(fig, text: str) -> None:
    fig.text(0.01, 0.01, text, color=MUTED, fontsize=8, ha="left", va="bottom")


def architecture(path: Path) -> None:
    _font()
    fig, ax = plt.subplots(figsize=(11.2, 4.8))
    ax.set_xlim(0, 112)
    ax.set_ylim(0, 40)
    ax.axis("off")
    stages = [
        (2, "Want"),
        (18, "Query"),
        (34, "Sources"),
        (50, "Filter"),
        (66, "Rank"),
        (82, "Present"),
        (98, "Hand back"),
    ]
    for x, title in stages:
        ax.add_patch(plt.Rectangle((x, 16), 13, 12, fill=False, edgecolor=NAVY, linewidth=1.2))
        ax.text(x + 6.5, 22, title, ha="center", va="center", fontsize=11, color=INK)
    ax.annotate("", xy=(18, 22), xytext=(15, 22), arrowprops=dict(arrowstyle="->", color=NAVY))
    for x in (34, 50, 66, 82, 98):
        ax.annotate("", xy=(x, 22), xytext=(x - 3, 22), arrowprops=dict(arrowstyle="->", color=NAVY))
    ax.text(56, 33, "Visible stages in the receipt. Not seven measured modules.", ha="center", fontsize=12)
    ax.text(
        56, 8,
        "Sources split in this corpus: one retailer, editorial web, marketplace, and a self-reported catalog phrase on 28 Oct.",
        ha="center", fontsize=9, color=MUTED,
    )
    _footer(fig, "Diagram of competing descriptions. Evidence class: bot self-report, except where a later figure says otherwise.")
    _save(fig, path)


def merchant_mix(analysis: dict, path: Path) -> None:
    _font()
    cohorts = [key for key in COHORT_LABELS if key in analysis["cohorts"]]
    classes = ["retailer", "marketplace", "brand_site", "price_comparison", "editorial", "unknown"]
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    import numpy as np
    x = np.arange(len(cohorts))
    bottom = np.zeros(len(cohorts))
    for label in classes:
        heights = []
        for cohort in cohorts:
            slot = analysis["cohorts"][cohort]["merchant_product_slots"].get(label, {})
            heights.append(slot.get("share") or 0)
        ax.bar(x, heights, bottom=bottom, color=MERCHANT_COLOR[label], width=0.72, label=label)
        bottom += np.array(heights)
    ax.set_xticks(x)
    ax.set_xticklabels([COHORT_LABELS[key] for key in cohorts], rotation=30, ha="right")
    ax.set_ylabel("Share of shown product rows")
    ax.set_ylim(0, 1)
    ax.legend(frameon=False, ncol=3, fontsize=8)
    ax.set_title("Merchant class of shown URLs, by cohort")
    _footer(fig, "Bot self-report. Walmart and Getir are coded retailer in v2. Single-bot cohorts are not population shares.")
    _save(fig, path)


def top1(analysis: dict, path: Path) -> None:
    _font()
    cohorts = [key for key in ("us-r1", "us-r2", "tr-r1", "tr-r2", "pref-tr") if key in analysis["cohorts"]]
    classes = ["retailer", "marketplace", "brand_site", "price_comparison"]
    fig, ax = plt.subplots(figsize=(10.2, 5.2))
    import numpy as np
    width = 0.18
    xs = np.arange(len(cohorts))
    for index, label in enumerate(classes):
        centers = xs + (index - 1.5) * width
        ps, los, his = [], [], []
        for cohort in cohorts:
            cell = analysis["cohorts"][cohort]["top1_merchant"][label]
            ps.append(0 if cell["p"] is None else cell["p"])
            los.append(0 if cell["low"] is None else cell["low"])
            his.append(0 if cell["high"] is None else cell["high"])
        yerr = np.vstack([
            np.array(ps) - np.array(los),
            np.array(his) - np.array(ps),
        ])
        ax.bar(centers, ps, width=width, color=MERCHANT_COLOR[label], label=label, yerr=yerr, capsize=2, ecolor=MUTED)
    ax.set_xticks(xs)
    ax.set_xticklabels([COHORT_LABELS[key] for key in cohorts])
    ax.set_ylabel("P(rank 1 merchant class)")
    ax.set_ylim(0, 1)
    ax.legend(frameon=False, ncol=2, fontsize=8)
    ax.set_title("Top-1 merchant class with Wilson 95% intervals")
    _footer(fig, "Intervals treat replies as independent. us-r1, us-r2, tr-r1, tr-r2, and pref-tr are one bot each.")
    _save(fig, path)


def stability(analysis: dict, path: Path) -> None:
    _font()
    fig, ax = plt.subplots(figsize=(10.2, 5.0))
    pairs = []
    for market in ("US", "TR"):
        pairs.extend(analysis["stability"].get(market, {}).get("pairs", []))
    labels = [row["pair_id"] for row in pairs]
    import numpy as np
    x = np.arange(len(pairs))
    ax.bar(x - 0.15, [row["link_jaccard"] or 0 for row in pairs], width=0.3, color=NAVY, label="Link Jaccard")
    ax.bar(x + 0.15, [row["rbo_p90"] or 0 for row in pairs], width=0.3, color=TEAL, label="RBO p=0.9")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=40, ha="right")
    ax.set_ylim(0, 1)
    ax.set_ylabel("Overlap")
    ax.legend(frameon=False)
    ax.set_title("Fresh-bot repeats: link overlap")
    _footer(fig, "Bot self-report. Kendall tau is undefined for most pairs because the shared link set has fewer than two URLs.")
    _save(fig, path)


def hhi_fig(analysis: dict, path: Path) -> None:
    _font()
    cohorts = [key for key in ("us-r1", "us-r2", "tr-r1", "tr-r2", "pref-tr") if key in analysis["cohorts"]]
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    import numpy as np
    x = np.arange(len(cohorts))
    points, los, his = [], [], []
    for cohort in cohorts:
        boot = analysis["cohorts"][cohort]["domain_hhi_bootstrap"]
        points.append(boot["point"] or 0)
        los.append(boot["low"] if boot["low"] is not None else boot["point"] or 0)
        his.append(boot["high"] if boot["high"] is not None else boot["point"] or 0)
    yerr = np.vstack([np.array(points) - np.array(los), np.array(his) - np.array(points)])
    ax.bar(x, points, color=NAVY, yerr=yerr, capsize=3, ecolor=RUST)
    ax.set_xticks(x)
    ax.set_xticklabels([COHORT_LABELS[key] for key in cohorts])
    ax.set_ylabel("Domain HHI of shown rows")
    ax.set_ylim(0, 1)
    ax.set_title("Retailer concentration inside each cohort")
    _footer(fig, "Bootstrap resamples replies. A single-bot cohort's interval is within-chat variation, not a cross-bot CI.")
    _save(fig, path)


def price_rank(analysis: dict, path: Path) -> None:
    _font()
    tests = analysis["within_list_price"]["tests"]
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    labels = ["Rank 1 is unique cheapest", "Rank 1 is unique dearest"]
    keys = ["cheapest", "dearest"]
    observed = [tests[key]["k"] for key in keys]
    nulls = [tests[key]["null_mean"] for key in keys]
    import numpy as np
    x = np.arange(2)
    ax.bar(x - 0.15, observed, width=0.3, color=NAVY, label="Observed replies")
    ax.bar(x + 0.15, nulls, width=0.3, color=SAND, label="Shuffle mean")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Replies")
    ax.legend(frameon=False)
    ax.set_title("Price position inside the shown list")
    n0 = tests["cheapest"]["n_lists"]
    p0 = tests["cheapest"]["p_one_sided"]
    _footer(fig, f"Within-list permutation. Informative lists for cheapest: {n0}. One-sided p={p0}. Shown set only.")
    _save(fig, path)


def verification(analysis: dict, path: Path) -> None:
    _font()
    outcomes = analysis["verification"]["outcomes_unique_urls"]
    labels = list(outcomes.keys())
    values = [outcomes[key] for key in labels]
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    ax.barh(labels, values, color=TEAL)
    ax.set_xlabel("Unique product URLs")
    ax.set_title("Independent fetch of receipt URLs")
    _footer(fig, "Independently observed. robots skips were not fetched. A blocked page can still be HTTP 200.")
    _save(fig, path)


def power_curve(path: Path) -> None:
    _font()
    import numpy as np
    ns = np.arange(8, 121)
    widths = [expected_half_width(int(n)) for n in ns]
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    ax.plot(ns, widths, color=NAVY, linewidth=1.6)
    marks = [
        (n_for_proportion(0.15), "Full primary ±0.15"),
        (n_for_proportion(0.20), "Full secondary ±0.20"),
        (n_for_proportion(0.25), "MVE primary ±0.25"),
        (n_for_proportion(0.35), "MVE secondary ±0.35"),
    ]
    for n, label in marks:
        ax.scatter([n], [expected_half_width(n)], color=RUST, zorder=3)
        ax.annotate(f"{label}\nn={n}", (n, expected_half_width(n)), textcoords="offset points", xytext=(6, 6), fontsize=8)
    ax.set_xlabel("Fresh bots (one prompt each)")
    ax.set_ylabel("Wald 95% half-width at p=0.5")
    ax.set_title("Runs needed for a run-level proportion")
    _footer(fig, "Inferred model. Worst-case variance. Not a design effect on top of the fresh-bot unit.")
    _save(fig, path)


def draw_all(out_dir: Path | None = None) -> None:
    out = out_dir or FIGURES
    analysis = json.loads((NORMALIZED / "analysis.json").read_text(encoding="utf-8"))
    architecture(out / "architecture.png")
    merchant_mix(analysis, out / "merchant-mix.png")
    top1(analysis, out / "top1-wilson.png")
    stability(analysis, out / "stability.png")
    hhi_fig(analysis, out / "hhi.png")
    price_rank(analysis, out / "price-rank.png")
    verification(analysis, out / "verification.png")
    power_curve(out / "power-curve.png")
