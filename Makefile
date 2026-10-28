# v1 stays reproducible via code/check.py. This target rebuilds the v2 study.
.PHONY: all test v1-check
all:
	$(MAKE) -C v2 all

test:
	$(MAKE) -C v2 test
	python3 -m pytest code/tests -q

v1-check:
	python3 code/check.py
