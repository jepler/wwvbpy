#!/usr/bin/python3
"""Leap seconds tests"""

# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

import datetime
import unittest
import wwvblib


class TestLeapSecond(unittest.TestCase):
    """Leap second tests"""

    def test_leap(self):
        """Tests that the expected leap seconds all occur."""
        d = datetime.datetime(1973, 1, 2, 0, 0)
        e = datetime.datetime(2020, 1, 1, 0, 0)
        leap = []
        while d < e:
            if wwvblib.isls(d):
                sense = wwvblib.get_dut1(d) > 0
                assert not sense
                leap.append(d.strftime("%b %Y"))
            m = d.utctimetuple().tm_mon
            while d.utctimetuple().tm_mon == m:
                d += datetime.timedelta(days=1)
        self.assertEqual(
            leap,
            [
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
                "Mar 2009",
                "Jun 2012",
                "Jun 2015",
                "Dec 2016",
            ],
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
