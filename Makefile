PYTHON ?= python3

.PHONY: default
default: coverage mypy

COVERAGE_INCLUDE=--omit '/usr/**/*.py'
.PHONY: coverage
coverage:
	$(PYTHON) -mcoverage erase
	$(PYTHON) -mcoverage run --branch -p -m unittest
	$(PYTHON) -mcoverage combine
	$(PYTHON) -mcoverage html $(COVERAGE_INCLUDE)
	$(PYTHON) -mcoverage xml $(COVERAGE_INCLUDE)
	$(PYTHON) -mcoverage report $(COVERAGE_INCLUDE) --fail-under=100

.PHONY: mypy
mypy:
	mypy --strict --no-warn-unused-ignores uwwvb.py wwvb

.PHONY: update
update:
	$(PYTHON) -mwwvb.updateiers --dist

# Copyright (C) 2021 Jeff Epler <jepler@gmail.com>
# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only
