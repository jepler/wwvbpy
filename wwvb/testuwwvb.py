#!/usr/bin/python3
"""Test of uwwvb.py"""
# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

import datetime
import random
import unittest

import wwvb
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
        minute = wwvb.WWVBMinuteIERS.from_datetime(
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
            minute = wwvb.WWVBMinuteIERS.from_datetime(dt)
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
            minute = wwvb.WWVBMinuteIERS.from_datetime(dt)
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
        minute = wwvb.WWVBMinuteIERS.from_datetime(
            datetime.datetime(2012, 6, 30, 23, 50)
        )
        r = random.Random(408)
        junk = [
            r.choice(
                [
                    wwvb.AmplitudeModulation.MARK,
                    wwvb.AmplitudeModulation.ONE,
                    wwvb.AmplitudeModulation.ZERO,
                ]
            )
            for _ in range(480)
        ]
        timecode = minute.as_timecode()
        test_input = junk + [wwvb.AmplitudeModulation.MARK] + timecode.am
        decoder = uwwvb.WWVBDecoder()
        for code in test_input[:-1]:
            decoded = decoder.update(code)
            self.assertIsNone(decoded)
        minute_maybe = decoder.update(wwvb.AmplitudeModulation.MARK)
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
        minute = wwvb.WWVBMinuteIERS.from_datetime(
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
        decoded = uwwvb.decode_wwvb(test_input)
        self.assertIsNone(decoded)

    def test_noise3(self):
        """Test impossible BCD values"""
        minute = wwvb.WWVBMinuteIERS.from_datetime(
            datetime.datetime(2012, 6, 30, 23, 50)
        )
        timecode = minute.as_timecode()

        for poslist in [
            [1, 2, 3, 4],  # tens minutes
            [5, 6, 7, 8],  # ones minutes
            [15, 16, 17, 18],  # tens hours
            [25, 26, 27, 28],  # tens days
            [30, 31, 32, 33],  # ones days
            [40, 41, 42, 43],  # tens years
            [45, 46, 47, 48],  # ones years
            [50, 51, 52, 53],  # ones dut1
        ]:
            with self.subTest(test=poslist):
                test_input = [int(i) for i in timecode.am]
                for pi in poslist:
                    test_input[pi] = 1
                decoded = uwwvb.decode_wwvb(test_input)
                self.assertIsNone(decoded)

    def test_str(self):
        """Test the str() of a WWVBDecoder"""
        self.assertEqual(str(uwwvb.WWVBDecoder()), "<WWVBDecoder 1 []>")

    def test_near_year_bug(self):
        """Chris's WWVB software had a bug where the hours after UTC
        midnight on 12-31 of a leap year would be shown incorrectly. Check that we
        don't have that bug."""
        minute = wwvb.WWVBMinuteIERS.from_datetime(datetime.datetime(2021, 1, 1, 0, 0))
        timecode = minute.as_timecode()
        decoded = uwwvb.decode_wwvb(timecode.am)
        self.assertDateTimeEqualExceptTzInfo(
            datetime.datetime(2020, 12, 31, 17, 00),  # Mountain time!
            uwwvb.as_datetime_local(decoded),
        )


if __name__ == "__main__":  # pragma no cover
    unittest.main()
