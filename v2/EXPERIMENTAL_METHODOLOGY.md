# Experimental methodology

The October corpus is a retrospective reanalysis. It was not preregistered. The schedule in `v2/config/preregistration.yaml` is the preregistration for runs that have not been sent. Those runs are marked UNEXECUTED everywhere they are mentioned.

## Preregistration

Stimuli, the receipt suffix, the sample-size rule, and the hypotheses are in `v2/config/preregistration.yaml`. The scheduler may change order, time block, and date stratum. It may not change prompt text. Seed 20261028.

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
6. **Temporal change.** The catalog phrase appears in 3 replies, all dated 28 October, and in none dated 22 October. The 28 October prompts are also a different mix. Date and prompt are tied.
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
| Full | Primary | ±0.149 (target 0.15) | 43 |
| Full | Secondary | target 0.20 | 25 |
| Full | Probe | fixed, not powered for ±0.20 | 6 |
| MVE | Primary | target 0.25 | 16 |
| MVE | Secondary | target 0.35 | 8 |
| MVE | Probe | fixed | 2 |

A two-arm difference of 30 percentage points at p=0.5 versus p=0.8, 80% power, two-sided 5%, needs about 36 fresh bots per arm under the normal approximation. The full primary cell (43) covers that reference. Full secondary cells (25) are sized for a ±0.20 interval, not for that power target. Probe cells are exploratory. Figure: `figures/power-curve.png`.

These calculations assume independent fresh bots. They do not add another design effect. They do not use the October point estimates as the planning proportion, because those estimates are single-bot descriptions.

## Schedule

| Experiment | Full runs | MVE runs |
|---|---:|---:|
| E01 | 86 | 32 |
| E02 | 50 | 16 |
| E03 | 48 | 16 |
| E05 | 50 | 16 |
| E06 | 50 | 16 |
| E07 | 50 | 16 |
| E08 | 50 | 16 |
| E10 | 50 | 16 |
| Total | 434 | 144 |

E04 (US versus Turkey) and E09 (date and time block) add no prompts. E04 uses E01 and E03. E09 is a column on every row.

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
