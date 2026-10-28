"""Filesystem locations for the v2 study. v1 files are read and never written."""
from __future__ import annotations

from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
V2 = PACKAGE.parents[1]
REPO = PACKAGE.parents[2]

CONFIG = V2 / "config"
PREREG = CONFIG / "preregistration.yaml"
PUBLIC_DOCS = CONFIG / "public_docs.yaml"

RAW = V2 / "raw"
REPLIES = RAW / "replies"
RUN_LOG = RAW / "run_log.csv"
VERIFICATION = RAW / "verification"
VERIFICATION_BODIES = VERIFICATION / "bodies"
VERIFICATION_INDEX = VERIFICATION / "index.jsonl"
BASELINE_DIR = RAW / "baseline"

NORMALIZED = V2 / "normalized"
FIGURES = V2 / "figures"

V1_TRANSCRIPTS = REPO / "evidence" / "transcripts"
V1_RECORDS = REPO / "data" / "records.csv"
V1_STATS = REPO / "data" / "stats.json"
V1_CODE = REPO / "code"
