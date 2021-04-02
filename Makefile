.PHONY: coverage
coverage:
	python3 -mcoverage run --branch -m unittest
	python3 -mcoverage html
	python3 -mcoverage annotate
	python3 -mcoverage report --fail-under=100

# Copyright (C) 2021 Jeff Epler <jepler@gmail.com>
# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only
