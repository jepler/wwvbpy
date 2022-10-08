#!/usr/bin/python3
"""Leap seconds tests"""

# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

import datetime
import unittest

import leapseconddata

import wwvb

from . import iersdata

ONE_DAY = datetime.timedelta(days=1)


def next_month(d: datetime.date) -> datetime.date:
    """Return the start of the next month after the day 'd'"""
    d = d.replace(day=28)
    while True:
        d0 = d
        d = d + ONE_DAY
        if d.month != d0.month:
            return d


class TestLeapSecond(unittest.TestCase):
    """Leap second tests"""

    maxDiff = 9999

    def test_leap(self) -> None:
        """Tests that the expected leap seconds all occur."""
        ls = leapseconddata.LeapSecondData.from_standard_source()
        assert ls.valid_until is not None

        d = iersdata.start
        e = min(iersdata.end, ls.valid_until)
        bench = [ts.start for ts in ls.leap_seconds[1:]]
        bench = [ts for ts in bench if d <= ts < e]
        leap = []
        while d < e:
            nm = next_month(d)
            eom = nm - ONE_DAY
            month_ends_dut1 = wwvb.get_dut1(eom)
            month_starts_dut1 = wwvb.get_dut1(nm)
            our_is_ls = month_ends_dut1 * month_starts_dut1 < 0
            if wwvb.isls(eom):
                assert our_is_ls
                self.assertLess(month_ends_dut1, 0)
                self.assertGreater(month_starts_dut1, 0)
                leap.append(nm)
            else:
                assert not our_is_ls
            d = datetime.datetime.combine(nm, datetime.time()).replace(
                tzinfo=datetime.timezone.utc
            )
        self.assertEqual(leap, bench)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
