# Retailer bias analysis

Three different claims are easy to collapse. They are separated here. Only the first is established by this corpus. The third is not identified and is not inferred.

## 1. Concentration

Concentration means the shown URLs pile onto few hosts. It is a fact about a list. Figure: `figures/hhi.png` and `figures/merchant-mix.png`.

| Cohort | Domain HHI | Bootstrap of replies | Bots |
|---|---:|---|---:|
| us-r1 | 0.577 | 0.577 (percentile bootstrap 0.500–1.000, 6 clusters). | 1 |
| us-r2 | 0.138 | 0.138 (percentile bootstrap 0.120–0.272, 6 clusters). | 1 |
| tr-r1 | 0.454 | 0.454 (percentile bootstrap 0.222–0.852, 6 clusters). | 1 |
| tr-r2 | 0.501 | 0.501 (percentile bootstrap 0.296–0.762, 6 clusters). | 1 |
| pref-tr | 0.169 | 0.169 (percentile bootstrap 0.112–0.388, 6 clusters). | 1 |

us-r1 is two hosts, Target and Best Buy, HHI 0.577. us-r2 is dispersed by comparison, HHI 0.138. Turkey's two no-preference bots are both concentrated, on different hosts. pref-tr concentrates on brand sites and cimri.com, which v2 codes as price_comparison (v1 coded it aggregator). Walmart and Getir are coded retailer in v2; the v1 code is kept on `v1_store_type`.

The bootstrap resamples replies. For a one-bot cohort it describes variation across that bot's prompts. It is not a confidence interval for a market.

## 2. Statistical preference

A statistical preference would be a tendency, across fresh bots, for one retailer to occupy rank 1 or the list more often than a stated alternative, after the design is balanced. This corpus does not have that sample. Each headline cohort is one bot.

The permutation p-values below reshuffle reply labels. Holm and Benjamini-Hochberg adjustments of those p-values are stored in `analysis.json` under `descriptive_contrasts`. They are not used. Holm and Benjamini-Hochberg values are reported for the three descriptive contrasts under reply exchangeability. That assumption is false for these single-bot cohorts, so neither adjustment is used to support a claim.

| Contrast | Difference in mean within-reply share | Permutation p under reply exchangeability | Used for a claim |
|---|---:|---:|---|
| us_retailer_r1_minus_r2 (retailer) | 0.967 | 0.003 | no |
| tr_marketplace_r1_minus_r2 (marketplace) | -0.136 | 0.427 | no |
| pref_brand_site_minus_tr_r1 (brand_site) | 0.206 | 0.349 | no |

Within a reply, rank 1 is associated with being the cheapest shown priced row. That test is in `RANKING_ANALYSIS.md`. It is a preference over prices inside the shown set, not a preference for a retailer holding price fixed. The within-product comparison that would hold the product fixed is thin: 1 model ids appear at two domains inside one reply.

## 3. Intentional commercial prioritization

This cannot be inferred from a concentrated list, from a significant association, or from a bot that says it preferred a store. A commercial arrangement is a fact about a contract, a payment, or an instruction. None of those is in the receipts, the fetched pages, or the public docs cited here.

The changelog says bots use built-in guides for popular shopping sites (`DOC-CHANGELOG`, 25 September 2026). A guide is not a ranking deal. The 22 October 2026 Shop Pay entry is a payment method, not a retailer weight.

E10 is the preregistered negative control: the prompt names retailers as equivalent and asks for the lowest price. The independent fetch would then say whether rank 1 was the cheapest page. That experiment is UNEXECUTED. Even a positive result would be an association until a first-party record showed why.

One checkout self-report says a sponsored Walmart ad added a second item (`CHECKOUT-US`). n=1. The fetch log records whether the word "sponsored" was visible on product pages. It does not reconstruct the cart.

## What would be enough, and what would still not be enough

Enough for a statistical preference: the fresh-bot schedule, especially E01, E02, E07, and E10, with the fetches repeated on those new URLs.

Enough for commercial intent: a record that is not a distribution. This study will not infer one from the schedule either.
