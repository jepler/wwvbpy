#!/usr/bin/python3
"""Leap seconds tests"""

# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

import datetime
import unittest
import wwvb

from . import iersdata

ONE_DAY = datetime.timedelta(days=1)


def end_of_month(d):
    """Return the end of the month containing the day 'd'"""
    while True:
        d0 = d
        d = d + ONE_DAY
        if d.month != d0.month:
            return d0


def next_month(d):
    """Return the first day of hte next month after 'd'"""
    while True:
        d0 = d
        d = d + ONE_DAY
        if d.month != d0.month:
            return d


class TestLeapSecond(unittest.TestCase):
    """Leap second tests"""

    def test_leap(self):
        """Tests that the expected leap seconds all occur."""
        d = iersdata.DUT1_DATA_START
        e = datetime.date(2022, 1, 1)
        leap = []
        while d < e:
            eom = end_of_month(d)
            nm = next_month(d)
            if wwvb.isls(d):
                month_ends_dut1 = wwvb.get_dut1(eom)
                month_starts_dut1 = wwvb.get_dut1(nm)
                self.assertLess(month_ends_dut1, 0)
                self.assertGreater(month_starts_dut1, 0)
                leap.append(d.strftime("%b %Y"))
            d = nm
        self.assertEqual(
            leap,
            [
                "Jun 1972",
                "Dec 1973",
                "Dec 1974",
                "Dec 1975",
                "Dec 1976",
                "Dec 1977",
                "Dec 1978",
                "Dec 1979",
                "Jun 1981",
                "Jun 1982",
                "Jun 1983",
                "Jun 1985",
                "Dec 1987",
                "Dec 1989",
                "Dec 1990",
                "Jun 1992",
                "Jun 1993",
                "Jun 1994",
                "Dec 1995",
                "Jun 1997",
                "Dec 1998",
                "Dec 2005",
                "Dec 2008",
                "Jun 2012",
                "Jun 2015",
                "Dec 2016",
            ],
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
