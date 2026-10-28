# Facts checked

Numeric claims in the article are the fields in `data/stats.json`, rebuilt from `evidence/transcripts/` by `code/analyze.py`. This list is the claim, then where to look. If this file and the article disagree, the article plus `stats.json` are the ones to recompute.

| Claim | Where |
|---|---|
| 49 shopping replies, 228 shown products, 54 files | `stats.json` `shopping_runs`, `shopping_product_rows`, `files` |
| Pilot five: 20 products, HHI 0.08, top brand 0.15, top three 0.35, Target 13, Best Buy 7 | `stats.json` `pilot_five` |
| US first pass, six replies: 23 products, all retailer, Target 16, Best Buy 7, HHI 0.074, 8 generic queries, 6/6 one domain | `cohorts.us-r1` |
| US fresh repeat: 28 products, 18 brand-own, 9 marketplace, 1 retailer, 47 queries of which 24 editorial, 6/6 first query editorial, mean 19.5 steps, 0/6 one domain | `cohorts.us-r2` |
| Turkey first pass: 38 products, marketplace 0.763, Amazon.com.tr 25, Trendyol 4 | `cohorts.tr-r1` |
| Turkey fresh repeat: 31 products, marketplace 0.903, Trendyol 21, Amazon.com.tr 6 | `cohorts.tr-r2` |
| 84 of 122 Turkey no-preference queries name a brand or a model | `tr-r1.query_class` plus `tr-r2.query_class` (brand 26+48, model 2+8, total queries 49+73) |
| Fresh-repeat link means 0 (US) and 0.054 (TR); brand means 0.157 and 0.378 | `repeat_link_mean`, `repeat_brand_mean`, and `tables/stability.csv` |
| US EL02 shares the WH-CH720N product key and no URL | `stability` row EL02 US; keys from `records.csv` |
| TR EL02 link 0.125, product 0.50; shared Space One URL and model codes A3028, A3004, A3035 | `stability` row EL02 TR |
| Preference link mean 0.015, brand mean 0.394; 13 brand-own, 10 cimri.com | `preference_link_mean`, `preference_brand_mean`, `cohorts.pref-tr` |
| Budget and store rows in the article | `tables/budgets.csv`, `stats.json` `perturbations` |
| Sony Turkey: 0 of 2 under 5,000 TL, both Sony, prose says none found | `EL02-TR-X2__r1` and its budget row |
| Tefal 6/6; Getir 6/6; Best Buy 4/4; Trendyol-only 5/5 | perturbation `brand_rule` and `store` objects |
| 4 of 5 minimal-wording US dresses are A New Day | `records.csv` rows for `FA01-US-X3__r1` |
| Transparency scan counts | `stats.json` `transparency` |
| 3 catalog replies, all 28 October | `catalog_runs` |
| Location-default reply is TRY, MediaMarkt and Teknosa | `cohorts.location-default` and `EL01-US-X3__r2fresh.md` |
| Checkout phrases (95829, greyed out, sponsored ad, Cart (0 items), guest cart, didn't sign in) | `stats.json` `checkout` and the two checkout files |
| US preference series not run | `profile-setup-notes.md`; no `pref-us__` shopping file |
| Same-chat gift repeat has no receipt | `np-tr__GI01-TR__r2.md` |

Quotes in the article are copied in `transcript/EXCERPTS.md` with the source path. They were checked against those files on 28 October 2026.

Not checked, and not claimed: any store's own ranking, any HTTP status beyond the bot's words, and whether the catalog path still exists after 28 October.
