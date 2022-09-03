#!/usr/bin/python3
"""Test of daylight saving time calculations"""

# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

import datetime
import unittest

import wwvb
from wwvb.tz import Mountain


class TestDaylight(unittest.TestCase):
    """Test of daylight saving time calculations"""

    def test_onset(self) -> None:
        """Test that the onset of DST is the same in Mountain and WWVBMinute (which uses ls bits)"""
        for h in [8, 9, 10]:
            for dm in range(-1441, 1442):
                d = datetime.datetime(
                    2021, 3, 14, h, 0, tzinfo=datetime.timezone.utc
                ) + datetime.timedelta(minutes=dm)
                m = wwvb.WWVBMinute.from_datetime(d)
                self.assertEqual(
                    m.as_datetime_local().replace(tzinfo=Mountain),
                    d.astimezone(Mountain),
                )

    def test_end(self) -> None:
        """Test that the end of DST is the same in Mountain and WWVBMinute (which uses ls bits)"""
        for h in [7, 8, 9]:
            for dm in range(-1441, 1442):
                d = datetime.datetime(
                    2021, 11, 7, h, 0, tzinfo=datetime.timezone.utc
                ) + datetime.timedelta(minutes=dm)
                m = wwvb.WWVBMinute.from_datetime(d)
                self.assertEqual(
                    m.as_datetime_local().replace(tzinfo=Mountain),
                    d.astimezone(Mountain),
                )

    def test_midsummer(self) -> None:
        """Test that middle of DST is the same in Mountain and WWVBMinute (which uses ls bits)"""
        for h in [7, 8, 9]:
            for dm in (-1, 0, 1):
                d = datetime.datetime(
                    2021, 7, 7, h, 0, tzinfo=datetime.timezone.utc
                ) + datetime.timedelta(minutes=dm)
                m = wwvb.WWVBMinute.from_datetime(d)
                self.assertEqual(
                    m.as_datetime_local().replace(tzinfo=Mountain),
                    d.astimezone(Mountain),
                )

    def test_midwinter(self) -> None:
        """Test that middle of standard time is the same in Mountain and WWVBMinute (which uses ls bits)"""
        for h in [7, 8, 9]:
            for dm in (-1, 0, 1):
                d = datetime.datetime(
                    2021, 12, 25, h, 0, tzinfo=datetime.timezone.utc
                ) + datetime.timedelta(minutes=dm)
                m = wwvb.WWVBMinute.from_datetime(d)
                self.assertEqual(
                    m.as_datetime_local().replace(tzinfo=Mountain),
                    d.astimezone(Mountain),
                )
