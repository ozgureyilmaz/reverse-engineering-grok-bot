"""Normalise the October corpus. Reads evidence/ and writes v2/normalized/.

Does not modify evidence/, data/, or figures/ from v1.
"""
from __future__ import annotations

import csv
import sys

from .classify import (
    RETAILER_RECODES,
    host_of,
    merchant_class,
    product_identity,
    query_flags,
    query_style,
    v1_store_type,
)
from .paths import NORMALIZED, V1_CODE, V1_TRANSCRIPTS

if str(V1_CODE) not in sys.path:
    sys.path.insert(0, str(V1_CODE))

from analyze import cohort_of  # noqa: E402
from receipts import load_runs  # noqa: E402

RUN_FIELDS = [
    "run_id", "corpus", "evidence_class", "source_file", "bot", "cohort", "role",
    "condition", "prompt_id", "family", "category", "market", "intended_market",
    "perturbation", "perturbation_id", "budget", "budget_currency", "received",
    "retrieval", "carryover", "n_products", "n_searches", "n_steps",
    "first_query", "first_query_style", "n_editorial_queries", "n_brand_queries",
    "n_model_queries", "n_generic_queries", "searches",
]
PRODUCT_FIELDS = [
    "record_id", "evidence_class", "corpus", "run_id", "source_file", "bot",
    "cohort", "role", "prompt_id", "family", "category", "perturbation",
    "perturbation_id", "market", "intended_market", "budget", "budget_currency",
    "received", "retrieval", "carryover", "rank", "product", "brand",
    "brand_canonical", "model", "product_id", "identity_strength", "v1_product_key",
    "price", "price_high", "currency", "price_vs_budget", "domain", "url",
    "link_key", "v1_store_type", "merchant_class", "merchant_recode_note", "alt_urls",
]
QUERY_FIELDS = [
    "query_id", "evidence_class", "run_id", "cohort", "position", "query",
    "style", "editorial", "brand", "model",
]


def _blank(value) -> str:
    if value is None:
        return ""
    return str(value)


def corpus_tables(transcripts=None):
    runs = load_runs(transcripts or V1_TRANSCRIPTS)
    run_rows = []
    product_rows = []
    query_rows = []
    for run in runs:
        cohort = cohort_of(run)
        styles = [query_style(q) for q in run.searches]
        flags = [query_flags(q) for q in run.searches]
        run_rows.append({
            "run_id": run.run_id,
            "corpus": "v1",
            "evidence_class": "bot_self_report",
            "source_file": run.source_file,
            "bot": run.bot,
            "cohort": cohort,
            "role": run.role,
            "condition": run.condition,
            "prompt_id": run.prompt_id,
            "family": run.family,
            "category": run.category,
            "market": run.market,
            "intended_market": run.intended_market,
            "perturbation": run.perturbation,
            "perturbation_id": run.perturbation_id,
            "budget": _blank(run.budget),
            "budget_currency": run.budget_currency,
            "received": run.received,
            "retrieval": run.retrieval,
            "carryover": run.carryover,
            "n_products": len(run.products),
            "n_searches": run.n_searches,
            "n_steps": run.n_steps,
            "first_query": run.searches[0] if run.searches else "",
            "first_query_style": styles[0] if styles else "",
            "n_editorial_queries": sum(1 for flag in flags if flag["editorial"]),
            "n_brand_queries": sum(1 for flag in flags if flag["brand"]),
            "n_model_queries": sum(1 for flag in flags if flag["model"]),
            "n_generic_queries": sum(1 for style in styles if style == "generic"),
            "searches": " || ".join(run.searches),
        })
        for index, query in enumerate(run.searches, start=1):
            flag = query_flags(query)
            query_rows.append({
                "query_id": f"v1:{run.run_id}#q{index}",
                "evidence_class": "bot_self_report",
                "run_id": run.run_id,
                "cohort": cohort,
                "position": index,
                "query": query,
                "style": query_style(query),
                "editorial": int(flag["editorial"]),
                "brand": int(flag["brand"]),
                "model": int(flag["model"]),
            })
        for product in run.products:
            identity = product_identity(product.product, product.brand)
            domain = product.domain or host_of(product.url)
            price_vs = ""
            if (
                product.price is not None
                and run.budget
                and product.currency
                and product.currency == run.budget_currency
            ):
                price_vs = f"{product.price / run.budget:.6f}"
            product_rows.append({
                "record_id": f"v1:{run.run_id}#{product.rank}",
                "evidence_class": "bot_self_report",
                "corpus": "v1",
                "run_id": run.run_id,
                "source_file": run.source_file,
                "bot": run.bot,
                "cohort": cohort,
                "role": run.role,
                "prompt_id": run.prompt_id,
                "family": run.family,
                "category": run.category,
                "perturbation": run.perturbation,
                "perturbation_id": run.perturbation_id,
                "market": run.market,
                "intended_market": run.intended_market,
                "budget": _blank(run.budget),
                "budget_currency": run.budget_currency,
                "received": run.received,
                "retrieval": run.retrieval,
                "carryover": run.carryover,
                "rank": product.rank,
                "product": product.product,
                "brand": product.brand,
                "brand_canonical": identity["brand_canonical"],
                "model": identity["model"],
                "product_id": identity["product_id"],
                "identity_strength": identity["identity_strength"],
                "v1_product_key": identity["v1_product_key"],
                "price": "" if product.price is None else f"{product.price:.2f}",
                "price_high": "" if product.price_high is None else f"{product.price_high:.2f}",
                "currency": product.currency,
                "price_vs_budget": price_vs,
                "domain": domain,
                "url": product.url,
                "link_key": product.link_key,
                "v1_store_type": v1_store_type(domain, product.brand),
                "merchant_class": merchant_class(domain, product.brand),
                "merchant_recode_note": RETAILER_RECODES.get(domain, ""),
                "alt_urls": product.alt_urls,
            })
    return run_rows, product_rows, query_rows


def _write_csv(path, rows, fields) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_normalized(out_dir=None) -> dict:
    out = out_dir or NORMALIZED
    runs, products, queries = corpus_tables()
    _write_csv(out / "v1_runs.csv", runs, RUN_FIELDS)
    _write_csv(out / "v1_products.csv", products, PRODUCT_FIELDS)
    _write_csv(out / "v1_queries.csv", queries, QUERY_FIELDS)
    shopping = [row for row in products if row["role"] == "shopping"]
    return {
        "runs": len(runs),
        "products": len(products),
        "shopping_products": len(shopping),
        "queries": len(queries),
    }
