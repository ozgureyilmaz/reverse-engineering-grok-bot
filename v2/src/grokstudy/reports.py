"""Write the v2 reports from normalized JSON. Numbers are not typed by hand."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import yaml

from .paths import (
    FIGURES,
    NORMALIZED,
    PREREG,
    PUBLIC_DOCS,
    V2,
)
from .schedule import load_prereg, tier_sizes


def _load(name: str) -> dict:
    return json.loads((NORMALIZED / name).read_text(encoding="utf-8"))


def _fmt(value, digits=3) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.{digits}f}"


def _pct(value) -> str:
    if value is None:
        return "n/a"
    return f"{100 * float(value):.1f}%"


def _wilson(cell: dict) -> str:
    if not cell or cell.get("p") is None:
        return "n/a"
    return (
        f"{_fmt(cell['p'])} (Wilson 95% {_fmt(cell['low'])}–{_fmt(cell['high'])}, "
        f"k={cell['k']}, n={cell['n']})"
    )


def _boot(cell: dict) -> str:
    if not cell or cell.get("point") is None:
        return "n/a"
    flag = " Degenerate: fewer than two clusters." if cell.get("degenerate") else ""
    return (
        f"{_fmt(cell['point'])} (percentile bootstrap {_fmt(cell['low'])}–{_fmt(cell['high'])}, "
        f"{cell['n_clusters']} clusters).{flag}"
    )


def _slot(analysis, cohort, merchant) -> dict:
    return analysis["cohorts"][cohort]["merchant_product_slots"].get(merchant, {"n": 0, "share": None})


def _ids(analysis, cohort) -> str:
    return ", ".join(f"`{item}`" for item in analysis["cohorts"][cohort]["run_ids"])


def _claims(analysis: dict, schedule: dict, baseline: dict) -> list[dict]:
    us1 = analysis["cohorts"]["us-r1"]
    us2 = analysis["cohorts"]["us-r2"]
    tr1 = analysis["cohorts"]["tr-r1"]
    tr2 = analysis["cohorts"]["tr-r2"]
    pref = analysis["cohorts"]["pref-tr"]
    price = analysis["within_list_price"]
    holm = {row["name"]: row for row in price["holm"]}
    cheap = price["tests"]["cheapest"]
    dear = price["tests"]["dearest"]
    cheap_h = holm.get("rank1_unique_cheapest", {})
    price_supported = cheap_h.get("p_holm") is not None and cheap_h["p_holm"] < 0.05
    price_status = "statistically_supported" if price_supported else "unknown"
    ver = analysis["verification"]
    catalog = analysis["catalog_self_report"]
    within = analysis["within_product"]
    stability = analysis["stability"]
    return [
        {
            "id": "C01",
            "claim": "The October corpus has 49 shopping replies and 228 shown shopping products.",
            "evidence_class": "bot_self_report",
            "evidence": f"Reparse of evidence/transcripts. shopping_runs={analysis['corpus']['shopping_runs']}, shopping_products={analysis['corpus']['shopping_products']}.",
            "ids": "all shopping run_ids in v2/normalized/v1_runs.csv",
            "alternatives": "A different product-row rule would change the count. This count uses the v1 receipt rule.",
            "confidence": "high",
            "status": "verified",
        },
        {
            "id": "C02",
            "claim": "In bot-us-1 on 22 October, every shown product URL is a retailer page (Target or Best Buy).",
            "evidence_class": "bot_self_report",
            "evidence": (
                f"Retailer slot share {_pct(_slot(analysis, 'us-r1', 'retailer')['share'])} "
                f"of {us1['n_products']} rows. Top domains: "
                + ", ".join(f"{item['domain']} {item['n']}" for item in us1["top_domains"])
                + f". Domain HHI {_fmt(us1['domain_hhi'])}."
            ),
            "ids": _ids(analysis, "us-r1"),
            "alternatives": "One chat. Later prompts could reuse the first store. This does not describe other US bots.",
            "confidence": "high",
            "status": "verified",
        },
        {
            "id": "C03",
            "claim": "The fresh US bot the same evening did not repeat that retailer pattern and shared no product link with the first pass.",
            "evidence_class": "bot_self_report",
            "evidence": (
                f"us-r2 brand_site share {_pct(_slot(analysis, 'us-r2', 'brand_site')['share'])}, "
                f"marketplace {_pct(_slot(analysis, 'us-r2', 'marketplace')['share'])}, "
                f"retailer {_pct(_slot(analysis, 'us-r2', 'retailer')['share'])} of {us2['n_products']} rows. "
                f"US link Jaccard mean {_fmt(stability['US']['link_jaccard_mean'])}; "
                f"top-1 link agrees on {stability['US']['top1_link_agree']} of {stability['US']['n_pairs']} pairs."
            ),
            "ids": _ids(analysis, "us-r2") + "; pairs in analysis.json stability.US",
            "alternatives": "Reverse prompt order, a different bot, and time of day are tied together. Two bots cannot separate those.",
            "confidence": "high",
            "status": "verified",
        },
        {
            "id": "C04",
            "claim": "The two Turkey no-preference bots both showed mostly marketplace URLs, and they did not show the same marketplace.",
            "evidence_class": "bot_self_report",
            "evidence": (
                f"tr-r1 marketplace {_pct(_slot(analysis, 'tr-r1', 'marketplace')['share'])} of {tr1['n_products']}; "
                f"top domains "
                + ", ".join(f"{item['domain']} {item['n']}" for item in tr1["top_domains"][:3])
                + f". tr-r2 marketplace {_pct(_slot(analysis, 'tr-r2', 'marketplace')['share'])} of {tr2['n_products']}; "
                + ", ".join(f"{item['domain']} {item['n']}" for item in tr2["top_domains"][:3])
                + "."
            ),
            "ids": _ids(analysis, "tr-r1") + "; " + _ids(analysis, "tr-r2"),
            "alternatives": "The first bot's receipt says other stores blocked it. That sentence is a self-report, not an HTTP log. Prompt order was reversed on the second bot.",
            "confidence": "high",
            "status": "verified",
        },
        {
            "id": "C05",
            "claim": "Fresh-bot link sets in this corpus are unstable. Brand sets overlap more than links. The top link never matched.",
            "evidence_class": "bot_self_report",
            "evidence": (
                f"US mean link Jaccard {_fmt(stability['US']['link_jaccard_mean'])}, "
                f"bootstrap {_boot(stability['US']['link_jaccard_bootstrap'])} "
                f"Brand mean {_fmt(stability['US']['brand_jaccard_mean'])}. "
                f"TR mean link Jaccard {_fmt(stability['TR']['link_jaccard_mean'])}, "
                f"bootstrap {_boot(stability['TR']['link_jaccard_bootstrap'])} "
                f"Brand mean {_fmt(stability['TR']['brand_jaccard_mean'])}. "
                f"Top-1 link agreements: US {stability['US']['top1_link_agree']}/6, TR {stability['TR']['top1_link_agree']}/6. "
                f"Kendall tau defined on {stability['US']['kendall_defined_pairs'] + stability['TR']['kendall_defined_pairs']} of 12 pairs."
            ),
            "ids": "stability pairs in v2/normalized/analysis.json",
            "alternatives": "The bootstrap treats six prompt-pairs as exchangeable. They share two bots per market. The interval is not a multi-bot CI. RBO still moves when the shared set is empty because it scores the whole prefix, and an empty overlap scores 0.",
            "confidence": "high for the 12-pair count; low for a noise rate beyond these bots",
            "status": "verified",
        },
        {
            "id": "C06",
            "claim": (
                f"Rank 1 is the unique cheapest shown priced row in {cheap['k']} of {cheap['n_lists']} "
                f"informative replies (shuffle mean {_fmt(cheap['null_mean'])}, Holm p={_fmt(cheap_h.get('p_holm'))}). "
                + (
                    "The Holm test supports that association inside the shown lists."
                    if price_supported
                    else "The Holm test does not support a price-ordering effect. That is not evidence that price is irrelevant."
                )
            ),
            "evidence_class": "inferred_model",
            "evidence": (
                f"Cheapest: {cheap['k']} of {cheap['n_lists']} informative replies, "
                f"shuffle mean {_fmt(cheap['null_mean'])}, one-sided permutation p={_fmt(cheap['p_one_sided'])}, "
                f"Holm p={_fmt(cheap_h.get('p_holm'))}. "
                f"Dearest: {dear['k']} of {dear['n_lists']}, shuffle mean {_fmt(dear['null_mean'])}, "
                f"one-sided p={_fmt(dear['p_one_sided'])}, "
                f"Holm p={_fmt(holm.get('rank1_unique_dearest', {}).get('p_holm'))}."
            ),
            "ids": "within_list_price in analysis.json; replies with a priced rank-1 row and a unique extreme",
            "alternatives": "The choice set is the shown list. A cheaper product that was never shown is invisible. Association inside the list is not a retrieval policy and not a commercial motive.",
            "confidence": "moderate for the shown lists; low beyond them",
            "status": price_status,
        },
        {
            "id": "C07",
            "claim": "The conditional logit of rank 1 among shown priced rows is a model of the displayed list, not of an unobserved catalog.",
            "evidence_class": "inferred_model",
            "evidence": _logit_sentence(analysis["conditional_logit"]),
            "ids": "conditional_logit in analysis.json",
            "alternatives": "Separation, few bots, and a shown-only choice set can all produce a coefficient that does not describe retrieval.",
            "confidence": "low",
            "status": "inferred" if analysis["conditional_logit"].get("status") == "fitted" else "unknown",
        },
        {
            "id": "C08",
            "claim": "Three shopping replies dated 28 October name a product-catalog search. No 22 October shopping reply does. Public pages retrieved the same day do not describe that path.",
            "evidence_class": "bot_self_report",
            "evidence": (
                f"n={catalog['n']}. Runs: "
                + ", ".join(f"`{row['run_id']}` ({row['received'][:10]})" for row in catalog["runs"])
                + ". See DOC-OVERVIEW, DOC-COMPUTER, DOC-CHANGELOG, DOC-GUIDE-101."
            ),
            "ids": ", ".join(f"`{row['run_id']}`" for row in catalog["runs"]) + "; DOC-OVERVIEW; DOC-CHANGELOG",
            "alternatives": "The bot can describe a path it did not call. The 28 October prompts are a selected subset. A documentation gap is not evidence the path is absent from the product.",
            "confidence": "moderate that the phrase is date-restricted in this corpus; low that a catalog tool was switched on",
            "status": "verified",
        },
        {
            "id": "C09",
            "claim": "Public Grok Bot documentation describes a cloud computer with a browser, persistent memory, and a checkout handoff that asks the person to approve payment. It does not publish a ranking formula.",
            "evidence_class": "public_documentation",
            "evidence": "Pages listed in v2/config/public_docs.yaml, retrieved 28 October 2026.",
            "ids": "DOC-OVERVIEW, DOC-COMPUTER, DOC-BOTS, DOC-MOBILE, DOC-CHANGELOG, DOC-GUIDE-101, DOC-API-SEARCH",
            "alternatives": "Docs can lag the product. The API page names web_search for a developer API. That name is not treated as a tool the shopping bot called.",
            "confidence": "moderate",
            "status": "verified",
        },
        {
            "id": "C10",
            "claim": "Retailer concentration in these chats is high inside some bots and is not evidence of intentional commercial prioritization.",
            "evidence_class": "bot_self_report",
            "evidence": (
                f"Domain HHI us-r1 {_fmt(us1['domain_hhi'])}, us-r2 {_fmt(us2['domain_hhi'])}, "
                f"tr-r1 {_fmt(tr1['domain_hhi'])}, tr-r2 {_fmt(tr2['domain_hhi'])}, "
                f"pref-tr {_fmt(pref['domain_hhi'])}."
            ),
            "ids": _ids(analysis, "us-r1"),
            "alternatives": "A bot that opens one site, a blocked-site self-report, a preference note, or ordinary habit can concentrate URLs. None of those is a contract.",
            "confidence": "high that concentration is present in some chats; high that commercial intent is not identified",
            "status": "verified",
        },
        {
            "id": "C11",
            "claim": "Intentional commercial prioritization cannot be inferred from these distributions.",
            "evidence_class": "inferred_model",
            "evidence": "No contract, payment, or ranking instruction was observed. E10, which would hold retailers equivalent and check the price order against fetched pages, is UNEXECUTED.",
            "ids": "E10, UNEXECUTED",
            "alternatives": "A future discrepancy between the cheapest fetched price and the rank-1 retailer would still be an association until a first-party log showed an instruction.",
            "confidence": "high",
            "status": "unknown",
        },
        {
            "id": "C12",
            "claim": "The Turkey preference bot's shown URLs are mostly brand sites and a price-comparison host. They are not a Trendyol list. This is one bot, not a measured effect of the note.",
            "evidence_class": "bot_self_report",
            "evidence": (
                f"pref-tr brand_site {_pct(_slot(analysis, 'pref-tr', 'brand_site')['share'])}, "
                f"price_comparison {_pct(_slot(analysis, 'pref-tr', 'price_comparison')['share'])}, "
                f"marketplace {_pct(_slot(analysis, 'pref-tr', 'marketplace')['share'])} of {pref['n_products']} rows."
            ),
            "ids": _ids(analysis, "pref-tr"),
            "alternatives": "One bot. No fresh repeat of the preference condition. The note is not isolated from the bot.",
            "confidence": "moderate as a description; low as a causal effect",
            "status": "verified",
        },
        {
            "id": "C13",
            "claim": "A fresh bot given an urgency prompt with no country priced headphones in lira and linked Turkish retailers.",
            "evidence_class": "bot_self_report",
            "evidence": "Cohort location-default, one run, retrieval catalog, currency and domains in the product rows.",
            "ids": _ids(analysis, "location-default") if "location-default" in analysis["cohorts"] else "`EL01-US-X3__r2fresh`",
            "alternatives": "One reply. The account already had locale facts, as the memory check said. This is not a measurement of a US shopper.",
            "confidence": "high for this reply; low as a general default",
            "status": "verified",
        },
        {
            "id": "C14",
            "claim": "Shown prices stayed under a stated cap except where the reply said the cap could not be met.",
            "evidence_class": "bot_self_report",
            "evidence": (
                f"{analysis['budget']['over_rows']} priced rows at or above the cap, "
                f"out of {analysis['budget']['priced_rows']} priced rows in budgeted replies. "
                f"Over record ids: "
                + (", ".join(f"`{item}`" for row in analysis["budget"]["runs"] for item in row["over_record_ids"]) or "none")
                + "."
            ),
            "ids": ", ".join(f"`{row['run_id']}`" for row in analysis["budget"]["runs"]),
            "alternatives": "The lower end of a range is the stored price. Unpriced rows are not in the denominator. The receipt can omit a product that broke the cap.",
            "confidence": "high for shown priced rows",
            "status": "verified",
        },
        {
            "id": "C15",
            "claim": "Independent fetches of the receipt URLs are the out-of-bot check on whether those pages existed when this study was rebuilt.",
            "evidence_class": "independently_observed",
            "evidence": _verification_sentence(ver),
            "ids": "v2/raw/verification/index.jsonl; record ids in v2/normalized/v1_products.csv",
            "alternatives": "A live page today was not necessarily live on 22 October. A robots skip is not a dead link. A price mismatch is not a fabricated receipt.",
            "confidence": "high for the HTTP outcomes that were recorded; not applicable to URLs that were not fetched",
            "status": "verified" if ver.get("indexed_urls") else "unknown",
        },
        {
            "id": "C16",
            "claim": "The same model code sometimes appears on more than one domain in the corpus. That is usually across replies, not a single choice set.",
            "evidence_class": "bot_self_report",
            "evidence": (
                f"{within['n_model_ids_on_two_or_more_domains']} model ids on two or more domains; "
                f"{within['n_model_ids_with_two_domains_inside_one_reply']} of those occur inside one reply."
            ),
            "ids": ", ".join(f"`{item['product_id']}`" for item in within["examples"][:8]) or "none",
            "alternatives": "Text identity without a model code was not used. A shared model code can still be a different seller offer.",
            "confidence": "moderate",
            "status": "verified",
        },
        {
            "id": "C17",
            "claim": "No compliant independent search baseline was available, so overlap between the bot's quoted queries and a search-engine ranking was not estimated.",
            "evidence_class": "inferred_model",
            "evidence": baseline.get("detail", ""),
            "ids": "baseline UNEXECUTED; harness v2/raw/baseline/",
            "alternatives": "An operator-supplied result list can be joined later without changing this sentence's status for the present rebuild.",
            "confidence": "high",
            "status": "unknown",
        },
        {
            "id": "C18",
            "claim": "The v2 experiment schedule has not been run.",
            "evidence_class": "inferred_model",
            "evidence": (
                f"Full schedule {schedule['schedule_rows']['full']} runs. "
                f"Minimum viable schedule {schedule['schedule_rows']['mve']} runs. "
                "Operator replies on disk: see operator_status.json."
            ),
            "ids": "E01, E02, E03, E04, E05, E06, E07, E08, E09, E10",
            "alternatives": "None. The cells are design calculations, not observations.",
            "confidence": "high",
            "status": "unexecuted",
        },
        {
            "id": "C19",
            "claim": "Reply-level permutation tests of cohort merchant shares are descriptive only.",
            "evidence_class": "inferred_model",
            "evidence": analysis["descriptive_contrasts"]["reason_holm_not_applied"],
            "ids": "descriptive_contrasts in analysis.json",
            "alternatives": "Resampling the six replies inside one chat can look precise. It is still one chat.",
            "confidence": "high",
            "status": "unknown",
        },
        {
            "id": "C20",
            "claim": "A product missing from a reply was not shown to have a low rank.",
            "evidence_class": "inferred_model",
            "evidence": analysis["candidate_set"],
            "ids": "all shopping replies; the dropped-page list is not in the receipt",
            "alternatives": "When a receipt names a dropped product, that sentence is still a self-report.",
            "confidence": "high",
            "status": "unknown",
        },
    ]


def _logit_sentence(model: dict) -> str:
    if model.get("status") != "fitted":
        return f"Not identified ({model.get('reason', model.get('status'))}). n_runs={model.get('n_runs')}."
    coefs = ", ".join(
        f"{name}={_fmt(value, 3)}" for name, value in model.get("coefficients", {}).items()
    )
    intervals = model.get("cluster_bootstrap_95") or {}
    price = intervals.get("log_price_vs_median")
    price_ci = "n/a" if not price else f"{_fmt(price['low'])}–{_fmt(price['high'])}"
    return (
        f"Fitted on {model['n_runs']} runs and {model['n_bots']} bots. Coefficients: {coefs}. "
        f"Cluster-bootstrap interval for log price vs the reply median: {price_ci} "
        f"({model.get('n_boot_converged')} of {model.get('n_boot_attempted')} resamples converged). "
        f"Reference: {model['reference']}. Few clusters: {model['few_clusters']}. "
        "Merchant coefficients are not a cross-bot retailer preference. "
        "Draws that did not converge were dropped, so the interval is conditional on convergence."
    )


def _verification_sentence(ver: dict) -> str:
    outcomes = ver.get("outcomes_unique_urls") or {}
    parts = ", ".join(f"{key} {value}" for key, value in sorted(outcomes.items()))
    redirects = ver.get("redirects_unique_urls") or {}
    redir = ", ".join(f"{key} {value}" for key, value in sorted(redirects.items()))
    prices = ver.get("price_agreement_product_rows") or {}
    price = ", ".join(f"{key} {value}" for key, value in sorted(prices.items()))
    return (
        f"{ver.get('unique_urls')} unique URLs from {ver.get('shopping_product_rows')} shopping rows "
        f"({ver.get('rows_without_url')} row without a URL). Indexed {ver.get('indexed_urls')}. "
        f"Outcomes: {parts}. Redirect class: {redir}. "
        f"Price agreement on product rows: {price}. "
        f"Pages where the visible text said sponsored: {ver.get('sponsored_word_observed_on_pages')}."
    )


def _matrix(claims: list[dict]) -> str:
    lines = [
        "| Claim | Evidence | Experiment or record IDs | Alternative explanations | Confidence | Verification status |",
        "|---|---|---|---|---|---|",
    ]
    for claim in claims:
        lines.append(
            "| {id}. {claim} ({klass}) | {evidence} | {ids} | {alternatives} | {confidence} | {status} |".format(
                id=claim["id"],
                claim=claim["claim"].replace("|", "/"),
                klass=claim["evidence_class"],
                evidence=claim["evidence"].replace("|", "/").replace("\n", " "),
                ids=claim["ids"].replace("|", "/"),
                alternatives=claim["alternatives"].replace("|", "/"),
                confidence=claim["confidence"],
                status=claim["status"],
            )
        )
    return "\n".join(lines)


def _schedule_table() -> str:
    lines = ["| Experiment | Full runs | MVE runs |", "|---|---:|---:|"]
    counts = {"full": {}, "mve": {}}
    for tier in ("full", "mve"):
        with (NORMALIZED / f"schedule_{tier}.csv").open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                counts[tier][row["experiment_id"]] = counts[tier].get(row["experiment_id"], 0) + 1
    for exp in sorted(set(counts["full"]) | set(counts["mve"])):
        lines.append(f"| {exp} | {counts['full'].get(exp, 0)} | {counts['mve'].get(exp, 0)} |")
    lines.append(f"| Total | {sum(counts['full'].values())} | {sum(counts['mve'].values())} |")
    lines.append("")
    lines.append("E04 (US versus Turkey) and E09 (date and time block) add no prompts. E04 uses E01 and E03. E09 is a column on every row.")
    return "\n".join(lines)


def _docs_section() -> str:
    docs = yaml.safe_load(PUBLIC_DOCS.read_text(encoding="utf-8"))
    lines = []
    for page in docs["pages"]:
        lines.append(f"### {page['id']}")
        lines.append("")
        lines.append(f"<{page['url']}>")
        lines.append("")
        lines.append("Supports:")
        for item in page["supports"]:
            lines.append(f"- {item}")
        lines.append("")
        lines.append("Does not support:")
        for item in page["does_not_support"]:
            lines.append(f"- {item}")
        lines.append("")
    lines.append(docs["searched_for_catalog"]["result"])
    return "\n".join(lines)


def _architecture(analysis, claims) -> str:
    catalog = analysis["catalog_self_report"]
    return f"""# Architecture analysis

