ifeq ("$(origin V)", "command line")
BUILD_VERBOSE=$(V)
endif
ifndef BUILD_VERBOSE
$(info Use make V=1, make V=2 or set BUILD_VERBOSE similarly in your environment to increase build verbosity.)
BUILD_VERBOSE = 0
endif
ifeq ($(BUILD_VERBOSE),0)
Q = @
STEPECHO = @:
else ifeq ($(BUILD_VERBOSE),1)
Q = @
STEPECHO = @echo
else
Q =
STEPECHO = @echo
endif

PYTHON ?= python3

.PHONY: default
default: coverage mypy

.PHONY: coverage
coverage:
	$(Q)$(PYTHON) -mcoverage erase
	$(Q)env PYTHONPATH=src $(PYTHON) -mcoverage run --branch -p -m unittest discover -s src
	$(Q)$(PYTHON) -mcoverage combine -q
	$(Q)$(PYTHON) -mcoverage html
	$(Q)$(PYTHON) -mcoverage xml
	$(Q)$(PYTHON) -mcoverage report --fail-under=100

.PHONY: mypy
mypy:
	$(Q)mypy --strict --no-warn-unused-ignores src

.PHONY: update
update:
	$(Q)env PYTHONPATH=src $(PYTHON) -mwwvb.updateiers --dist

# Copyright (C) 2021 Jeff Epler <jepler@gmail.com>
# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only
