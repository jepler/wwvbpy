PYTHON ?= python3

COVERAGE_INCLUDE=--omit '/usr/**/*.py'
.PHONY: coverage
coverage:
	$(PYTHON) -mcoverage run --branch -m unittest
	$(PYTHON) -mcoverage html $(COVERAGE_INCLUDE)
	$(PYTHON) -mcoverage annotate $(COVERAGE_INCLUDE)
	$(PYTHON) -mcoverage report $(COVERAGE_INCLUDE) --fail-under=100

.PHONY: mypy
mypy:
	mypy --strict uwwvb.py wwvb
# Copyright (C) 2021 Jeff Epler <jepler@gmail.com>
# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only