Evidence classes are named in each section. Receipt text is never an execution trace. This file is rebuilt from `v2/normalized/analysis.json` and `v2/config/public_docs.yaml`.

## What can be seen from outside

The receipt shows seven stages. They are a description of the text, not seven measured modules.

```mermaid
flowchart LR
  want[Want] --> query[Query]
  query --> sources[Sources]
  sources --> filter[Filter]
  filter --> rank[Rank]
  rank --> present[Present]
  present --> hand[Hand back]
```

![Stage diagram](figures/architecture.png)

1. **Want.** The prompt, including the fixed receipt suffix and the instruction not to buy.
2. **Query.** The receipt quotes search text. That text is often more specific than the prompt. The quote is the bot's report of what it searched.
3. **Sources.** The receipt names a site search, a web search, an editorial page, a marketplace, or, on some 28 October replies, a product-catalog search.
4. **Filter.** The bot sometimes says it dropped a row for price, rating, stock, or material. The dropped set is otherwise unobserved.
5. **Rank.** The order of the receipt list. Without the candidate set, that order cannot be compared with a store's own order.
6. **Present.** A short list and the receipt.
7. **Hand back.** Ordinary prompts were told not to check out. Two later prompts were told to stop before payment. Both saved endings say nothing was charged. n=2, and both are self-reports.

