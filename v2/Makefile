# Rebuild the v2 study from raw transcripts and the verification cache.
# `make` does not fetch the network. `make verify` does.

PYTHON ?= python3
export PYTHONPATH := src:../code

.PHONY: all test schedule normalize ingest baseline analyze figures report check verify

all: test schedule normalize ingest baseline analyze figures report check

test:
	$(PYTHON) -m pytest tests -q

schedule:
	$(PYTHON) -m grokstudy.cli schedule

normalize:
	$(PYTHON) -m grokstudy.cli normalize

ingest:
	$(PYTHON) -m grokstudy.cli ingest

baseline:
	$(PYTHON) -m grokstudy.cli baseline

analyze:
	$(PYTHON) -m grokstudy.cli analyze

figures:
	$(PYTHON) -m grokstudy.cli figures

report:
	$(PYTHON) -m grokstudy.cli report

check:
	$(PYTHON) -m grokstudy.cli check

verify:
	$(PYTHON) -m grokstudy.cli verify
