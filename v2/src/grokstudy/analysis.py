"""Retrospective analysis of the October corpus plus URL verification.

Population language is not used for contrasts that rest on one bot per arm.
Within-list permutation tests are about the lists that were saved. They do
not recover the unobserved candidate set: a product that was never shown
cannot be given a rank.
"""
from __future__ import annotations

import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit

import numpy as np

from .normalize import corpus_tables
from .paths import NORMALIZED, V1_CODE, VERIFICATION_INDEX
from .statsutil import (
    benjamini_hochberg,
    cluster_bootstrap,
    hhi,
    holm,
    jaccard,
    kendall_tau_a,
    permutation_pvalue,
    rbo,
    wilson_interval,
    within_list_permutation,
)
from .verify import load_index

if str(V1_CODE) not in sys.path:
    sys.path.insert(0, str(V1_CODE))

from analyze import PAIRS  # noqa: E402

MERCHANT_ORDER = [
    "retailer", "marketplace", "brand_site", "price_comparison", "editorial", "unknown",
]
COHORT_ORDER = [
    "us-r1", "us-r2", "tr-r1", "tr-r2", "pref-tr",
    "round3-oct22", "round3-oct28", "location-default",
]


def _read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _num(value: str) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _round(obj):
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return round(obj, 6)
    if isinstance(obj, dict):
        return {k: _round(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round(v) for v in obj]
    if isinstance(obj, (np.floating,)):
        return _round(float(obj))
    if isinstance(obj, (np.integer,)):
        return int(obj)
    return obj


def _group(rows: list[dict], key: str) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row[key]].append(row)
    return grouped


def _shopping_runs(runs: list[dict]) -> list[dict]:
    # The same-chat cache is a shopping file with no second receipt. It stays
    # in the reply count and in the cached cohort. It is not dropped here.
    return [row for row in runs if row["role"] == "shopping"]


def _by_rank(products: list[dict]) -> list[dict]:
    return sorted(products, key=lambda row: int(row["rank"]))


def _top(products: list[dict]) -> dict | None:
    ordered = _by_rank(products)
    return ordered[0] if ordered else None


def _share_rows(products: list[dict], field: str) -> dict:
    n = len(products)
    counts: dict[str, int] = defaultdict(int)
    for row in products:
        counts[row[field] or "unknown"] += 1
    return {
        key: {"n": counts.get(key, 0), "share": (counts.get(key, 0) / n) if n else None}
        for key in list(MERCHANT_ORDER) + sorted(k for k in counts if k not in MERCHANT_ORDER)
        if counts.get(key, 0) or key in MERCHANT_ORDER
    }


def _mean_run_share(run_lists: list[list[dict]], merchant: str) -> float | None:
    shares = []
    for products in run_lists:
        if not products:
            continue
        shares.append(sum(1 for row in products if row["merchant_class"] == merchant) / len(products))
    if not shares:
        return None
    return sum(shares) / len(shares)


def _domain_labels(products: list[dict]) -> list[str]:
    return [row["domain"] for row in products if row["domain"]]


