# Operator run log

Append one row per scheduled run to `v2/raw/run_log.csv`. Do not invent timestamps. A run that was not sent is absent from this file, not filled with a guessed time.

| Column | Meaning |
|---|---|
| run_id | From the schedule. The reply file is `replies/<run_id>.md`. |
| experiment_id | E01–E10, excluding the analysis-only ids. |
| bot_slot | The schedule's `FRESH-US-001` label. A new bot for every row. |
| market | US or TR, as assigned. |
| market_cue | Copy from the schedule. This is the cue in the prompt, not a private location. |
| sent_at | ISO 8601 time the shopping prompt was sent. |
| received_at | ISO 8601 time the reply finished. |
| wording_variant | A or B, from the schedule. |
| time_block | The assigned block. If you missed it, write the block you actually used in `operator_notes` and keep the assigned value here. |
| date_stratum | D1, D2, or D3 for E01. Empty otherwise. |
| preference_outcome | `saved`, `refused`, or empty when the run has no setup prompt. |
| operator_notes | Short. No city, phone, email, or bot UUID. |

`sent_at` and `received_at` are the operator's clock. The bot's own words stay in the reply file.
