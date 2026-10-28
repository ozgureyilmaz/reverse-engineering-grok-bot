# Independent URL fetches

`index.jsonl` is one JSON object per product URL. `bodies/` holds gzipped response prefixes named by the sha256 of the bytes that were read. These files are observations of public pages. They are not the bot's receipt.

A row with `fetch_status` `skipped_robots` was not fetched. A row with `robots_status` `robots_unverified` means `robots.txt` could not be read after a retry and one fetch was still attempted; that distinction is part of the result.