def _norm_url(url: str) -> str:
    parts = urlsplit(url or "")
    host = (parts.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return host + (parts.path or "").rstrip("/")


def fetch_outcome(record: dict) -> str:
    status = record.get("fetch_status")
    if status == "skipped_robots":
        robots = record.get("robots_status") or ""
        if robots == "robots_forbidden":
            return "robots_forbidden"
        return "robots_skipped"
    if status == "error" or not record.get("http_status"):
        return "error"
    final = record.get("final_url") or ""
    kind = record.get("page_kind") or ""
    code = int(record.get("http_status") or 0)
    if kind == "challenge" or "/blocked" in final or "captcha" in (record.get("title") or "").lower():
        return "blocked"
    if code in {404, 410, 400}:
        return "dead"
    if code in {401, 403, 429, 451}:
        return "blocked"
    if code == 200:
        return "live"
    if 200 < code < 400:
        return "live"
    return "other"


def _redirect_class(record: dict) -> str:
    if record.get("fetch_status") != "fetched":
        return "not_fetched"
    original = _norm_url(record.get("url") or "")
    final = _norm_url(record.get("final_url") or "")
    if not final or final == original:
        return "same_url"
    orig_host = original.split("/", 1)[0]
    final_host = final.split("/", 1)[0]
    if orig_host != final_host:
        return "cross_domain"
    return "same_domain"


def _price_agreement(receipt_price: str, receipt_ccy: str, page_price, page_ccy: str) -> str:
    if page_price is None:
        return "page_price_unparsed"
    if receipt_price == "":
        return "receipt_price_missing"
    ccy_map = {"TL": "TRY", "USD": "USD", "TRY": "TRY", "EUR": "EUR", "GBP": "GBP"}
    left = ccy_map.get((receipt_ccy or "").upper(), (receipt_ccy or "").upper())
    right = ccy_map.get((page_ccy or "").upper(), (page_ccy or "").upper())
    if not right:
        return "page_currency_missing"
    if left and right and left != right:
        return "currency_differs"
    receipt = float(receipt_price)
    page = float(page_price)
    gap = abs(page - receipt)
    rel = gap / receipt if receipt else gap
    if rel <= 0.05 or gap <= 0.02:
        return "match"
    return "mismatch"


def _verification_block(products: list[dict]) -> dict:
    index = load_index(VERIFICATION_INDEX)
    by_url = {}
    for row in index:
        by_url[row["url"]] = row
    shopping = [row for row in products if row["role"] == "shopping"]
    urls = [row["url"] for row in shopping if row["url"]]
    unique = list(dict.fromkeys(urls))
    outcomes = defaultdict(int)
    redirects = defaultdict(int)
    robots = defaultdict(int)
    price_rows = defaultdict(int)
    sponsored_pages = 0
    live_price_parsed = 0
    missing = 0
    joined = []
    for url in unique:
        record = by_url.get(url)
        if record is None:
            missing += 1
            outcomes["not_in_index"] += 1
            continue
        outcomes[fetch_outcome(record)] += 1
        redirects[_redirect_class(record)] += 1
        robots[record.get("robots_status") or ""] += 1
        if record.get("sponsored_label") is True:
            sponsored_pages += 1
        if record.get("price") is not None and fetch_outcome(record) == "live":
            live_price_parsed += 1
    for row in shopping:
        if not row["url"]:
            continue
        record = by_url.get(row["url"])
        if record is None:
            continue
        agreement = _price_agreement(
            row["price"], row["currency"], record.get("price"), record.get("currency") or ""
        )
        price_rows[agreement] += 1
        if agreement in {"match", "mismatch"}:
            joined.append({
                "record_id": row["record_id"],
                "agreement": agreement,
                "receipt_price": row["price"],
                "page_price": record.get("price"),
                "currency": row["currency"],
                "domain": row["domain"],
            })
    return {
        "evidence_class": "independently_observed",
        "shopping_product_rows": len(shopping),
        "rows_without_url": sum(1 for row in shopping if not row["url"]),
        "unique_urls": len(unique),
        "indexed_urls": len(unique) - missing,
        "missing_from_index": missing,
        "outcomes_unique_urls": dict(outcomes),
        "redirects_unique_urls": dict(redirects),
        "robots_status_unique_urls": dict(robots),
        "price_agreement_product_rows": dict(price_rows),
        "sponsored_word_observed_on_pages": sponsored_pages,
        "live_pages_with_parsed_price": live_price_parsed,
        "price_note": (
            "A mismatch means the fetched page price and the receipt price differ "
            "by more than 5 percent. The fetch is later than the chat. It is not "
            "a finding that the receipt was wrong on the day it was saved."
        ),
        "sponsored_note": (
            "sponsored_label is true only when the visible page text contained "
            "the word. Pages that do not say it are left unknown, not coded as unsponsored."
        ),
        "example_mismatches": [row["record_id"] for row in joined if row["agreement"] == "mismatch"][:12],
        "example_matches": [row["record_id"] for row in joined if row["agreement"] == "match"][:12],
    }


def _stability(products_by_run: dict[str, list[dict]]) -> dict:
    markets = defaultdict(list)
    for left_id, right_id, market, family in PAIRS:
        left = _by_rank(products_by_run.get(left_id, []))
        right = _by_rank(products_by_run.get(right_id, []))
        left_links = [row["link_key"] for row in left if row["link_key"]]
        right_links = [row["link_key"] for row in right if row["link_key"]]
        left_brands = [row["brand_canonical"] for row in left if row["brand_canonical"]]
        right_brands = [row["brand_canonical"] for row in right if row["brand_canonical"]]
        left_models = [row["product_id"] for row in left if row["identity_strength"] == "model"]
        right_models = [row["product_id"] for row in right if row["identity_strength"] == "model"]
        rank_left = {key: i for i, key in enumerate(left_links)}
        rank_right = {key: i for i, key in enumerate(right_links)}
        tau = kendall_tau_a(rank_left, rank_right)
        row = {
            "pair_id": f"{market}:{family}",
            "market": market,
            "family": family,
            "run_a": left_id,
            "run_b": right_id,
            "link_jaccard": jaccard(left_links, right_links),
            "brand_jaccard": jaccard(left_brands, right_brands),
            "model_jaccard": jaccard(left_models, right_models),
            "rbo_p90": rbo(left_links, right_links, 0.9),
            "kendall_tau_a": tau["tau_a"],
            "kendall_defined": tau["defined"],
            "kendall_n_shared": tau["n_shared"],
            "top1_link_agree": bool(left_links and right_links and left_links[0] == right_links[0]),
            "top1_brand_agree": bool(left_brands and right_brands and left_brands[0] == right_brands[0]),
        }
        markets[market].append(row)

    def _mean(rows, field):
        vals = [row[field] for row in rows if row[field] is not None]
        return sum(vals) / len(vals) if vals else None

    summary = {}
    for market, rows in markets.items():
        link_ci = cluster_bootstrap(
            rows, lambda sample: _mean(sample, "link_jaccard"), n_boot=2000, seed=20261028
        )
        brand_ci = cluster_bootstrap(
            rows, lambda sample: _mean(sample, "brand_jaccard"), n_boot=2000, seed=20261029
        )
        rbo_ci = cluster_bootstrap(
            rows, lambda sample: _mean(sample, "rbo_p90"), n_boot=2000, seed=20261030
        )
        summary[market] = {
            "n_pairs": len(rows),
            "n_bots": 2,
            "link_jaccard_mean": _mean(rows, "link_jaccard"),
            "link_jaccard_bootstrap": link_ci,
            "brand_jaccard_mean": _mean(rows, "brand_jaccard"),
            "brand_jaccard_bootstrap": brand_ci,
            "rbo_mean": _mean(rows, "rbo_p90"),
            "rbo_bootstrap": rbo_ci,
            "top1_link_agree": sum(1 for row in rows if row["top1_link_agree"]),
            "top1_brand_agree": sum(1 for row in rows if row["top1_brand_agree"]),
            "kendall_defined_pairs": sum(1 for row in rows if row["kendall_defined"]),
            "pairs": rows,
            "interval_assumption": (
                "The bootstrap resamples the six prompt-pairs. Both passes in a "
                "market are one bot each, and the first pass is one chat. The "
                "interval is not a multi-bot confidence interval."
            ),
        }
    return summary


def _price_lists(run_lists: list[list[dict]], extreme: str) -> list[list[bool]]:
    flags = []
    for products in run_lists:
        ordered_all = _by_rank(products)
        if not ordered_all or not ordered_all[0]["price"]:
            continue
        priced = [
            row for row in ordered_all
            if row["price"] and row["currency"] == ordered_all[0]["currency"]
        ]
        if len(priced) < 2:
            continue
        prices = [float(row["price"]) for row in priced]
        target = min(prices) if extreme == "min" else max(prices)
        if prices.count(target) != 1:
            continue
        flags.append([float(row["price"]) == target for row in priced])
    return flags


def _conditional_logit(run_lists: list[tuple[str, list[dict]]]) -> dict:
    """Conditional logit of which shown priced row is rank 1.

    The choice set is the priced rows of the reply, not the unobserved catalog.
    Reference merchant class is retailer. Cluster bootstrap resamples bots.
    """
    names = ["log_price_vs_median", "marketplace", "brand_site", "price_comparison"]
    prepared = []
    for bot, products in run_lists:
        ordered = _by_rank(products)
        if not ordered or not ordered[0]["price"]:
            continue
        priced = [row for row in ordered if row["price"] and row["currency"] == ordered[0]["currency"]]
        if len(priced) < 2:
            continue
        prices = np.array([float(row["price"]) for row in priced], dtype=float)
        median = float(np.median(prices))
        if median <= 0:
            continue
        rel = np.log(prices / median)
        matrix = [rel]
        for label in names[1:]:
            matrix.append(np.array([1.0 if row["merchant_class"] == label else 0.0 for row in priced]))
        prepared.append((bot, np.column_stack(matrix), 0))
    if len(prepared) < 8:
        return {"status": "not_identified", "reason": f"only {len(prepared)} usable runs", "n_runs": len(prepared)}
    keep = []
    for col in range(len(names)):
        if any(float(np.std(item[1][:, col])) > 1e-8 for item in prepared):
            keep.append(col)
    if not keep:
        return {"status": "not_identified", "reason": "no varying covariate", "n_runs": len(prepared)}
    used = [names[i] for i in keep]
    datasets = [(bot, matrix[:, keep], chosen) for bot, matrix, chosen in prepared]
    fit = _fit_logit(datasets)
    if fit is None:
        return {"status": "not_identified", "reason": "hessian singular or separated", "n_runs": len(datasets), "features": used}
    bots = sorted({bot for bot, _, _ in datasets})
    by_bot = defaultdict(list)
    for item in datasets:
        by_bot[item[0]].append(item)
    rng_seed = 20261028
    import random
    rng = random.Random(rng_seed)
    boots = []
    attempted = 0
    if len(bots) >= 2:
        for _ in range(400):
            attempted += 1
            draw = [bots[rng.randrange(len(bots))] for _ in bots]
            sample = [row for bot in draw for row in by_bot[bot]]
            if len(sample) < 8:
                continue
            refit = _fit_logit(sample)
            if refit is None:
                continue
            boots.append(refit)
    intervals = {}
    if boots:
        for index, name in enumerate(used):
            col = sorted(row[index] for row in boots)
            intervals[name] = {
                "low": col[int(0.025 * (len(col) - 1))],
                "high": col[int(0.975 * (len(col) - 1))],
                "n_boot": len(col),
            }
    return {
        "status": "fitted",
        "n_runs": len(datasets),
        "n_bots": len(bots),
        "features": used,
        "reference": "retailer (editorial and unknown also sit in the reference when present)",
        "coefficients": {name: fit[index] for index, name in enumerate(used)},
        "cluster_bootstrap_95": intervals,
        "few_clusters": len(bots) < 20,
        "n_boot_attempted": attempted,
        "n_boot_converged": len(boots),
        "choice_set": "priced rows shown in the reply",
        "evidence_class": "inferred_model",
        "assumption": (
            "Rank 1 is a multinomial draw from the shown priced rows with "
            "utilities linear in log price relative to the reply median and in "
            "merchant class. The candidate set before the reply is unobserved, "
            "so a negative price coefficient is an association inside the shown "
            "list. The bootstrap resamples bots. Several bots contribute one "
            "chat of several prompts, so clusters are few and dependent on the "
            "October design."
        ),
    }


def _fit_logit(datasets: list[tuple]) -> list[float] | None:
    if not datasets:
        return None
    k = datasets[0][1].shape[1]
    beta = np.zeros(k)
    for _ in range(30):
        grad = np.zeros(k)
        hess = np.zeros((k, k))
        for _, matrix, chosen in datasets:
            eta = matrix @ beta
            eta = eta - eta.max()
            weights = np.exp(eta)
            probs = weights / weights.sum()
            expected = matrix.T @ probs
            grad += matrix[chosen] - expected
            hess += (matrix.T * probs) @ matrix - np.outer(expected, expected)
        try:
            step = np.linalg.solve(hess, grad)
        except np.linalg.LinAlgError:
            return None
        beta = beta + step
        if np.linalg.norm(step) < 1e-8:
            break
    if np.max(np.abs(beta)) > 12:
        return None
    return [float(value) for value in beta]


def _within_product(products: list[dict]) -> dict:
    grouped = defaultdict(list)
    for row in products:
        if row["role"] != "shopping" or row["identity_strength"] != "model":
            continue
        grouped[row["product_id"]].append(row)
    multi = []
    same_run = []
    for product_id, rows in sorted(grouped.items()):
        domains = sorted({row["domain"] for row in rows if row["domain"]})
        if len(domains) < 2:
            continue
        by_run = defaultdict(set)
        for row in rows:
            if row["domain"]:
                by_run[row["run_id"]].add(row["domain"])
        in_one_reply = {run_id: sorted(doms) for run_id, doms in by_run.items() if len(doms) >= 2}
        item = {
            "product_id": product_id,
            "n_rows": len(rows),
            "domains": domains,
            "record_ids": [row["record_id"] for row in rows],
            "run_ids": sorted({row["run_id"] for row in rows}),
        }
        multi.append(item)
        if in_one_reply:
            same_run.append({**item, "runs_with_two_domains": in_one_reply})
    return {
        "n_model_ids_on_two_or_more_domains": len(multi),
        "n_model_ids_with_two_domains_inside_one_reply": len(same_run),
        "note": (
            "A model id on two domains in different replies is not a choice the "
            "bot made from one candidate set. Only the inside-one-reply count "
            "is a within-list retailer comparison, and only of the retailers the "
            "reply happened to show."
        ),
        "examples": multi[:15],
        "same_reply_examples": same_run[:10],
    }


def _cohort_block(name: str, run_rows: list[dict], products_by_run: dict[str, list[dict]]) -> dict:
    lists = [products_by_run.get(row["run_id"], []) for row in run_rows]
    products = [item for group in lists for item in group]
    bots = sorted({row["bot"] for row in run_rows if row["bot"]})
    tops = [_top(group) for group in lists if group]
    merchant_top = defaultdict(int)
    for top in tops:
        merchant_top[top["merchant_class"] or "unknown"] += 1
    n_top = len(tops)
    domains = _domain_labels(products)
    domain_counts = defaultdict(int)
    for domain in domains:
        domain_counts[domain] += 1
    top_domains = sorted(domain_counts.items(), key=lambda item: (-item[1], item[0]))[:6]

    def domain_hhi(groups):
        return hhi(_domain_labels([item for group in groups for item in group]))

    def merchant_hhi(groups):
        return hhi([item["merchant_class"] for group in groups for item in group])

    return {
        "cohort": name,
        "n_runs": len(run_rows),
        "n_bots": len(bots),
        "bots": bots,
        "n_products": len(products),
        "run_ids": [row["run_id"] for row in run_rows],
        "single_bot": len(bots) <= 1,
        "merchant_product_slots": _share_rows(products, "merchant_class"),
        "v1_store_type_slots": _share_rows(products, "v1_store_type"),
        "top1_merchant": {
            key: wilson_interval(merchant_top.get(key, 0), n_top)
            for key in MERCHANT_ORDER
        },
        "domain_hhi": hhi(domains),
        "merchant_hhi": hhi([row["merchant_class"] for row in products]),
        "brand_hhi": hhi([row["brand_canonical"] for row in products if row["brand_canonical"]]),
        "domain_hhi_bootstrap": cluster_bootstrap(lists, domain_hhi, n_boot=2000, seed=20261028),
        "merchant_hhi_bootstrap": cluster_bootstrap(lists, merchant_hhi, n_boot=2000, seed=20261031),
        "top_domains": [{"domain": domain, "n": n} for domain, n in top_domains],
        "retrieval": dict(_counts(row["retrieval"] for row in run_rows)),
        "first_query_style": dict(_counts(row["first_query_style"] for row in run_rows if row["first_query_style"])),
        "interval_assumption": (
            "Run-level Wilson intervals treat replies as independent Bernoulli "
            "trials. Bootstrap intervals resample replies. "
            + (
                "This cohort is a single bot, so neither interval is a multi-bot interval."
                if len(bots) <= 1
                else "Replies that share a bot are not independent, so the interval is anti-conservative for a bot-level estimand."
            )
        ),
    }


def _counts(values) -> dict:
    from collections import Counter
    return dict(Counter(values))


def _budget(products: list[dict], runs: list[dict]) -> dict:
    by_run = _group(products, "run_id")
    rows = []
    for run in runs:
        if run["role"] != "shopping" or not run["budget"]:
            continue
        cap = float(run["budget"])
        shown = by_run.get(run["run_id"], [])
        priced = [
            row for row in shown
            if row["price"] and row["currency"] == run["budget_currency"]
        ]
        over = [row for row in priced if float(row["price"]) >= cap]
        rows.append({
            "run_id": run["run_id"],
            "budget": cap,
            "currency": run["budget_currency"],
            "priced": len(priced),
            "over": len(over),
            "under": len(priced) - len(over),
            "over_record_ids": [row["record_id"] for row in over],
        })
    return {
        "runs": rows,
        "priced_rows": sum(row["priced"] for row in rows),
        "over_rows": sum(row["over"] for row in rows),
        "evidence_class": "bot_self_report",
        "rule": "A shown price at or above the stated under-X cap counts as over. The lower end of a range is the stored price.",
    }


def _contrasts(products_by_run, runs_by_cohort) -> dict:
    def lists(cohort):
        return [products_by_run.get(row["run_id"], []) for row in runs_by_cohort.get(cohort, [])]

    specs = [
        ("us_retailer_r1_minus_r2", "us-r1", "us-r2", "retailer"),
        ("tr_marketplace_r1_minus_r2", "tr-r1", "tr-r2", "marketplace"),
        ("pref_brand_site_minus_tr_r1", "pref-tr", "tr-r1", "brand_site"),
    ]
    results = []
    pvalues = []
    for name, left, right, merchant in specs:
        result = permutation_pvalue(
            lists(left), lists(right),
            lambda groups, merchant=merchant: _mean_run_share(groups, merchant),
            n_perm=4999, seed=20261028,
        )
        result["name"] = name
        result["merchant"] = merchant
        result["assumption"] = (
            "Exchangeability of replies across the two cohorts. Each cohort "
            "here is one bot and, for the no-preference passes, one chat. "
            "The p-value is not a test of a stable cross-bot policy."
        )
        result["use_for_inference"] = False
        results.append(result)
        if result["p"] is not None:
            pvalues.append((name, result["p"]))
    adjusted = holm(pvalues) if pvalues else []
    bh = benjamini_hochberg(pvalues) if pvalues else []
    return {
        "tests": results,
        "holm_if_exchangeable": adjusted,
        "bh_if_exchangeable": bh,
        "holm_applies": False,
        "reason_holm_not_applied": (
            "Holm and Benjamini-Hochberg values are reported for the three "
            "descriptive contrasts under reply exchangeability. That assumption "
            "is false for these single-bot cohorts, so neither adjustment is used "
            "to support a claim."
        ),
    }


def build_analysis(runs: list[dict], products: list[dict], queries: list[dict]) -> dict:
    shopping_runs = _shopping_runs(runs)
    products_by_run = _group(products, "run_id")
    runs_by_cohort = _group(shopping_runs, "cohort")
    cohorts = {}
    for name in COHORT_ORDER:
        if name in runs_by_cohort:
            cohorts[name] = _cohort_block(name, runs_by_cohort[name], products_by_run)
    shopping_products = [row for row in products if row["role"] == "shopping"]
    all_lists = [products_by_run.get(row["run_id"], []) for row in shopping_runs]
    cheapest = _price_lists(all_lists, "min")
    dearest = _price_lists(all_lists, "max")
    price_tests = {
        "cheapest": within_list_permutation(cheapest, n_perm=4999, seed=20261028),
        "dearest": within_list_permutation(dearest, n_perm=4999, seed=20261029),
    }
    family = []
    if price_tests["cheapest"]["p_one_sided"] is not None:
        family.append(("rank1_unique_cheapest", price_tests["cheapest"]["p_one_sided"]))
    if price_tests["dearest"]["p_one_sided"] is not None:
        family.append(("rank1_unique_dearest", price_tests["dearest"]["p_one_sided"]))
    # Two-sided reporting: the permutation helper is one-sided (score >= observed).
    # For the dearest negative control that is the correct tail. Holm is applied
    # to these one-sided p-values and that choice is stated.
    logit_input = [
        (row["bot"], products_by_run.get(row["run_id"], []))
        for row in shopping_runs
        if row["bot"]
    ]
    catalog = [
        {"run_id": row["run_id"], "received": row["received"], "cohort": row["cohort"], "bot": row["bot"]}
        for row in shopping_runs if row["retrieval"] == "catalog"
    ]
    query_styles = defaultdict(int)
    for row in queries:
        query_styles[row["style"]] += 1
    return {
        "evidence_classes": {
            "receipts": "bot_self_report",
            "verification": "independently_observed",
            "models": "inferred_model",
        },
        "corpus": {
            "files_parsed_role_rows": len(runs),
            "shopping_runs": len(shopping_runs),
            "shopping_products": len(shopping_products),
            "queries": len(queries),
            "products_all_roles": len(products),
        },
        "cohorts": cohorts,
        "stability": _stability(products_by_run),
        "within_list_price": {
            "tests": price_tests,
            "holm": holm(family) if family else [],
            "p_values_are": "one-sided permutation p-values",
            "null": "Inside a reply, the unique cheapest or dearest priced row is equally likely to sit on any rank.",
            "does_not_say": "It does not say the bot ranked a retailer's full result list, because that list was not observed.",
        },
        "conditional_logit": _conditional_logit(logit_input),
        "descriptive_contrasts": _contrasts(products_by_run, runs_by_cohort),
        "within_product": _within_product(products),
        "budget": _budget(products, runs),
        "catalog_self_report": {
            "evidence_class": "bot_self_report",
            "n": len(catalog),
            "runs": catalog,
            "note": "retrieval=catalog means the receipt text matched the catalog phrasing in the v1 parser. It is not an execution trace.",
        },
        "query_styles": dict(query_styles),
        "verification": _verification_block(products),
        "candidate_set": (
            "The set of products the bot considered and dropped is unobserved, "
            "except where the receipt mentions one. Absence from a reply is not "
            "a low rank."
        ),
    }


def write_analysis(out_dir: Path | None = None) -> dict:
    out = out_dir or NORMALIZED
    runs, products, queries = corpus_tables()
    analysis = build_analysis(runs, products, queries)
    payload = _round(analysis)
    out.mkdir(parents=True, exist_ok=True)
    (out / "analysis.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return payload
