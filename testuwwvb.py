#!/usr/bin/python3

# Copyright (C) 2011-2020 Jeff Epler <jepler@gmail.com>
# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-or-later

import datetime
import random
import unittest

import wwvblib
import uwwvb
import glob
import os
import io
import sys


def decode_test_minute(data):
    return uwwvb.decode_wwvb(data)


class WWVBRoundtrip(unittest.TestCase):
    def test_decode(self):
        minute = wwvblib.WWVBMinuteIERS.from_datetime(
            datetime.datetime(2012, 6, 30, 23, 50)
        )
        decoder = uwwvb.WWVBDecoder()
        decoder.update(uwwvb.MARK)
        any_leap_second = False
        for i in range(20):
            timecode = minute.as_timecode()
            decoded = None
            if len(timecode.am) == 61:
                any_leap_second = True
            for code in timecode.am:
                decoded = uwwvb.decode_wwvb(decoder.update(int(code))) or decoded
            self.assertIsNotNone(decoded)
            self.assertEqual(
                minute.as_datetime_utc().replace(tzinfo=None),
                uwwvb.as_datetime_utc(*decoded),
            )
            minute = minute.next_minute()
        self.assertTrue(any_leap_second)

    def test_roundtrip(self):
        dt = datetime.datetime(2002, 1, 1, 0, 0)
        while dt.year < 2013:
            minute = wwvblib.WWVBMinuteIERS.from_datetime(dt)
            timecode = minute.as_timecode().am
            decoded = uwwvb.as_datetime_utc(*uwwvb.decode_wwvb(minute.as_timecode().am))
            self.assertEqual(
                minute.as_datetime_utc().replace(tzinfo=None),
                decoded,
            )
            dt = dt + datetime.timedelta(minutes=7182)

    def test_dst(self):
        for dt in (
            datetime.datetime(2021, 3, 14, 8, 59),
            datetime.datetime(2021, 3, 14, 9, 00),
            datetime.datetime(2021, 3, 14, 9, 1),
            datetime.datetime(2021, 11, 7, 8, 59),
            datetime.datetime(2021, 11, 7, 9, 00),
            datetime.datetime(2021, 11, 7, 9, 1),
            datetime.datetime(2021, 12, 7, 9, 1),
            datetime.datetime(2021, 7, 7, 9, 1),
        ):
            minute = wwvblib.WWVBMinuteIERS.from_datetime(dt)
            timecode = minute.as_timecode().am
            decoded = uwwvb.as_datetime_local(
                *uwwvb.decode_wwvb(minute.as_timecode().am)
            )
            self.assertEqual(
                minute.as_datetime_local().replace(tzinfo=None),
                decoded,
            )

            decoded = uwwvb.as_datetime_local(
                *uwwvb.decode_wwvb(minute.as_timecode().am),
                dst_observed=False,
            )
            self.assertEqual(
                minute.as_datetime_local(dst_observed=False).replace(tzinfo=None),
                decoded,
            )

    def test_noise(self):
        minute = wwvblib.WWVBMinuteIERS.from_datetime(
            datetime.datetime(2012, 6, 30, 23, 50)
        )
        r = random.Random(408)
        junk = [
            r.choice(
                [
                    wwvblib.AmplitudeModulation.MARK,
                    wwvblib.AmplitudeModulation.ONE,
                    wwvblib.AmplitudeModulation.ZERO,
                ]
            )
            for _ in range(480)
        ]
        timecode = minute.as_timecode()
        test_input = junk + [wwvblib.AmplitudeModulation.MARK] + timecode.am
        decoder = uwwvb.WWVBDecoder()
        for code in test_input[:-1]:
            decoded = decoder.update(code)
            self.assertIsNone(decoded)
        minute_maybe = decoder.update(wwvblib.AmplitudeModulation.MARK)
        self.assertIsNotNone(minute_maybe)
        decoded = uwwvb.decode_wwvb(minute_maybe)
        self.assertEqual(
            minute.as_datetime_utc().replace(tzinfo=None),
            uwwvb.as_datetime_utc(*decoded),
        )
        self.assertEqual(
            minute.as_datetime_local().replace(tzinfo=None),
            uwwvb.as_datetime_local(*decoded),
        )

    def test_noise2(self):
        minute = wwvblib.WWVBMinuteIERS.from_datetime(
            datetime.datetime(2012, 6, 30, 23, 50)
        )
        timecode = minute.as_timecode()
        decoded = decode_test_minute(timecode.am)
        self.assertIsNotNone(decoded)
        for position in uwwvb.always_mark:
            test_input = timecode.am[:]
            for noise in (0, 1):
                test_input[position] = noise
                decoded = decode_test_minute(test_input)
                self.assertIsNone(decoded)
        for position in uwwvb.always_zero:
            test_input = timecode.am[:]
            for noise in (1, 2):
                test_input[position] = noise
                decoded = decode_test_minute(test_input)
                self.assertIsNone(decoded)
        for i in range(8):
            if i == 0b101 or i == 0b010:
                continue
            test_input = timecode.am[:]
            test_input[36] = i & 1
            test_input[37] = (i >> 1) & 1
            test_input[38] = (i >> 2) & 1
            decoded = decode_test_minute(test_input)
            self.assertIsNone(decoded)
        # Invalid year-day
        test_input = timecode.am[:]
        test_input[22] = 1
        test_input[23] = 1
        test_input[25] = 1
        test_input[26] = 1
        test_input[27] = 1
        decoded = decode_test_minute(test_input)
        self.assertIsNone(decoded)


if __name__ == "__main__":  # pragma no cover
    unittest.main()