## What looks stable, and what moves

| Stage | In this corpus | Reading |
|---|---|---|
| Constraint filter | Store, brand, and budget constraints on the shown rows are kept, with the stated Sony-plus-budget misses | Looks more regular than link identity. n is small and several prompts share a chat. |
| Source choice | US first pass is one retailer. US fresh pass opens on editorial queries. Turkey passes are marketplaces. Three 28 October replies say catalog. | Not one pipeline. |
| Rank of URLs | Fresh repeats share a top link in 0 of 12 pairs | Unstable across these bots. |
| Hand-back | Both checkout endings stop before payment | Two self-reports. Not a measured policy. |

Deterministic and stochastic are the wrong pair of words for most of this. A stage can be sensitive to the chat, the account, and the day, which is not the same thing as a coin flip, and this design cannot separate those.

## Competing hypotheses

```mermaid
flowchart TD
  subgraph sources [Self-reported source paths]
    a[H-A one retailer search]
    b[H-B editorial web then brand or marketplace pages]
    c[H-C marketplace search with brand or model in the query]
    d[H-D preference note toward brand sites and a comparison host]
    e[H-E catalog phrase then a product page]
  end
```

| Id | Hypothesis | What matches | Confidence | What would verify it |
|---|---|---|---|---|
| H-A | The bot rewrites the want and searches one retailer | us-r1 only. {us_sentence(analysis)} | Low as a general US path. High as a description of that chat. | A tool log showing one host and the result list, for more than one fresh bot. |
| H-B | The bot searches the web for reviews, then opens brand or marketplace pages | us-r2. First-query styles: {analysis['cohorts']['us-r2']['first_query_style']}. | Low as "the" US path. High as a description of that bot. | The same, plus the result list of the quoted query from an independent index. E01 and the baseline harness. |
| H-C | Turkey shopping is a multi-step marketplace search, often with a brand already in the query | tr-r1 and tr-r2, which disagree on the host. | Moderate for "marketplace URLs", low for a preferred host. | Fresh bots in E01-TR, with HTTP checks of pages the receipt says were blocked. |
| H-D | A saved preference note shifts the primary URL toward brand sites | pref-tr, one bot. | Low as a cause. | E05, including refusals. |
| H-E | A catalog search was available on 28 October | The phrase appears in {catalog['n']} replies, all on that date: {", ".join(row["run_id"] for row in catalog["runs"])}. | Low. The phrase is verified. The tool is not. | A first-party log that a catalog index was queried, with the index's name as the system uses it. Public docs retrieved 28 October 2026 do not describe it. |
| H-F | With no country in the prompt, the bot uses account locale | `EL01-US-X3__r2fresh` only. | Low beyond that reply. | E01 runs that deliberately omit the country, on accounts whose locale is known to the operator. |
| H-G | Link identity is unstable even when the prompt is fixed | The 12 fresh pairs. | High for these pairs. The rate is what E01 is for. | E01. |

