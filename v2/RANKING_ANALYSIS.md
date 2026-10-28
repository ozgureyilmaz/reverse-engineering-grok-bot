# Ranking analysis

The question is what predicts which products appear, and in what order. The candidate set is unobserved. A model below is a model of the shown list unless it says otherwise. Evidence class for the tables is bot self-report. The tests are inferred models with the assumptions in the same paragraph.

## Top-1 and top of the merchant mix

Top-1 probabilities are the share of replies whose first shown row has that merchant class. Wilson intervals treat replies as independent Bernoulli trials. They are too narrow for a bot-level estimand when the cohort is one bot. Figure: `figures/top1-wilson.png`.

| Cohort | Bots | Replies | Products | Rank-1 retailer | Rank-1 marketplace | Rank-1 brand site |
|---|---:|---:|---:|---|---|---|
| us-r1 | 1 | 6 | 23 | 1.000 (Wilson 95% 0.610–1.000, k=6, n=6) | 0.000 (Wilson 95% 0.000–0.390, k=0, n=6) | 0.000 (Wilson 95% 0.000–0.390, k=0, n=6) |
| us-r2 | 1 | 6 | 28 | 0.000 (Wilson 95% 0.000–0.390, k=0, n=6) | 0.500 (Wilson 95% 0.188–0.812, k=3, n=6) | 0.500 (Wilson 95% 0.188–0.812, k=3, n=6) |
| tr-r1 | 1 | 6 | 38 | 0.000 (Wilson 95% 0.000–0.390, k=0, n=6) | 0.833 (Wilson 95% 0.436–0.970, k=5, n=6) | 0.167 (Wilson 95% 0.030–0.564, k=1, n=6) |
| tr-r2 | 1 | 6 | 31 | 0.000 (Wilson 95% 0.000–0.390, k=0, n=6) | 0.833 (Wilson 95% 0.436–0.970, k=5, n=6) | 0.167 (Wilson 95% 0.030–0.564, k=1, n=6) |
| pref-tr | 1 | 6 | 27 | 0.167 (Wilson 95% 0.030–0.564, k=1, n=6) | 0.167 (Wilson 95% 0.030–0.564, k=1, n=6) | 0.500 (Wilson 95% 0.188–0.812, k=3, n=6) |
| location-default | 1 | 1 | 4 | 1.000 (Wilson 95% 0.207–1.000, k=1, n=1) | 0.000 (Wilson 95% 0.000–0.793, k=0, n=1) | 0.000 (Wilson 95% 0.000–0.793, k=0, n=1) |

## Rank stability

Kendall tau-a is computed only on link keys that appear in both lists. It is undefined when fewer than two links are shared, which is the usual case here. RBO with p=0.9 scores the full prefixes, including lists that do not share items. An empty overlap scores 0. Figure: `figures/stability.png`.

US mean link Jaccard 0.000; 0.000 (percentile bootstrap 0.000–0.000, 6 clusters).

TR mean link Jaccard 0.054; 0.054 (percentile bootstrap 0.000–0.121, 6 clusters).

The bootstrap resamples the six prompt-pairs. Both passes in a market are one bot each, and the first pass is one chat. The interval is not a multi-bot confidence interval.

