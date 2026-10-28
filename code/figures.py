"""Figures for the report. Reads data/stats.json and data/tables/.

The drawings use the counts in those files. They do not invent a third series.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch

INK = "#1c1917"
MUTED = "#57534e"
NAVY = "#1e3a4c"
RUST = "#b85c38"
TEAL = "#2f6f5e"
GOLD = "#a6843d"
SAND = "#e7e0d4"
PAPER = "#fffcf7"
LINE = "#d6d3d1"

COHORTS = [
    ("us-r1", "US first pass"),
    ("us-r2", "US fresh repeat"),
    ("tr-r1", "TR first pass"),
    ("tr-r2", "TR fresh repeat"),
    ("pref-tr", "TR preferences"),
]
TYPE_ORDER = ["retailer", "marketplace", "brand_own", "aggregator", "unknown"]
TYPE_COLOR = {
    "retailer": NAVY,
    "marketplace": RUST,
    "brand_own": TEAL,
    "aggregator": GOLD,
    "unknown": SAND,
}
QUERY_ORDER = ["generic", "brand", "model", "editorial"]
QUERY_COLOR = {"generic": SAND, "brand": TEAL, "model": NAVY, "editorial": RUST}


def _font() -> None:
    regular = Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf")
    bold = Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf")
    mono = Path("/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf")
    for path in (regular, bold, mono):
        if path.exists():
            font_manager.fontManager.addfont(str(path))
    plt.rcParams.update({
        "font.family": "Liberation Serif" if regular.exists() else "serif",
        "axes.edgecolor": INK,
        "axes.labelcolor": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "text.color": INK,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.titleweight": "regular",
        "axes.spines.top": False,
        "axes.spines.right": False,
    })


def _save(fig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _footer(ax, text: str) -> None:
    ax.annotate(
        text, xy=(0, 0), xycoords="figure fraction", xytext=(12, 8),
        textcoords="offset points", fontsize=8, color=MUTED, ha="left", va="bottom",
    )


def pipeline(stats: dict, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11.2, 6.4))
    ax.set_xlim(0, 112)
    ax.set_ylim(0, 70)
    ax.axis("off")
    fig.patch.set_facecolor("white")
    stages = [
        (4, 38, "1  Want", "The shopper's\nprompt"),
        (20, 38, "2  Query", "Rewritten into\nsearch text"),
        (36, 38, "3  Sources", "Where it\nlooks"),
        (52, 38, "4  Filter", "Price, stock,\nrating, material"),
        (68, 38, "5  Rank", "The order\non the page"),
        (84, 38, "6  Present", "A pick, a list,\na receipt"),
        (100, 38, "7  Hand back", "Stops before\npayment"),
    ]
    for i, (x, y, title, body) in enumerate(stages):
        box = FancyBboxPatch(
            (x, y), 13.2, 16, boxstyle="round,pad=0.3,rounding_size=0.6",
            facecolor=PAPER, edgecolor=NAVY, linewidth=1.1,
        )
        ax.add_patch(box)
        ax.text(x + 6.6, y + 12.2, title, ha="center", va="center", fontsize=10, color=NAVY)
        ax.text(x + 6.6, y + 6.2, body, ha="center", va="center", fontsize=8, color=INK)
        if i < len(stages) - 1:
            ax.annotate(
                "", xy=(stages[i + 1][0], y + 8), xytext=(x + 13.2, y + 8),
                arrowprops=dict(arrowstyle="-|>", color=NAVY, lw=1.0),
            )
    us1 = stats["cohorts"]["us-r1"]
    us2 = stats["cohorts"]["us-r2"]
    tr_runs = stats["cohorts"]["tr-r1"]["runs"] + stats["cohorts"]["tr-r2"]["runs"]
    tr_queries = {**stats["cohorts"]["tr-r1"]["query_class"]}
    for key, val in stats["cohorts"]["tr-r2"]["query_class"].items():
        tr_queries[key] = tr_queries.get(key, 0) + val
    named = tr_queries.get("brand", 0) + tr_queries.get("model", 0)
    total_q = sum(tr_queries.values())
    catalog = len(stats["catalog_runs"])
    notes = [
        (6, 22, NAVY, "US first pass", f"{us1['runs']} of {us1['runs']} runs opened on a store search.\n{us1['n_queries']} quoted queries, all generic category words.\n{us1['one_domain_runs']} of {us1['runs']} showed a single domain."),
        (42, 22, RUST, "US fresh repeat", f"{us2['runs']} of {us2['runs']} opened on an editorial web search\n(\"best\", Wirecutter, RTINGS). Mean {us2['mean_steps']} steps.\n0 of {us2['runs']} stayed on one domain."),
        (78, 22, TEAL, "Turkey, no preferences", f"{tr_runs} runs. {named} of {total_q} quoted queries name\na brand or a model. Lists come mostly\nfrom marketplaces, not one chain."),
    ]
    for x, y, color, title, body in notes:
        ax.plot([x, x + 28], [y + 9.2, y + 9.2], color=color, lw=2.2)
        ax.text(x, y + 6.6, title, fontsize=10, color=color, ha="left")
        ax.text(x, y + 1.2, body, fontsize=8, color=INK, ha="left", va="bottom")
    ax.text(6, 6.5, f"A third source shows up on 28 October: {catalog} shopping replies name a product-catalog search. None of the 22 October receipts do.", fontsize=9, color=INK)
    ax.text(6, 66, "What the receipts show, not a diagram of the model", fontsize=15, color=INK, ha="left")
    ax.text(6, 62, "Seven stages you can see from the outside. The source stage is not the same in every cohort.", fontsize=10, color=MUTED)
    _save(fig, path)


def domain_mix(stats: dict, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9.4, 5.4))
    labels, series = [], {k: [] for k in TYPE_ORDER}
    for key, label in COHORTS:
        block = stats["cohorts"][key]
        labels.append(f"{label}\n{block['products']} products")
        types = block["store_types"]
        for name in TYPE_ORDER:
            series[name].append(types.get(name, {}).get("share") or 0)
    import numpy as np
    y = np.arange(len(labels))
    left = np.zeros(len(labels))
    for name in TYPE_ORDER:
        vals = np.array(series[name])
        if vals.sum() == 0:
            continue
        ax.barh(y, vals, left=left, color=TYPE_COLOR[name], height=0.62, label=name.replace("_", " "))
        left += vals
    ax.set_yticks(y, labels)
    ax.set_xlim(0, 1)
    ax.set_xlabel("Share of shown products")
    ax.set_title("Where the shown products were hosted")
    ax.legend(frameon=False, ncol=4, loc="lower center", bbox_to_anchor=(0.5, -0.28))
    ax.invert_yaxis()
    _footer(ax, "Source: receipt products in data/records.csv. One product, one primary URL.")
    _save(fig, path)


def overlap_heatmap(stats: dict, path: Path) -> None:
    families = ["EL01", "EL02", "FA01", "GR01", "HO01", "GI01"]
    cols = [
        ("US", "link", "US link"),
        ("US", "product", "US product"),
        ("US", "brand", "US brand"),
        ("TR", "link", "TR link"),
        ("TR", "product", "TR product"),
        ("TR", "brand", "TR brand"),
    ]
    lookup = {(row["market"], row["family"]): row for row in stats["stability"]}
    import numpy as np
    grid = np.array([[lookup[(m, f)][k] for m, k, _ in cols] for f in families], dtype=float)
    fig, ax = plt.subplots(figsize=(8.6, 5.2))
    im = ax.imshow(grid, cmap="YlGnBu", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(cols)), ["US\nlink", "US\nproduct", "US\nbrand", "TR\nlink", "TR\nproduct", "TR\nbrand"])
    ax.set_yticks(range(len(families)), families)
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            val = grid[i, j]
            label = f"{val:.3f}".rstrip("0").rstrip(".")
            if "." not in label:
                label += ".00"
            elif len(label.split(".")[1]) == 1:
                label += "0"
            ax.text(j, i, label, ha="center", va="center", fontsize=8,
                    color="white" if val > 0.55 else INK)
    ax.set_title("Fresh-bot repeat overlap")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04).set_label("Jaccard")
    fig.text(0.01, 0.01, "Link = canonical URL. Product = model or name key. Brand = normalised brand. 0 is no overlap.", fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    _save(fig, path)


def perturbation_effects(stats: dict, path: Path) -> None:
    rows = [r for r in stats["perturbations"] if r["condition"] != "location-default"]
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 6.6), sharex=True)
    for ax, market, title in (
        (axes[0], "US", "United States"),
        (axes[1], "TR", "Turkey"),
    ):
        subset = [r for r in rows if r["intended_market"] == market]
        subset = list(reversed(subset))
        y = range(len(subset))
        labels = []
        for r in subset:
            mark = ""
            if r["carryover"] == "full":
                mark = " *"
            elif r["carryover"] == "partial":
                mark = " †"
            elif r["day"] == "2026-10-28":
                mark = " ‡"
            labels.append(f"{r['family']} {r['variable']}{mark}")
        ax.hlines(list(y), 0, 1, color=LINE, lw=0.6, zorder=0)
        ax.scatter([r["link"] for r in subset], list(y), color=NAVY, s=36, zorder=2, label="Link overlap with first pass")
        ax.scatter([r["brand"] for r in subset], list(y), color=TEAL, s=36, marker="D", zorder=2, label="Brand overlap with first pass")
        link_mean = stats["repeat_link_mean"][market]
        brand_mean = stats["repeat_brand_mean"][market]
        ax.axvline(link_mean, color=NAVY, ls=":", lw=1, label=f"Repeat link mean {link_mean:.2f}")
        ax.axvline(brand_mean, color=TEAL, ls="--", lw=1, label=f"Repeat brand mean {brand_mean:.2f}")
        ax.set_yticks(list(y), labels)
        ax.set_xlim(-0.02, 1.02)
        ax.set_title(title)
        ax.set_xlabel("Jaccard with the first-pass run")
    axes[0].legend(frameon=False, fontsize=8, loc="lower right")
    fig.suptitle("Perturbation overlap against the repeat baseline", fontsize=14, x=0.02, ha="left")
    fig.text(0.01, 0.01, "* no new search   † receipt cites an earlier search   ‡ 28 October   Dotted and dashed lines are fresh-repeat means, not a test.", fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    _save(fig, path)


def price_spread(stats: dict, path: Path) -> None:
    import numpy as np
    fig, ax = plt.subplots(figsize=(8.8, 5.0))
    for i, (key, label) in enumerate(COHORTS):
        ratios = stats["cohorts"][key]["price_ratios"]
        jitter = np.linspace(-0.12, 0.12, len(ratios)) if len(ratios) > 1 else [0]
        ax.scatter(np.full(len(ratios), i) + jitter, ratios, color=NAVY, s=32, zorder=2)
        med = stats["cohorts"][key]["median_price_ratio"]
        if med is not None:
            ax.hlines(med, i - 0.28, i + 0.28, color=RUST, lw=2, zorder=3)
    ax.set_xticks(range(len(COHORTS)), [c[1] for c in COHORTS], rotation=15, ha="right")
    ax.set_ylabel("Highest price ÷ lowest price in the reply")
    ax.set_title("Price spread inside one reply")
    ax.annotate("bar = median", xy=(0.98, 0.95), xycoords="axes fraction", ha="right", color=RUST, fontsize=9)
    _footer(ax, "Same currency inside a reply. Not a comparison of US dollars with lira.")
    _save(fig, path)


def query_style(stats: dict, path: Path) -> None:
    import numpy as np
    fig, ax = plt.subplots(figsize=(8.8, 5.0))
    labels = [c[1] for c in COHORTS]
    x = np.arange(len(COHORTS))
    bottom = np.zeros(len(COHORTS))
    for name in QUERY_ORDER:
        vals = []
        for key, _ in COHORTS:
            block = stats["cohorts"][key]
            n = sum(block["first_query"].values()) or 1
            vals.append(block["first_query"].get(name, 0) / n)
        vals = np.array(vals)
        if vals.sum() == 0:
            continue
        ax.bar(x, vals, bottom=bottom, color=QUERY_COLOR[name], width=0.66, label=name)
        bottom += vals
    ax.set_xticks(x, labels, rotation=15, ha="right")
    ax.set_ylim(0, 1)
    ax.set_ylabel("Share of runs")
    ax.set_title("What the first quoted search was")
    ax.legend(frameon=False, ncol=4, loc="lower center", bbox_to_anchor=(0.5, -0.32))
    _footer(ax, "Editorial = best / review / Wirecutter / RTINGS. Model = a model code. Brand = a brand name and no model code.")
    _save(fig, path)


def draw_all(root: Path | None = None) -> None:
    root = root or Path(__file__).resolve().parents[1]
    _font()
    stats = json.loads((root / "data" / "stats.json").read_text(encoding="utf-8"))
    out = root / "figures"
    pipeline(stats, out / "pipeline.png")
    domain_mix(stats, out / "domain-mix.png")
    overlap_heatmap(stats, out / "overlap-heatmap.png")
    perturbation_effects(stats, out / "perturbation-effects.png")
    price_spread(stats, out / "price-spread.png")
    query_style(stats, out / "query-style.png")


if __name__ == "__main__":
    draw_all()