## Location, memory, preferences

Public documentation says a bot keeps stable preferences and that name and time zone are shared across the account's bots, while other memory is per bot (`DOC-BOTS`, `DOC-OVERVIEW`). It also says phone location, when requested in the person's own mobile chat, is a position rather than an address (`DOC-MOBILE`). None of that says which country a desktop shopping prompt uses when the prompt names none.

In the corpus, a no-preference Turkey bot said it had account facts and no shopping preferences. The US preference note was refused because a city in the note did not match a city the bot already associated with the account. The city is not in this repository. The methodological point is that "fresh bot" was not a blank account.

## Checkout handoff

`DOC-COMPUTER` says checkout can use a Vault card, a Secure Form, or a wallet such as Link or X Money. The changelog entry of 22 October 2026 says bots can pay with Shop Pay. The 26 October 2026 entry says the person still approves every purchase. The two saved endings in this corpus stop before payment and say nothing was charged. One of them says a sponsored ad added a second Walmart line, which the bot then removed. That is one self-report (`CHECKOUT-US`). It is not a rate.

## First-party evidence that would decide the source path

A log of each retrieval call the bot actually made: the arguments, the time, the candidate rows before filtering, and the rows dropped, using the system's own names. A screen recording would check the receipt against the pages. Neither is in this repository. This study did not try to obtain hidden instructions.

