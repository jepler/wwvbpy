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
ifeq ($(OS),Windows_NT)
ENVPYTHON ?= _env/Scripts/python.exe
else
ENVPYTHON ?= _env/bin/python3
endif

.PHONY: default
default: coverage mypy

COVERAGE_INCLUDE=--include "src/**/*.py"
.PHONY: coverage
coverage:
	$(Q)$(PYTHON) -mcoverage erase
	$(Q)env PYTHONPATH=src $(PYTHON) -mcoverage run --branch -p -m unittest discover -s test
	$(Q)$(PYTHON) -mcoverage combine -q
	$(Q)$(PYTHON) -mcoverage html $(COVERAGE_INCLUDE)
	$(Q)$(PYTHON) -mcoverage xml $(COVERAGE_INCLUDE)
	$(Q)$(PYTHON) -mcoverage report --fail-under=100 $(COVERAGE_INCLUDE)

.PHONY: test_venv
test_venv:
	$(Q)$(PYTHON) -mvenv --clear _env
	$(Q)$(ENVPYTHON) -mpip install .
	$(Q)$(ENVPYTHON) -m unittest discover -s test

.PHONY: mypy
mypy:
	$(Q)mypy --strict --no-warn-unused-ignores src

.PHONY: update
update:
	$(Q)env PYTHONPATH=src $(PYTHON) -mwwvb.updateiers --dist

# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?= -a -E -j auto
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = doc
BUILDDIR      = _build

# Route particular targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
.PHONY: html
html:
	$(Q)$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# SPDX-FileCopyrightText: 2024 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only
