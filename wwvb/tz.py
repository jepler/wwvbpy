# -*- python -*-
"""A library for WWVB timecodes"""

# Copyright (C) 2011-2020 Jeff Epler <jepler@gmail.com>
# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

import datetime
import sys
from typing import Callable

ZoneInfo: Callable[[str], datetime.tzinfo]

if sys.version_info >= (3, 9):  # pragma no coverage
    from zoneinfo import ZoneInfo  # type: ignore
else:  # pragma no coverage
    from backports.zoneinfo import ZoneInfo  # type: ignore

Mountain = ZoneInfo("America/Denver")

__all__ = ["Mountain"]
