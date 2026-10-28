# Dataset

`records.csv` and `records.jsonl` have one row per product the bot listed in a RECEIPT, in the order the receipt gave. A reply with no shown products (the same-chat gift repeat) is in `runs.csv` and not in `records.csv`.

The product rows come from the RECEIPT only. A URL in the prose, or a page the bot opened and then dropped, is not a row. Lines the bot marks as mentioned but not shown are not rows. HTML entities in names are unescaped here; `evidence/` keeps the saved text.

`searches` is the quoted query strings in that reply's search section, joined with ` || `. An inch mark such as `11"` is not treated as a quote. `n_searches` counts those strings. `n_steps` counts numbered or bulleted actions in the same section. A reply that says it ran no new search has both counts at 0.

`price` is the first currency amount on the receipt line. A range keeps the lower figure in `price` and the upper in `price_high`. A figure marked "was" or a shipping add-on is not the price. `link_key` drops tracking parameters and, for Amazon and Target, keeps the ASIN or the A-id.

`brand_norm` folds obvious aliases (Soundcore by Anker and Anker Soundcore become Anker; A New Day (Target) becomes A New Day; T-fal becomes Tefal). Other brand strings are kept as written.

`stats.json` and `tables/` are produced by `code/analyze.py`. Cohort names:

| cohort | what it is |
|---|---|
| us-r1 | bot-us-1, 22 October, no perturbation. Five prompts in one chat, then the gift prompt later the same day. |
| us-r2 | bot-us-2, fresh, the six US prompts in reverse order. |
| tr-r1 | bot-tr-1, the six Turkey prompts in forward order. |
| tr-r2 | bot-tr-2, fresh, the six Turkey prompts in reverse order. The gift repeat is `np-tr__GI01-TR__r3`. |
| pref-tr | bot-tr-pref, the six Turkey prompts after a saved preference note. |
| round3-oct22 | the perturbation replies dated 22 October. |
| round3-oct28 | the perturbation replies dated 28 October, other than the location-default run. |
| location-default | `EL01-US-X3__r2fresh`. The prompt had no country. The reply priced in lira. |
| cached | `np-tr__GI01-TR__r2`, the same-chat repeat with no new search and no second receipt. |

Jaccard uses the set of `link_key`, `product_key`, or `brand_norm` values. A price is over a stated "under X" budget when it is greater than or equal to X.
