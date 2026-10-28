# Findings

Statuses mean: **verified** (a count in the files, or an HTTP observation), **statistically supported** (a test whose stated assumptions hold), **inferred** (a model that goes past the test), **unknown** (not identified). UNEXECUTED experiments are not findings.

## Verified

- The October corpus has 49 shopping replies and 228 shown shopping products. Reparse of evidence/transcripts. shopping_runs=49, shopping_products=228.
- In bot-us-1 on 22 October, every shown product URL is a retailer page (Target or Best Buy). This is one chat (`bot-us-1`), not a US policy.
- The fresh US bot the same evening did not repeat that retailer pattern and shared no product link with the first pass.
- The two Turkey no-preference bots both showed mostly marketplace URLs, and they did not show the same marketplace.
- Fresh-bot link sets in this corpus are unstable. Brand sets overlap more than links. The top link never matched. The bootstrap intervals in that claim resample prompt-pairs. They are not multi-bot intervals.
- Three shopping replies dated 28 October name a product-catalog search. No 22 October shopping reply does. Public pages retrieved the same day do not describe that path. The phrase is verified. A catalog tool is not.
- Public Grok Bot documentation describes a cloud computer with a browser, persistent memory, and a checkout handoff that asks the person to approve payment. It does not publish a ranking formula.
- Retailer concentration in these chats is high inside some bots and is not evidence of intentional commercial prioritization. Concentration is verified. Commercial intent is not part of this bullet.
- The Turkey preference bot's shown URLs are mostly brand sites and a price-comparison host. They are not a Trendyol list. This is one bot, not a measured effect of the note.
- A fresh bot given an urgency prompt with no country priced headphones in lira and linked Turkish retailers.
- Shown prices stayed under a stated cap except where the reply said the cap could not be met.
- Independent fetches of the receipt URLs are the out-of-bot check on whether those pages existed when this study was rebuilt. 203 unique URLs from 228 shopping rows (1 row without a URL). Indexed 203. Outcomes: blocked 13, error 12, live 160, robots_forbidden 18. Redirect class: not_fetched 30, same_domain 39, same_url 134. Price agreement on product rows: match 33, mismatch 11, page_price_unparsed 183. Pages where the visible text said sponsored: 32.
- The same model code sometimes appears on more than one domain in the corpus. That is usually across replies, not a single choice set.

## Statistically supported

- No within-list price result cleared the Holm threshold. See C06 in the evidence matrix. Non-significance is not evidence that price is irrelevant.

No cross-bot difference is statistically supported. The design has one bot on each side of the headline contrasts. Reply-level p-values were computed and are not used (C19).

## Inferred

- The seven-stage picture is a way to read the receipts. It is not a module list.
- Fitted on 48 runs and 9 bots. Coefficients: log_price_vs_median=-0.609, marketplace=-0.378, brand_site=-0.725, price_comparison=-1.985. Cluster-bootstrap interval for log price vs the reply median: -1.328–-0.047 (249 of 400 resamples converged). Reference: retailer (editorial and unknown also sit in the reference when present). Few clusters: True. Merchant coefficients are not a cross-bot retailer preference. Draws that did not converge were dropped, so the interval is conditional on convergence. Status: inferred.
- Sample-size numbers for the unrun schedule are a normal approximation at p=0.5. Full tier 434 runs. Minimum viable tier 144 runs.

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
