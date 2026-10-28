"""Counts for the Grok Bot shopping study.

Every share is descriptive. Nothing here is a significance test.
Repeats that returned an earlier answer without a new search are not treated
as a second sample.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from receipts import RECORD_FIELDS, Run, load_runs, norm_brand, record_dict, run_dict

# Fresh-bot repeat of the same prompt. GI01-TR r2 is the same chat, so the
# fresh repeat is r3.
PAIRS = [
    ("np-us__EL01-US__r1", "np-us__EL01-US__r2", "US", "EL01"),
    ("np-us__EL02-US__r1", "np-us__EL02-US__r2", "US", "EL02"),
    ("np-us__FA01-US__r1", "np-us__FA01-US__r2", "US", "FA01"),
    ("np-us__GR01-US__r1", "np-us__GR01-US__r2", "US", "GR01"),
    ("np-us__HO01-US__r1", "np-us__HO01-US__r2", "US", "HO01"),
    ("np-us__GI01-US__r1", "np-us__GI01-US__r2", "US", "GI01"),
    ("np-tr__EL01-TR__r1", "np-tr__EL01-TR__r2", "TR", "EL01"),
    ("np-tr__EL02-TR__r1", "np-tr__EL02-TR__r2", "TR", "EL02"),
    ("np-tr__FA01-TR__r1", "np-tr__FA01-TR__r2", "TR", "FA01"),
    ("np-tr__GR01-TR__r1", "np-tr__GR01-TR__r2", "TR", "GR01"),
    ("np-tr__HO01-TR__r1", "np-tr__HO01-TR__r2", "TR", "HO01"),
    ("np-tr__GI01-TR__r1", "np-tr__GI01-TR__r3", "TR", "GI01"),
]

_EXCLUSION = [
    ("left_out", r"left (?:them |it )?out|I left out"),
    ("dropped", r"\bdropped\b"),
    ("over_budget", r"over[- ]budget|above the budget|too expensive|couldn't find any|could not find any|none under|nothing under|nothing fits"),
    ("no_price", r"no price|didn't show a price|did not show a price|without a price|price wasn't|no offer"),
    ("low_rating", r"under 3 stars|rated under 3|below 3 stars"),
    ("not_recommended", r"not recommended"),
    ("stock", r"sold out|out of stock|tükendi"),
    ("skipped", r"\bskipped\b"),
]
_CAVEAT = [
    ("seller", r"sold by|marketplace seller|fulfilled by"),
    ("warranty", r"warrant|garanti"),
    ("condition", r"opened before|misleading|third[- ]party"),
]

_BRAND_WORD = re.compile(
    r"(?i)\b(sony|anker|soundcore|jbl|bose|apple|sennheiser|beats|jlab|philips|"
    r"tefal|t-fal|karaca|lava|quince|yeti|leatherman|thermopro|xiaomi|edifier|"
    r"samsung|ugreen|baseus|koton|ipekyol|beymen|mavi|lavazza|starbucks|illy|"
    r"lodge|greenpan|figmint|casio|huawei|arzum|kronotrop|petra)\b"
)
_MODEL_Q = re.compile(
    r"(?i)\b(wh-?ch?-?\d{3,}|wf-?\d{3,}|wh-?\d{3,}|airpods|q\d{2}i?|a\d{4})\b"
)


def day_of(received: str) -> str:
    m = re.search(r"20\d\d-\d\d-\d\d", received or "")
    return m.group(0) if m else ""


def cohort_of(run: Run) -> str:
    if run.role != "shopping":
        return run.role
    if run.condition == "location-default":
        return "location-default"
    if run.condition == "pref-tr":
        return "pref-tr"
    if run.perturbation:
        return "round3-oct28" if day_of(run.received) == "2026-10-28" else "round3-oct22"
    if run.bot == "bot-us-1" and run.carryover != "full":
        return "us-r1"
    if run.bot == "bot-us-2":
        return "us-r2"
    if run.bot == "bot-tr-1" and run.carryover != "full":
        return "tr-r1"
    if run.bot == "bot-tr-2":
        return "tr-r2"
    if run.carryover == "full":
        return "cached"
    return "other"


def jaccard(a, b) -> float | None:
    left = {x for x in a if x}
    right = {x for x in b if x}
    if not left and not right:
        return None
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def hhi(brands: list[str]) -> float | None:
    vals = [b for b in brands if b]
    if not vals:
        return None
    counts = Counter(vals)
    n = sum(counts.values())
    return sum((v / n) ** 2 for v in counts.values())


def mean(xs: list[float | None]) -> float | None:
    vals = [x for x in xs if x is not None]
    return sum(vals) / len(vals) if vals else None


def r3(x: float | None) -> float | None:
    return None if x is None else round(x, 3)


def query_class(query: str) -> str:
    if re.search(r"(?i)\b(best|review|reviews|wirecutter|rtings|soundguys|serious eats|well reviewed|en iyi)\b", query or ""):
        return "editorial"
    if _MODEL_Q.search(query or ""):
        return "model"
    if _BRAND_WORD.search(query or ""):
        return "brand"
    return "generic"


def _keys(run: Run, kind: str) -> list[str]:
    if kind == "link":
        return [p.link_key for p in run.products]
    if kind == "product":
        return [p.product_key for p in run.products]
    return [norm for p in run.products if (norm := norm_brand(p.brand))]


def budget_row(run: Run) -> dict | None:
    if run.budget is None or run.role != "shopping":
        return None
    priced = [p for p in run.products if p.price is not None and p.currency == run.budget_currency]
    other = [p for p in run.products if p.price is not None and p.currency != run.budget_currency]
    over = [p for p in priced if p.price >= run.budget]
    crosses = [p for p in priced if p.price < run.budget and p.price_high is not None and p.price_high >= run.budget]
    prose = bool(re.search(r"(?i)couldn'?t find any|could not find any|none under|nothing under|no .{0,40}under", run.bot_text))
    return {
        "run_id": run.run_id,
        "prompt_id": run.prompt_id,
        "perturbation": run.perturbation,
        "budget": run.budget,
        "currency": run.budget_currency,
        "shown": len(run.products),
        "priced": len(priced),
        "over": len(over),
        "under": len(priced) - len(over),
        "range_crosses": len(crosses),
        "unpriced": len(run.products) - len(priced) - len(other),
        "prose_says_none": prose,
        "over_names": [p.product for p in over],
    }


def store_ok(run: Run) -> dict | None:
    if not run.store_required:
        return None
    doms = [p.domain for p in run.products if p.domain]
    hit = [d for d in doms if d == run.store_required]
    return {
        "run_id": run.run_id,
        "required": run.store_required,
        "shown": len(run.products),
        "on_store": len(hit),
        "domains": sorted(set(doms)),
        "all_on_store": bool(doms) and len(hit) == len(doms),
    }


def brand_ok(run: Run) -> dict | None:
    if not run.brand_required:
        return None
    brands = [norm_brand(p.brand) for p in run.products]
    hit = [b for b in brands if b.lower() == run.brand_required]
    return {
        "run_id": run.run_id,
        "required": run.brand_required,
        "shown": len(run.products),
        "on_brand": len(hit),
        "brands": brands,
        "all_on_brand": bool(brands) and len(hit) == len(brands),
    }


def flags(text: str, patterns: list[tuple[str, str]]) -> list[str]:
    return [name for name, pat in patterns if re.search(pat, text or "", re.I)]


def cohort_block(runs: list[Run]) -> dict:
    products = [p for r in runs for p in r.products]
    brands = [norm_brand(p.brand) for p in products]
    brands = [b for b in brands if b]
    types = Counter(p.store_type for p in products)
    domains = Counter(p.domain for p in products if p.domain)
    n = len(products) or 1
    first = Counter()
    any_class = Counter()
    retrieval = Counter(r.retrieval for r in runs)
    one_domain = 0
    ratios = []
    for r in runs:
        doms = {p.domain for p in r.products if p.domain}
        if len(doms) == 1:
            one_domain += 1
        if r.searches:
            first[query_class(r.searches[0])] += 1
            for q in r.searches:
                any_class[query_class(q)] += 1
        prices = [p.price for p in r.products if p.price and p.price > 0]
        if len(prices) >= 2 and len({p.currency for p in r.products if p.price}) == 1:
            ratios.append(max(prices) / min(prices))
    counts = Counter(brands)
    top = counts.most_common(3)
    top_share = sum(v for _, v in top) / len(brands) if brands else None
    return {
        "runs": len(runs),
        "products": len(products),
        "mean_products": r3(len(products) / len(runs)) if runs else None,
        "mean_steps": r3(mean([r.n_steps for r in runs])),
        "mean_searches": r3(mean([r.n_searches for r in runs])),
        "median_searches": _median([r.n_searches for r in runs]),
        "one_domain_runs": one_domain,
        "brands": len(set(brands)),
        "hhi": r3(hhi(brands)),
        "top1_share": r3(top[0][1] / len(brands)) if brands else None,
        "top1_brand": top[0][0] if top else "",
        "top3_share": r3(top_share),
        "store_types": {k: {"n": v, "share": r3(v / n)} for k, v in types.most_common()},
        "domains": [{"domain": d, "n": c} for d, c in domains.most_common(8)],
        "retrieval": dict(retrieval),
        "first_query": dict(first),
        "query_class": dict(any_class),
        "n_queries": sum(any_class.values()),
        "median_price_ratio": r3(_median(ratios)),
        "mean_price_ratio": r3(mean(ratios)),
        "price_ratios": [round(x, 2) for x in ratios],
    }


def _median(xs: list[float]) -> float | None:
    vals = sorted(x for x in xs if x is not None)
    if not vals:
        return None
    mid = len(vals) // 2
    if len(vals) % 2:
        return float(vals[mid])
    return (vals[mid - 1] + vals[mid]) / 2


def stability(by_id: dict[str, Run]) -> list[dict]:
    rows = []
    for a, b, market, family in PAIRS:
        left, right = by_id[a], by_id[b]
        row = {
            "market": market,
            "family": family,
            "run_a": a,
            "run_b": b,
            "carry_a": left.carryover,
            "carry_b": right.carryover,
            "link": r3(jaccard(_keys(left, "link"), _keys(right, "link"))),
            "product": r3(jaccard(_keys(left, "product"), _keys(right, "product"))),
            "brand": r3(jaccard(_keys(left, "brand"), _keys(right, "brand"))),
            "top1_link": int(bool(left.products and right.products and left.products[0].link_key and left.products[0].link_key == right.products[0].link_key)),
            "top1_brand": int(bool(left.products and right.products and _keys(left, "brand")[:1] == _keys(right, "brand")[:1] and _keys(left, "brand")[:1])),
        }
        rows.append(row)
    return rows


def perturbations(by_id: dict[str, Run], runs: list[Run], noise: dict[str, float | None]) -> list[dict]:
    rows = []
    for run in runs:
        if run.role != "shopping" or not run.perturbation_id:
            continue
        base_id = f"{'np-us' if run.intended_market == 'US' else 'np-tr'}__{run.prompt_id}__r1"
        base = by_id.get(base_id)
        link = jaccard(_keys(run, "link"), _keys(base, "link")) if base else None
        brand = jaccard(_keys(run, "brand"), _keys(base, "brand")) if base else None
        product = jaccard(_keys(run, "product"), _keys(base, "product")) if base else None
        market_noise = noise.get(run.intended_market)
        rows.append({
            "run_id": run.run_id,
            "perturbation_id": run.perturbation_id,
            "variable": run.perturbation,
            "family": run.family,
            "intended_market": run.intended_market,
            "market": run.market,
            "condition": run.condition,
            "day": day_of(run.received),
            "retrieval": run.retrieval,
            "carryover": run.carryover,
            "baseline": base_id,
            "link": r3(link),
            "product": r3(product),
            "brand": r3(brand),
            "repeat_link_mean": market_noise,
            "link_below_repeat_mean": None if link is None or market_noise is None else int(link < market_noise - 1e-9),
            "n_products": len(run.products),
            "budget": budget_row(run),
            "store": store_ok(run),
            "brand_rule": brand_ok(run),
        })
    return rows


def preference(by_id: dict[str, Run]) -> list[dict]:
    rows = []
    for family in ["EL01", "EL02", "FA01", "GR01", "HO01", "GI01"]:
        a = by_id[f"np-tr__{family}-TR__r1"]
        b = by_id[f"pref-tr__{family}-TR__r1"]
        rows.append({
            "family": family,
            "link": r3(jaccard(_keys(a, "link"), _keys(b, "link"))),
            "product": r3(jaccard(_keys(a, "product"), _keys(b, "product"))),
            "brand": r3(jaccard(_keys(a, "brand"), _keys(b, "brand"))),
        })
    return rows


def transparency(runs: list[Run]) -> dict:
    shopping = [r for r in runs if r.role == "shopping"]
    exclusion_hits = defaultdict(list)
    caveat_hits = defaultdict(list)
    any_ex = []
    any_cav = []
    for r in shopping:
        ex = flags(r.bot_text, _EXCLUSION)
        cav = flags(r.bot_text, _CAVEAT)
        for name in ex:
            exclusion_hits[name].append(r.run_id)
        for name in cav:
            caveat_hits[name].append(r.run_id)
        if ex:
            any_ex.append(r.run_id)
        if cav:
            any_cav.append(r.run_id)
    return {
        "shopping_runs": len(shopping),
        "runs_disclosing_an_exclusion": len(any_ex),
        "runs_with_a_seller_or_condition_caveat": len(any_cav),
        "exclusion": {k: {"n": len(v), "runs": v} for k, v in exclusion_hits.items()},
        "caveat": {k: {"n": len(v), "runs": v} for k, v in caveat_hits.items()},
    }


def checkout_summary(runs: list[Run]) -> list[dict]:
    rows = []
    for run in runs:
        if run.role != "checkout":
            continue
        text = run.bot_text
        rows.append({
            "run_id": run.run_id,
            "market": "US" if "US" in run.run_id else "TR",
            "bot": run.bot,
            "day": day_of(run.received) or "2026-10-28",
            "same_chat_as": run.same_chat_as,
            "shown_product": run.products[0].product if run.products else "",
            "price": run.products[0].price if run.products else None,
            "currency": run.products[0].currency if run.products else "",
            "domain": run.products[0].domain if run.products else "",
            "url": run.products[0].url if run.products else "",
            "says_unavailable_95829": "95829" in text,
            "says_sacramento": "Sacramento" in text,
            "says_greyed_out": "greyed out" in text.lower(),
            "says_bladed_or_restricted": "bladed" in text.lower() or "may be restricted" in text.lower(),
            "says_nothing_charged": bool(re.search(r"nothing was (?:bought or )?charged|Nothing was bought or paid", text)),
            "says_no_checkout_started": "never started a checkout" in text.lower() or "Checkout was not started" in text,
            "says_guest_cart": "guest cart" in text.lower(),
            "says_didnt_sign_in": "didn't sign in" in text.lower() or "did not sign in" in text.lower(),
            "says_sponsored_ad": "sponsored ad" in text.lower(),
            "says_surge": "Leatherman Surge" in text,
            "says_cart_empty": "Cart (0 items)" in text and "$0.00" in text,
            "offered_brand_site": "leatherman.com" in text.lower(),
            "names_item": "Tefal UnlimitedOne" in text or "Leatherman Rev" in text,
        })
    return rows


def build_stats(runs: list[Run]) -> dict:
    by_id = {r.run_id: r for r in runs}
    shopping = [r for r in runs if r.role == "shopping"]
    groups: dict[str, list[Run]] = defaultdict(list)
    for r in shopping:
        groups[cohort_of(r)].append(r)
    cohorts = {name: cohort_block(rows) for name, rows in sorted(groups.items())}
    stab = stability(by_id)
    noise = {
        "US": r3(mean([row["link"] for row in stab if row["market"] == "US"])),
        "TR": r3(mean([row["link"] for row in stab if row["market"] == "TR"])),
    }
    brand_noise = {
        "US": r3(mean([row["brand"] for row in stab if row["market"] == "US"])),
        "TR": r3(mean([row["brand"] for row in stab if row["market"] == "TR"])),
    }
    pilot_ids = [
        "np-us__EL01-US__r1", "np-us__EL02-US__r1", "np-us__FA01-US__r1",
        "np-us__GR01-US__r1", "np-us__HO01-US__r1",
    ]
    return {
        "files": len(runs),
        "shopping_runs": len(shopping),
        "product_rows": sum(len(r.products) for r in runs),
        "shopping_product_rows": sum(len(r.products) for r in shopping),
        "roles": dict(Counter(r.role for r in runs)),
        "cohorts": cohorts,
        "pilot_five": cohort_block([by_id[i] for i in pilot_ids]),
        "stability": stab,
        "repeat_link_mean": noise,
        "repeat_brand_mean": brand_noise,
        "perturbations": perturbations(by_id, runs, noise),
        "preference_tr": preference(by_id),
        "preference_link_mean": r3(mean([row["link"] for row in preference(by_id)])),
        "preference_brand_mean": r3(mean([row["brand"] for row in preference(by_id)])),
        "budgets": [row for r in shopping if (row := budget_row(r))],
        "transparency": transparency(runs),
        "checkout": checkout_summary(runs),
        "catalog_runs": [
            {"run_id": r.run_id, "day": day_of(r.received), "market": r.market, "condition": r.condition}
            for r in shopping if r.retrieval == "catalog"
        ],
        "cached_runs": [r.run_id for r in shopping if r.carryover == "full"],
        "could_not_compute": [
            "Overlap with a Google Shopping or Amazon top-N baseline was not computed: no baseline capture was saved.",
            "The US saved-preferences series was not run. The Turkey saved-preferences bot was run.",
            "No significance test is reported. The samples are small and several runs share a chat.",
            "The TR checkout reply is only the final cancellation. The intermediate cart screens were not in the saved text.",
            "Whether the 28 October catalog path is a lasting backend change is not something these receipts can settle.",
        ],
    }


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = fields or list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            flat = {}
            for key in fields:
                val = row.get(key, "")
                if isinstance(val, (dict, list)):
                    val = json.dumps(val, ensure_ascii=False)
                flat[key] = val
            writer.writerow(flat)


def write_outputs(runs: list[Run], data: Path) -> dict:
    stats = build_stats(runs)
    data.mkdir(parents=True, exist_ok=True)
    records = [record_dict(r, p) for r in runs for p in r.products]
    write_csv(data / "records.csv", records, RECORD_FIELDS)
    with (data / "records.jsonl").open("w", encoding="utf-8") as fh:
        for row in records:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    run_rows = [run_dict(r) for r in runs]
    # Stable column order for the run index.
    run_fields = [
        "run_id", "round", "role", "condition", "bot", "prompt_id", "perturbation",
        "perturbation_id", "category", "family", "intended_market", "market",
        "n_products", "n_steps", "n_searches", "retrieval", "carryover", "budget",
        "budget_currency", "sent", "received", "has_receipt", "same_chat_as",
        "domains", "searches", "source_file", "warnings",
    ]
    write_csv(data / "runs.csv", run_rows, run_fields)
    with (data / "runs.jsonl").open("w", encoding="utf-8") as fh:
        for row in run_rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    tables = data / "tables"
    write_csv(tables / "stability.csv", stats["stability"])
    write_csv(tables / "perturbations.csv", stats["perturbations"])
    write_csv(tables / "preference_tr.csv", stats["preference_tr"])
    write_csv(tables / "budgets.csv", stats["budgets"])
    write_csv(tables / "checkout.csv", stats["checkout"])
    cohort_rows = []
    for name, block in stats["cohorts"].items():
        cohort_rows.append({
            "cohort": name,
            "runs": block["runs"],
            "products": block["products"],
            "mean_products": block["mean_products"],
            "mean_steps": block["mean_steps"],
            "mean_searches": block["mean_searches"],
            "one_domain_runs": block["one_domain_runs"],
            "hhi": block["hhi"],
            "top1_brand": block["top1_brand"],
            "top1_share": block["top1_share"],
            "median_price_ratio": block["median_price_ratio"],
            "retrieval": json.dumps(block["retrieval"]),
            "first_query": json.dumps(block["first_query"]),
            "store_types": json.dumps(block["store_types"]),
        })
    write_csv(tables / "cohorts.csv", cohort_rows)
    (data / "stats.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return stats


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    runs = load_runs(root / "evidence" / "transcripts")
    stats = write_outputs(runs, root / "data")
    print(f"files={stats['files']} shopping={stats['shopping_runs']} products={stats['shopping_product_rows']}")
    print("repeat link", stats["repeat_link_mean"], "brand", stats["repeat_brand_mean"])


if __name__ == "__main__":
    main()
