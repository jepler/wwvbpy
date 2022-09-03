PYTHON ?= python3

.PHONY: default
default: coverage mypy

.PHONY: coverage
coverage:
	$(PYTHON) -mcoverage erase
	$(PYTHON) -mcoverage run --branch -p -m unittest discover -s src
	$(PYTHON) -mcoverage combine -q
	$(PYTHON) -mcoverage html
	$(PYTHON) -mcoverage xml
	$(PYTHON) -mcoverage report --fail-under=100

.PHONY: mypy
mypy:
	mypy --strict --no-warn-unused-ignores src

.PHONY: update
update:
	$(PYTHON) -mwwvb.updateiers --dist

# Copyright (C) 2021 Jeff Epler <jepler@gmail.com>
# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only
