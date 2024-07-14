# -*- python -*-
"""A library for WWVB timecodes"""

# SPDX-FileCopyrightText: 2021-2024 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

from zoneinfo import ZoneInfo

Mountain = ZoneInfo("America/Denver")

__all__ = ["Mountain", "ZoneInfo"]
