# -*- python3 -*-
"""Retrieve iers data, possibly from user or site data or from the wwvbpy distribution"""

# Copyright (C) 2021 Jeff Epler <jepler@gmail.com>
# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

import datetime
import os

import platformdirs

__all__ = ["DUT1_DATA_START", "DUT1_OFFSETS", "start", "span", "end"]
from .iersdata_dist import DUT1_DATA_START, DUT1_OFFSETS

for location in [
    platformdirs.user_data_dir("wwvbpy", "unpythonic.net"),
    platformdirs.site_data_dir("wwvbpy", "unpythonic.net"),
]:  # pragma no cover
    filename = os.path.join(location, "wwvbpy_iersdata.py")
    if os.path.exists(filename):
        with open(filename, encoding="utf-8") as f:
            exec(f.read(), globals(), globals())  # pylint: disable=exec-used
        break

start = datetime.datetime.combine(DUT1_DATA_START, datetime.time()).replace(
    tzinfo=datetime.timezone.utc
)
span = datetime.timedelta(days=len(DUT1_OFFSETS))
end = start + span
