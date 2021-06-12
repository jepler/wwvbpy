#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

"""Print the table of historical DUT1 values"""
from datetime import timedelta
from itertools import groupby
from .iersdata import DUT1_DATA_START, DUT1_OFFSETS


def main():
    """Print the table of historical DUT1 values"""
    date = DUT1_DATA_START.date()
    for key, it in groupby(DUT1_OFFSETS):
        dut1_ms = (ord(key) - ord("k")) / 10.0
        count = len(list(it))
        print("%10s % 3.1f %4d" % (date, dut1_ms, count))
        date += timedelta(days=count)
    print(date)


if __name__ == "__main__":
    main()