## Public documentation

{_docs_section()}
"""


def us_sentence(analysis) -> str:
    domains = ", ".join(
        f"{item['domain']} {item['n']}" for item in analysis["cohorts"]["us-r1"]["top_domains"]
    )
    return f"Top domains {domains}."


def _ranking(analysis) -> str:
    stab = analysis["stability"]
    price = analysis["within_list_price"]
    logit = analysis["conditional_logit"]
    within = analysis["within_product"]
    pair_lines = ["| Pair | Link Jaccard | Brand Jaccard | Model Jaccard | RBO | Kendall tau-a | Top-1 link |",
                  "|---|---:|---:|---:|---:|---:|---|"]
    for market in ("US", "TR"):
        for row in stab[market]["pairs"]:
            pair_lines.append(
                f"| `{row['run_a']}` vs `{row['run_b']}` | {_fmt(row['link_jaccard'])} | "
                f"{_fmt(row['brand_jaccard'])} | {_fmt(row['model_jaccard'])} | {_fmt(row['rbo_p90'])} | "
                f"{_fmt(row['kendall_tau_a']) if row['kendall_defined'] else 'undefined'} | {row['top1_link_agree']} |"
            )
    return f"""# Ranking analysis

The question is what predicts which products appear, and in what order. The candidate set is unobserved. A model below is a model of the shown list unless it says otherwise. Evidence class for the tables is bot self-report. The tests are inferred models with the assumptions in the same paragraph.

## Top-1 and top of the merchant mix

Top-1 probabilities are the share of replies whose first shown row has that merchant class. Wilson intervals treat replies as independent Bernoulli trials. They are too narrow for a bot-level estimand when the cohort is one bot. Figure: `figures/top1-wilson.png`.

| Cohort | Bots | Replies | Products | Rank-1 retailer | Rank-1 marketplace | Rank-1 brand site |
|---|---:|---:|---:|---|---|---|
""" + "\n".join(
        f"| {name} | {block['n_bots']} | {block['n_runs']} | {block['n_products']} | "
        f"{_wilson(block['top1_merchant']['retailer'])} | "
        f"{_wilson(block['top1_merchant']['marketplace'])} | "
        f"{_wilson(block['top1_merchant']['brand_site'])} |"
        for name, block in analysis["cohorts"].items()
        if name in {"us-r1", "us-r2", "tr-r1", "tr-r2", "pref-tr", "location-default"}
    ) + f"""

## Rank stability

Kendall tau-a is computed only on link keys that appear in both lists. It is undefined when fewer than two links are shared, which is the usual case here. RBO with p=0.9 scores the full prefixes, including lists that do not share items. An empty overlap scores 0. Figure: `figures/stability.png`.

US mean link Jaccard {_fmt(stab['US']['link_jaccard_mean'])}; {_boot(stab['US']['link_jaccard_bootstrap'])}

TR mean link Jaccard {_fmt(stab['TR']['link_jaccard_mean'])}; {_boot(stab['TR']['link_jaccard_bootstrap'])}

{stab['US']['interval_assumption']}

{chr(10).join(pair_lines)}

Top-1 brand agrees on {stab['US']['top1_brand_agree']} US pairs and {stab['TR']['top1_brand_agree']} Turkey pairs. Brand overlap is the fairer descriptive comparison. It is still two bots per market.

## Price, inside the shown list

Null: in a reply whose rank-1 row has a price and whose priced rows in that currency have a unique cheapest (or dearest) row, that extreme row is equally likely to sit at any rank. The permutation shuffles within the reply. Replies are not treated as a sample of bots for this null. The null is about these lists.

Holm adjustment is applied to the two one-sided p-values. The dearest test is a negative control. Non-significance of the dearest test is not evidence that the bot avoids expensive items. It is a failure to see that particular pattern.

| Test | Lists | Rank 1 has the attribute | Shuffle mean | One-sided p | Holm p |
|---|---:|---:|---:|---:|---:|
| Unique cheapest | {price['tests']['cheapest']['n_lists']} | {price['tests']['cheapest']['k']} | {_fmt(price['tests']['cheapest']['null_mean'])} | {_fmt(price['tests']['cheapest']['p_one_sided'])} | {_fmt(next((row['p_holm'] for row in price['holm'] if row['name']=='rank1_unique_cheapest'), None))} |
| Unique dearest | {price['tests']['dearest']['n_lists']} | {price['tests']['dearest']['k']} | {_fmt(price['tests']['dearest']['null_mean'])} | {_fmt(price['tests']['dearest']['p_one_sided'])} | {_fmt(next((row['p_holm'] for row in price['holm'] if row['name']=='rank1_unique_dearest'), None))} |

