#!/usr/bin/python3
#    Print leap seconds according to iers data
#    Copyright (C) 2012-2020 Jeff Epler <jepler@gmail.com.net>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
import wwvbgen
import datetime
import iersdata
import unittest


class TestLeapSecond(unittest.TestCase):
    def test_leap(self):
        d = datetime.datetime(1973, 1, 2, 0, 0)
        e = datetime.datetime(2020, 1, 1, 0, 0)
        leap = []
        while d < e:
            if wwvbgen.isls(d):
                sense = wwvbgen.get_dut1(d) > 0
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


if __name__ == "__main__":
    unittest.main()
