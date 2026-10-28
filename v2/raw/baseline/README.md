# Optional search-result lists

This directory is empty on purpose. The study did not call a search API and did not scrape a search page.

If you have a result list you are allowed to store, add one JSON file per quoted query. The file name is the sha256 of the query string. The shape is documented in `v2/src/grokstudy/baseline.py`. Until those files exist, the baseline comparison is UNEXECUTED.