| Pair | Link Jaccard | Brand Jaccard | Model Jaccard | RBO | Kendall tau-a | Top-1 link |
|---|---:|---:|---:|---:|---:|---|
| `np-us__EL01-US__r1` vs `np-us__EL01-US__r2` | 0.000 | 0.400 | 0.000 | 0.000 | undefined | False |
| `np-us__EL02-US__r1` vs `np-us__EL02-US__r2` | 0.000 | 0.400 | 0.500 | 0.000 | undefined | False |
| `np-us__FA01-US__r1` vs `np-us__FA01-US__r2` | 0.000 | 0.000 | n/a | 0.000 | undefined | False |
| `np-us__GR01-US__r1` vs `np-us__GR01-US__r2` | 0.000 | 0.143 | n/a | 0.000 | undefined | False |
| `np-us__HO01-US__r1` vs `np-us__HO01-US__r2` | 0.000 | 0.000 | n/a | 0.000 | undefined | False |
| `np-us__GI01-US__r1` vs `np-us__GI01-US__r2` | 0.000 | 0.000 | n/a | 0.000 | undefined | False |
| `np-tr__EL01-TR__r1` vs `np-tr__EL01-TR__r2` | 0.000 | 0.400 | 0.100 | 0.000 | undefined | False |
| `np-tr__EL02-TR__r1` vs `np-tr__EL02-TR__r2` | 0.125 | 0.250 | 1.000 | 0.176 | undefined | False |
| `np-tr__FA01-TR__r1` vs `np-tr__FA01-TR__r2` | 0.000 | 0.143 | n/a | 0.000 | undefined | False |
| `np-tr__GR01-TR__r1` vs `np-tr__GR01-TR__r2` | 0.200 | 0.500 | n/a | 0.333 | -1.000 | False |
| `np-tr__HO01-TR__r1` vs `np-tr__HO01-TR__r2` | 0.000 | 0.600 | n/a | 0.000 | undefined | False |
| `np-tr__GI01-TR__r1` vs `np-tr__GI01-TR__r3` | 0.000 | 0.375 | n/a | 0.000 | undefined | False |

Top-1 brand agrees on 2 US pairs and 1 Turkey pairs. Brand overlap is the fairer descriptive comparison. It is still two bots per market.

## Price, inside the shown list

Null: in a reply whose rank-1 row has a price and whose priced rows in that currency have a unique cheapest (or dearest) row, that extreme row is equally likely to sit at any rank. The permutation shuffles within the reply. Replies are not treated as a sample of bots for this null. The null is about these lists.

Holm adjustment is applied to the two one-sided p-values. The dearest test is a negative control. Non-significance of the dearest test is not evidence that the bot avoids expensive items. It is a failure to see that particular pattern.

| Test | Lists | Rank 1 has the attribute | Shuffle mean | One-sided p | Holm p |
|---|---:|---:|---:|---:|---:|
| Unique cheapest | 48 | 14 | 11.078 | 0.196 | 0.391 |
| Unique dearest | 46 | 9 | 10.770 | 0.787 | 0.787 |

Figure: `figures/price-rank.png`.

Fitted on 48 runs and 9 bots. Coefficients: log_price_vs_median=-0.609, marketplace=-0.378, brand_site=-0.725, price_comparison=-1.985. Cluster-bootstrap interval for log price vs the reply median: -1.328–-0.047 (249 of 400 resamples converged). Reference: retailer (editorial and unknown also sit in the reference when present). Few clusters: True. Merchant coefficients are not a cross-bot retailer preference. Draws that did not converge were dropped, so the interval is conditional on convergence.

Rank 1 is a multinomial draw from the shown priced rows with utilities linear in log price relative to the reply median and in merchant class. The candidate set before the reply is unobserved, so a negative price coefficient is an association inside the shown list. The bootstrap resamples bots. Several bots contribute one chat of several prompts, so clusters are few and dependent on the October design.

## What does not predict appearance

Editorial-versus-store, market, and "the bot's quoted source path" are run-level labels. They do not vary inside a reply, so a conditional logit cannot estimate them. They are cohort descriptions in the architecture note. They are confounded with which bot was used.

Brand and model identity predict the Turkey queries more than the first US pass: the query-style counts are in `analysis.json` under each cohort's `first_query_style`, and the query table is `v1_queries.csv`. A query class is a label on the bot's quoted string.

## Within-product retailer order

9 model ids appear on at least two domains. 1 of those appear inside a single reply. A model id on two domains in different replies is not a choice the bot made from one candidate set. Only the inside-one-reply count is a within-list retailer comparison, and only of the retailers the reply happened to show.

## Budget

3 of 56 priced rows in budgeted replies are at or above the cap. A shown price at or above the stated under-X cap counts as over. The lower end of a range is the stored price. The over-cap record ids are listed in `analysis.json`.

## What this does not estimate

It does not estimate P(a product is retrieved | it exists). It does not estimate a store's ranking. The baseline for that comparison is UNEXECUTED. Absence from a list is not a low rank.
