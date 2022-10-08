#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

"""Print the table of historical DUT1 values"""
from datetime import timedelta
from itertools import groupby

import wwvb

from .iersdata import DUT1_DATA_START, DUT1_OFFSETS


def main() -> None:
    """Print the table of historical DUT1 values"""
    date = DUT1_DATA_START
    for key, it in groupby(DUT1_OFFSETS):
        dut1_ms = (ord(key) - ord("k")) / 10.0
        count = len(list(it))
        end = date + timedelta(days=count - 1)
        dut1_next = wwvb.get_dut1(date + timedelta(days=count), warn_outdated=False)
        ls = f" LS on {end:%F} 23:59:60 UTC" if dut1_ms * dut1_next < 0 else ""
        print(f"{date:%F} {dut1_ms: 3.1f} {count:4d}{ls}")
        date += timedelta(days=count)
    print(date)


if __name__ == "__main__":  # pragma no branch
    main()
