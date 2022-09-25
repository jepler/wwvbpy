# -*- python -*-
"""A library for WWVB timecodes"""

# Copyright (C) 2011-2020 Jeff Epler <jepler@gmail.com>
# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

from zoneinfo import ZoneInfo

Mountain = ZoneInfo("America/Denver")

__all__ = ["Mountain", "ZoneInfo"]