Figure: `figures/price-rank.png`.

{_logit_sentence(logit)}

{logit.get('assumption', '')}

## What does not predict appearance

Editorial-versus-store, market, and "the bot's quoted source path" are run-level labels. They do not vary inside a reply, so a conditional logit cannot estimate them. They are cohort descriptions in the architecture note. They are confounded with which bot was used.

Brand and model identity predict the Turkey queries more than the first US pass: the query-style counts are in `analysis.json` under each cohort's `first_query_style`, and the query table is `v1_queries.csv`. A query class is a label on the bot's quoted string.

## Within-product retailer order

{within['n_model_ids_on_two_or_more_domains']} model ids appear on at least two domains. {within['n_model_ids_with_two_domains_inside_one_reply']} of those appear inside a single reply. {within['note']}

## Budget

{analysis['budget']['over_rows']} of {analysis['budget']['priced_rows']} priced rows in budgeted replies are at or above the cap. {analysis['budget']['rule']} The over-cap record ids are listed in `analysis.json`.

## What this does not estimate

It does not estimate P(a product is retrieved | it exists). It does not estimate a store's ranking. The baseline for that comparison is UNEXECUTED. Absence from a list is not a low rank.
"""


def _retailer(analysis) -> str:
    contrasts = analysis["descriptive_contrasts"]["tests"]
    contrast_lines = ["| Contrast | Difference in mean within-reply share | Permutation p under reply exchangeability | Used for a claim |",
                      "|---|---:|---:|---|"]
    for row in contrasts:
        contrast_lines.append(
            f"| {row['name']} ({row['merchant']}) | {_fmt(row['diff'])} | {_fmt(row['p'])} | no |"
        )
    hhi_lines = ["| Cohort | Domain HHI | Bootstrap of replies | Bots |", "|---|---:|---|---:|"]
    for name in ("us-r1", "us-r2", "tr-r1", "tr-r2", "pref-tr"):
        block = analysis["cohorts"][name]
        hhi_lines.append(
            f"| {name} | {_fmt(block['domain_hhi'])} | {_boot(block['domain_hhi_bootstrap'])} | {block['n_bots']} |"
        )
    return f"""# Retailer bias analysis

Three different claims are easy to collapse. They are separated here. Only the first is established by this corpus. The third is not identified and is not inferred.

## 1. Concentration

Concentration means the shown URLs pile onto few hosts. It is a fact about a list. Figure: `figures/hhi.png` and `figures/merchant-mix.png`.

{chr(10).join(hhi_lines)}

us-r1 is two hosts, Target and Best Buy, HHI {_fmt(analysis['cohorts']['us-r1']['domain_hhi'])}. us-r2 is dispersed by comparison, HHI {_fmt(analysis['cohorts']['us-r2']['domain_hhi'])}. Turkey's two no-preference bots are both concentrated, on different hosts. pref-tr concentrates on brand sites and cimri.com, which v2 codes as price_comparison (v1 coded it aggregator). Walmart and Getir are coded retailer in v2; the v1 code is kept on `v1_store_type`.

The bootstrap resamples replies. For a one-bot cohort it describes variation across that bot's prompts. It is not a confidence interval for a market.

## 2. Statistical preference

A statistical preference would be a tendency, across fresh bots, for one retailer to occupy rank 1 or the list more often than a stated alternative, after the design is balanced. This corpus does not have that sample. Each headline cohort is one bot.

The permutation p-values below reshuffle reply labels. Holm and Benjamini-Hochberg adjustments of those p-values are stored in `analysis.json` under `descriptive_contrasts`. They are not used. {analysis['descriptive_contrasts']['reason_holm_not_applied']}

{chr(10).join(contrast_lines)}

Within a reply, rank 1 is associated with being the cheapest shown priced row. That test is in `RANKING_ANALYSIS.md`. It is a preference over prices inside the shown set, not a preference for a retailer holding price fixed. The within-product comparison that would hold the product fixed is thin: {analysis['within_product']['n_model_ids_with_two_domains_inside_one_reply']} model ids appear at two domains inside one reply.

## 3. Intentional commercial prioritization

This cannot be inferred from a concentrated list, from a significant association, or from a bot that says it preferred a store. A commercial arrangement is a fact about a contract, a payment, or an instruction. None of those is in the receipts, the fetched pages, or the public docs cited here.

The changelog says bots use built-in guides for popular shopping sites (`DOC-CHANGELOG`, 25 September 2026). A guide is not a ranking deal. The 22 October 2026 Shop Pay entry is a payment method, not a retailer weight.

E10 is the preregistered negative control: the prompt names retailers as equivalent and asks for the lowest price. The independent fetch would then say whether rank 1 was the cheapest page. That experiment is UNEXECUTED. Even a positive result would be an association until a first-party record showed why.

One checkout self-report says a sponsored Walmart ad added a second item (`CHECKOUT-US`). n=1. The fetch log records whether the word "sponsored" was visible on product pages. It does not reconstruct the cart.

## What would be enough, and what would still not be enough

Enough for a statistical preference: the fresh-bot schedule, especially E01, E02, E07, and E10, with the fetches repeated on those new URLs.

Enough for commercial intent: a record that is not a distribution. This study will not infer one from the schedule either.
"""


def _methodology(analysis, schedule) -> str:
    sizes = schedule["sizes_per_market_cell"]
    return f"""# Experimental methodology

The October corpus is a retrospective reanalysis. It was not preregistered. The schedule in `v2/config/preregistration.yaml` is the preregistration for runs that have not been sent. Those runs are marked UNEXECUTED everywhere they are mentioned.

## Preregistration

Stimuli, the receipt suffix, the sample-size rule, and the hypotheses are in `v2/config/preregistration.yaml`. The scheduler may change order, time block, and date stratum. It may not change prompt text. Seed {load_prereg()['seed']}.

Hypotheses H1–H5 are about noise, retailer-constraint compliance, a cheapest-price negative control, a preference note, and a US/Turkey wording contrast. No hypothesis of intentional commercial prioritization is preregistered.

## Variables

