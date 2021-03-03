#!/usr/bin/python3
"""Test of uwwvb.py"""
# Copyright (C) 2011-2020 Jeff Epler <jepler@gmail.com>
# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-or-later

import datetime
import random
import unittest

import wwvblib
import uwwvb


class WWVBRoundtrip(unittest.TestCase):
    """tests of uwwvb.py"""

    def assertDateTimeEqualExceptTzInfo(self, a, b):  # pylint: disable=invalid-name
        """Test two datetime objects for equality, excluding tzinfo, and allowing adafruit_datetime and core datetime modules to compare equal"""
        self.assertEqual(
            (a.year, a.month, a.day, a.hour, a.minute, a.second, a.microsecond),
            (b.year, b.month, b.day, b.hour, b.minute, b.second, b.microsecond),
        )

    def test_decode(self):
        """Test decoding of some minutes including a leap second.
        Each minute must decode and match the primary decoder."""
        minute = wwvblib.WWVBMinuteIERS.from_datetime(
            datetime.datetime(2012, 6, 30, 23, 50)
        )
        decoder = uwwvb.WWVBDecoder()
        decoder.update(uwwvb.MARK)
        any_leap_second = False
        for _ in range(20):
            timecode = minute.as_timecode()
            decoded = None
            if len(timecode.am) == 61:
                any_leap_second = True
            for code in timecode.am:
                decoded = uwwvb.decode_wwvb(decoder.update(int(code))) or decoded
            self.assertIsNotNone(decoded)
            self.assertDateTimeEqualExceptTzInfo(
                minute.as_datetime_utc(),
                uwwvb.as_datetime_utc(decoded),
            )
            minute = minute.next_minute()
        self.assertTrue(any_leap_second)

    def test_roundtrip(self):
        """Test that some big range of times all decode the same as the primary decoder"""
        dt = datetime.datetime(2002, 1, 1, 0, 0)
        while dt.year < 2013:
            minute = wwvblib.WWVBMinuteIERS.from_datetime(dt)
            decoded = uwwvb.as_datetime_utc(uwwvb.decode_wwvb(minute.as_timecode().am))
            self.assertDateTimeEqualExceptTzInfo(
                minute.as_datetime_utc(),
                decoded,
            )
            dt = dt + datetime.timedelta(minutes=7182)

    def test_dst(self):
        """Test of DST as handled by the small decoder"""
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
            decoded = uwwvb.as_datetime_local(
                uwwvb.decode_wwvb(minute.as_timecode().am)
            )
            self.assertDateTimeEqualExceptTzInfo(
                minute.as_datetime_local(),
                decoded,
            )

            decoded = uwwvb.as_datetime_local(
                uwwvb.decode_wwvb(minute.as_timecode().am),
                dst_observed=False,
            )
            self.assertDateTimeEqualExceptTzInfo(
                minute.as_datetime_local(dst_observed=False),
                decoded,
            )

    def test_noise(self):
        """Test of the state-machine decoder when faced with pseudorandom noise"""
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
        self.assertDateTimeEqualExceptTzInfo(
            minute.as_datetime_utc(),
            uwwvb.as_datetime_utc(decoded),
        )
        self.assertDateTimeEqualExceptTzInfo(
            minute.as_datetime_local(),
            uwwvb.as_datetime_local(decoded),
        )

    def test_noise2(self):
        """Test of the full minute decoder with targeted errors to get full coverage"""
        minute = wwvblib.WWVBMinuteIERS.from_datetime(
            datetime.datetime(2012, 6, 30, 23, 50)
        )
        timecode = minute.as_timecode()
        decoded = uwwvb.decode_wwvb(timecode.am)
        self.assertIsNotNone(decoded)
        for position in uwwvb.always_mark:
            test_input = timecode.am[:]
            for noise in (0, 1):
                test_input[position] = noise
                decoded = uwwvb.decode_wwvb(test_input)
                self.assertIsNone(decoded)
        for position in uwwvb.always_zero:
            test_input = timecode.am[:]
            for noise in (1, 2):
                test_input[position] = noise
                decoded = uwwvb.decode_wwvb(test_input)
                self.assertIsNone(decoded)
        for i in range(8):
            if i in (0b101, 0b010):  # Test the 6 impossible bit-combos
                continue
            test_input = timecode.am[:]
            test_input[36] = i & 1
            test_input[37] = (i >> 1) & 1
            test_input[38] = (i >> 2) & 1
            decoded = uwwvb.decode_wwvb(test_input)
            self.assertIsNone(decoded)
        # Invalid year-day
        test_input = timecode.am[:]
        test_input[22] = 1
        test_input[23] = 1
        test_input[25] = 1
        test_input[26] = 1
        test_input[27] = 1
        decoded = uwwvb.decode_wwvb(test_input)
        self.assertIsNone(decoded)

    def test_str(self):
        """Test the str() of a WWVBDecoder"""
        self.assertEqual(str(uwwvb.WWVBDecoder()), "<WWVBDecoder 1 []>")


if __name__ == "__main__":  # pragma no cover
    unittest.main()
