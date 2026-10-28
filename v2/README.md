# Grok Bot shopping study, v2

Black-box reanalysis of the October 2026 corpus, plus a preregistered schedule for runs that have not been sent. v1 files under `evidence/`, `data/`, `figures/`, and `notes/` are not rewritten.

Receipt text is a bot self-report. It is not an execution trace. HTTP checks are independent observations. Public docs are cited by URL. Sample-size math and rank models are models, and the reports say so.

## Rebuild

Python 3.11 or newer.

```sh
python3 -m pip install -r v2/requirements.txt
make -C v2
```

`make` rebuilds the normalised tables, the figures, and the six reports from `evidence/transcripts/` and from `v2/raw/verification/`. It does not contact the network. From the repository root, `make` does the same thing.

`python3 code/check.py` still checks the v1 manifest. v2 is outside that manifest on purpose.

## Verify URLs

```sh
make -C v2 verify
```

This fetches each distinct product URL once. It sends an honest User-Agent, reads `robots.txt` first, and waits at least 1.5 seconds between requests to the same host. A disallow is recorded and the product URL is not fetched. If `robots.txt` cannot be read after one retry, one product fetch is attempted and marked `robots_unverified`. Raw bodies, capped and gzipped, are stored by sha256 under `v2/raw/verification/bodies/`. Set-Cookie headers are not stored.

## Run the new experiments

The schedules are `v2/normalized/schedule_full.csv` and `v2/normalized/schedule_mve.csv`. Counts and the precision targets are in `EXPERIMENTAL_METHODOLOGY.md`. Run the minimum-viable file first. Each row is one fresh bot.

1. Open a fresh Grok Bot chat. Do not continue an earlier chat.
2. If `setup_prompt` is non-empty, send that first. If the bot refuses to save the note, set `preference_outcome` to `refused` and do not send the shopping prompt.
3. Paste `prompt_text` exactly, including the receipt suffix. Do not buy anything and do not enter a card.
4. Save the reply as `v2/raw/replies/<run_id>.md`.
5. Append one row to `v2/raw/run_log.csv` with `sent_at`, `received_at`, `bot_slot`, and `market_cue`. The column list is in `v2/raw/RUNLOG.md`.

Then:

```sh
make -C v2
```

Until those replies exist, the reports mark every v2 experiment UNEXECUTED.

## Search baseline

No search API credential was available, and result pages were not scraped. To add a list you obtained within that source's terms, put JSON files in `v2/raw/baseline/` as described in `v2/src/grokstudy/baseline.py`, then run `make`.

## Tests

```sh
make -C v2 test
python3 -m pytest code/tests -q
python3 code/check.py
```