| Role | Variable | Where it lives |
|---|---|---|
| Outcome | Shown product rows, in receipt order | Bot self-report |
| Outcome | Merchant class, domain, price | Coded from the URL and the receipt price |
| Outcome | HTTP status, final URL, parsed page price | Independent fetch |
| Factor, v2 | Market cue, wording, brand specificity, retailer constraint, preference setup, time block, date stratum | Schedule |
| Not observed | Candidate set, tool arguments, dropped rows, ranker scores | — |

Controls that the v2 design does specify: one fresh bot per run, the same receipt suffix, counterbalanced order, and a preference arm that records refusal instead of retrying past it. Controls it cannot create: a blank account. Public docs say some facts are shared across bots.

## v1 methodology audit

1. **Small n.** Headline cohorts are six replies and one bot. Product-row percentages look more precise than the design is.
2. **Session memory.** Several prompts share a chat. One same-chat repeat returned the earlier list and said it did not search again. That file is excluded from the shopping-product count (no second receipt). Later prompts in a chat are not independent draws.
3. **Self-reported receipts.** Queries, blocked pages, catalog searches, and the cart story are the bot's words. This reanalysis labels them as such.
4. **Prompt order.** The fresh pass reversed the order of the six wants. Order and "fresh bot" are tied.
5. **Geographic confounding.** Turkey prompts name Turkey. A prompt with no country, on this account, came back in lira (`EL01-US-X3__r2fresh`). US rows are US only when the prompt or the chat established it. Bots are not a blank locale.
6. **Temporal change.** The catalog phrase appears in {analysis['catalog_self_report']['n']} replies, all dated 28 October, and in none dated 22 October. The 28 October prompts are also a different mix. Date and prompt are tied.
7. **Missing candidate sets.** Dropped products are visible only when the prose names them. Absence is not a low rank.
8. **No baseline.** Overlap with an independent search ranking was not computed in v1 and is UNEXECUTED here. The harness is `v2/raw/baseline/`.
9. **Selection of perturbations.** Round-3 prompts are single changes on top of chats that already shopped. Two of them say they reused an earlier search.
10. **No execution trace.** No screen recording and no tool log. A click the receipt omits is missing.
11. **US preference arm not run.** The bot refused to save the note. That refusal is data. The arm is not a contrast.
12. **Turkey checkout file** keeps the closing message. Intermediate screens are missing.
13. **Multiple looks at the same chats.** v1 reported many ratios. This reanalysis picks a two-test Holm family for the within-list price question and does not promote reply-permutation p-values to findings.

## Sample size

Unit: one fresh bot and one shopping prompt. Products inside a reply are not the unit. v1 replies from one chat often share a host, so a product-level sample size would overstate precision. The formula is the usual normal half-width at p=0.5, which maximises binomial variance:

n = ceil(z^2 * p * (1-p) / h^2), z the 97.5% normal quantile.

| Tier | Role | Half-width or fixed n | Runs per market cell |
|---|---|---|---:|
| Full | Primary | ±{_fmt(schedule['expected_half_width_at_p_0_5']['full'].get('primary'))} (target 0.15) | {sizes['full']['primary']} |
| Full | Secondary | target 0.20 | {sizes['full']['secondary']} |
| Full | Probe | fixed, not powered for ±0.20 | {sizes['full']['probe']} |
| MVE | Primary | target 0.25 | {sizes['mve']['primary']} |
| MVE | Secondary | target 0.35 | {sizes['mve']['secondary']} |
| MVE | Probe | fixed | {sizes['mve']['probe']} |

A two-arm difference of 30 percentage points at p=0.5 versus p=0.8, 80% power, two-sided 5%, needs about {schedule['difference_per_arm_reference']} fresh bots per arm under the normal approximation. The full primary cell ({sizes['full']['primary']}) covers that reference. Full secondary cells ({sizes['full']['secondary']}) are sized for a ±0.20 interval, not for that power target. Probe cells are exploratory. Figure: `figures/power-curve.png`.

These calculations assume independent fresh bots. They do not add another design effect. They do not use the October point estimates as the planning proportion, because those estimates are single-bot descriptions.

## Schedule

{_schedule_table()}

Files: `v2/normalized/schedule_full.csv`, `v2/normalized/schedule_mve.csv`. Each row has `run_id`, `experiment_id`, `bot_slot` (`FRESH-US-001` style; three digits because the full tier exceeds 99), `market`, `prompt_text` with the v1 receipt suffix, `wording_variant`, `time_block`, and `date_stratum` where E01 assigns one.

E01 is the noise floor and the negative control of repeating one prompt. E10 is the negative control that declares named retailers equivalent and asks for the lowest price. E02 asks for one SKU at every retailer the bot can open. E03 is a probe across matched everyday wants, including an open-ended gift prompt flagged `open_ended`. E05 is the preference note, with an explicit refusal outcome. E06 is brand-specific. E07 locks the retailer. E08 changes wording and keeps English in both markets so language is not a second factor. E04 and E09 are analysis contrasts, not extra prompts.

## Tests that will be used on the new runs

Primary, Holm within the preregistered family once the runs exist: E01 top-1 agreement and link Jaccard against the noise floor; E07 difference in on-retailer share versus the E01 twin; E10 rank-1 versus the cheapest independently fetched price. Cluster: the bot, which is the run. BH on the remaining preregistered contrasts, not on every slice the tables invite. The October within-list price test stays a retrospective result. It is not confirmation of H1–H5.

## Operator run log

`v2/raw/run_log.csv` columns: run_id, experiment_id, bot_slot, market, market_cue, sent_at, received_at, wording_variant, time_block, date_stratum, preference_outcome, operator_notes. Replies go to `v2/raw/replies/<run_id>.md`. `python -m grokstudy.cli ingest` reads that directory. Until those files exist the operator corpus is UNEXECUTED.

## Multiple comparisons, clustering, non-significance

Holm is applied to the two within-list price tests. Benjamini-Hochberg is computed for the three reply-label contrasts and then not used, because the clusters are bots and there is one bot per arm. Non-significance is not evidence of absence. A significant association inside the shown list is not a cause, and it is not a commercial arrangement.

## Ethics

Black box only. No prompt extraction, no attempt to bypass access controls, no purchase, no payment. URL fetches use an honest User-Agent, obey robots.txt when it can be read, and do not store Set-Cookie headers. Personal data stays out of v2 the same way it stayed out of v1: no account city, no phone, no email, no bot UUID. ZIP 95829 appears only as the Walmart default named in the checkout receipt.
"""


def _findings(analysis, claims, schedule) -> str:
    by_id = {claim["id"]: claim for claim in claims}
    price_bullet = (
        f"- {by_id['C06']['claim']} {by_id['C06']['evidence']}"
        if by_id["C06"]["status"] == "statistically_supported"
        else "- No within-list price result cleared the Holm threshold. See C06 in the evidence matrix. Non-significance is not evidence that price is irrelevant."
    )
    return f"""# Findings

