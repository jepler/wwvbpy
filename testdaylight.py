#!/usr/bin/python3

# Copyright (C) 2011-2020 Jeff Epler <jepler@gmail.com>
# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-or-later

import datetime
import unittest
import wwvblib
from tzinfo_us import Mountain


class TestDaylight(unittest.TestCase):
    def test_onset(self):
        for h in [8, 9, 10]:
            for dm in (-1, 0, 1):
                d = datetime.datetime(
                    2021, 3, 14, h, 0, tzinfo=datetime.timezone.utc
                ) + datetime.timedelta(minutes=dm)
                m = wwvblib.WWVBMinute.from_datetime(d)
                self.assertEqual(
                    m.as_datetime_local().replace(tzinfo=Mountain),
                    d.astimezone(Mountain),
                )

    def test_end(self):
        for h in [7, 8, 9]:
            for dm in (-1, 0, 1):
                d = datetime.datetime(
                    2021, 11, 7, h, 0, tzinfo=datetime.timezone.utc
                ) + datetime.timedelta(minutes=dm)
                m = wwvblib.WWVBMinute.from_datetime(d)
                self.assertEqual(
                    m.as_datetime_local().replace(tzinfo=Mountain),
                    d.astimezone(Mountain),
                )

    def test_midsummer(self):
        for h in [7, 8, 9]:
            for dm in (-1, 0, 1):
                d = datetime.datetime(
                    2021, 7, 7, h, 0, tzinfo=datetime.timezone.utc
                ) + datetime.timedelta(minutes=dm)
                m = wwvblib.WWVBMinute.from_datetime(d)
                self.assertEqual(
                    m.as_datetime_local().replace(tzinfo=Mountain),
                    d.astimezone(Mountain),
                )

    def test_midwinter(self):
        for h in [7, 8, 9]:
            for dm in (-1, 0, 1):
                d = datetime.datetime(
                    2021, 12, 25, h, 0, tzinfo=datetime.timezone.utc
                ) + datetime.timedelta(minutes=dm)
                m = wwvblib.WWVBMinute.from_datetime(d)
                self.assertEqual(
                    m.as_datetime_local().replace(tzinfo=Mountain),
                    d.astimezone(Mountain),
                )