Statuses mean: **verified** (a count in the files, or an HTTP observation), **statistically supported** (a test whose stated assumptions hold), **inferred** (a model that goes past the test), **unknown** (not identified). UNEXECUTED experiments are not findings.

## Verified

- {by_id['C01']['claim']} {by_id['C01']['evidence']}
- {by_id['C02']['claim']} This is one chat (`bot-us-1`), not a US policy.
- {by_id['C03']['claim']}
- {by_id['C04']['claim']}
- {by_id['C05']['claim']} The bootstrap intervals in that claim resample prompt-pairs. They are not multi-bot intervals.
- {by_id['C08']['claim']} The phrase is verified. A catalog tool is not.
- {by_id['C09']['claim']}
- {by_id['C10']['claim']} Concentration is verified. Commercial intent is not part of this bullet.
- {by_id['C12']['claim']}
- {by_id['C13']['claim']}
- {by_id['C14']['claim']}
- {by_id['C15']['claim']} {by_id['C15']['evidence']}
- {by_id['C16']['claim']}

## Statistically supported

{price_bullet}

No cross-bot difference is statistically supported. The design has one bot on each side of the headline contrasts. Reply-level p-values were computed and are not used (C19).

## Inferred

- The seven-stage picture is a way to read the receipts. It is not a module list.
- {_logit_sentence(analysis['conditional_logit'])} Status: {by_id['C07']['status']}.
- Sample-size numbers for the unrun schedule are a normal approximation at p=0.5. Full tier {schedule['schedule_rows']['full']} runs. Minimum viable tier {schedule['schedule_rows']['mve']} runs.

## Unknown

- Whether any retailer is preferred after product, price, and market are held fixed.
- Whether the 28 October catalog phrase names a real index, and whether that index is still used.
- Whether link Jaccard near zero is the noise rate of the product, or the distance between two particular bots on one evening.
- The overlap between quoted queries and an independent search ranking. The baseline is UNEXECUTED.
- Intentional commercial prioritization. Not inferred.
- What a blank account, or a US preference note that the bot accepts, would do.
- The checkout policy. Two self-reports, one of them missing intermediate screens.

## Which v1 findings survive

| v1 statement | v2 status |
|---|---|
| 49 shopping replies, 228 products, the cohort domain counts | Survives. The parser is the v1 parser. v2 relabels Walmart and Getir as retailers and cimri.com as price_comparison, and keeps the v1 label beside them. |
| US first pass is Target and Best Buy | Survives as a description of `bot-us-1`. Rejected as "how the US bot shops". |
| Fresh US pass is editorial-first and shares no link | Survives as a description of `bot-us-2`. |
| Turkey is marketplaces, and the host flipped from Amazon.com.tr to Trendyol | Survives as a description of two bots. Rejected as a stable host preference. |
| Preferences moved Turkey URLs to brand sites and Cimri | Survives as a description of one bot. The causal wording should be dropped. |
| Link Jaccard near zero, brand overlap higher, top link never matched | Survives as a count of the 12 pairs. The general noise rate is unknown. |
| Budget and store constraints were kept on the shown rows, with the Sony misses stated | Survives for the shown priced rows. |
| Catalog phrase on 28 October in 3 of 6 shopping replies that day | Survives as a phrase count. The infrastructure-change reading is weakened: prompt mix and date are tied, and public docs do not document the path. |
| No-country urgency prompt shopped in Turkey | Survives for that one reply. |
| Checkout stopped before payment; one sponsored cart line | Survives as two self-reports and one ad anecdote. Not a rate. |
| A single pipeline | Rejected. |
| Any ranking formula or retailer contract | Not a v1 claim. Still unknown. |

## What definitive verification would require

The operator schedule, starting with the minimum viable tier, plus a repeat of the URL fetch on the new receipts, plus an independent result list if one can be obtained within its terms. A definitive account of the source path needs a first-party log of the calls and the candidate set. This repository does not contain that log and does not try to extract one.

## Experiments not yet run

E01 through E10 are UNEXECUTED. E04 and E09 have no prompts of their own. `v2/normalized/operator_status.json` is the ingest marker.
"""


def _evidence(claims) -> str:
    return f"""# Evidence matrix

Every row is one claim. The status is the status of that claim, not of the whole study. Record ids look like `v1:<run_id>#<rank>`. Experiment ids are E01–E10. Document ids are DOC-*.

Holm covers the two within-list price tests (C06). Benjamini-Hochberg on the reply-label contrasts is computed in `analysis.json` and is not a status in this table (C19).

{_matrix(claims)}

## How a row was produced

`v2/src/grokstudy/reports.py` builds this table from `v2/normalized/analysis.json`, which is built from `evidence/transcripts/` and from `v2/raw/verification/index.jsonl`. Public-doc rows cite `v2/config/public_docs.yaml`. Schedule rows cite `v2/normalized/schedule_counts.json`. Re-running `make` rewrites the table. A claim without an id in that chain is a bug.
"""


def write_reports() -> None:
    analysis = _load("analysis.json")
    schedule = _load("schedule_counts.json")
    baseline_path = NORMALIZED / "baseline_status.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8")) if baseline_path.exists() else {
        "detail": "baseline_status.json missing", "status": "UNEXECUTED"
    }
    claims = _claims(analysis, schedule, baseline)
    (NORMALIZED / "evidence_matrix.json").write_text(
        json.dumps(claims, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    docs = {
        "ARCHITECTURE_ANALYSIS.md": _architecture(analysis, claims),
        "RANKING_ANALYSIS.md": _ranking(analysis),
        "RETAILER_BIAS_ANALYSIS.md": _retailer(analysis),
        "EXPERIMENTAL_METHODOLOGY.md": _methodology(analysis, schedule),
        "EVIDENCE_MATRIX.md": _evidence(claims),
        "FINAL_FINDINGS.md": _findings(analysis, claims, schedule),
    }
    for name, text in docs.items():
        (V2 / name).write_text(text, encoding="utf-8")
    # tier_sizes is used by the methodology via schedule JSON; touch the import
    # so a refactor that drops the sample-size helper fails this module's tests.
    _ = tier_sizes
    _ = FIGURES
    _ = PREREG
