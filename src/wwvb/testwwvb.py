#!/usr/bin/python3
"""Test most wwvblib functionality"""

# Copyright (C) 2011-2020 Jeff Epler <jepler@gmail.com>
# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

import copy
import datetime
import glob
import io
import random
import sys
import unittest
from typing import Optional

import uwwvb
import wwvb

from . import decode, iersdata, tz


class WWVBMinute2k(wwvb.WWVBMinute):
    """Treats the origin of the 2-digit epoch as 2000"""

    epoch = 2000


# pylint: disable=too-many-locals
class WWVBTestCase(unittest.TestCase):
    """Test each expected output in tests/.  Some outputs are from another program, some are from us"""

    maxDiff = 131072

    def test_cases(self) -> None:
        """Generate a test case for each expected output in tests/"""
        for test in glob.glob("tests/*"):
            with self.subTest(test=test):
                with open(test, "rt", encoding="utf-8") as f:
                    text = f.read()
                lines = [line for line in text.split("\n") if not line.startswith("#")]
                while not lines[0]:
                    del lines[0]
                text = "\n".join(lines)
                header = lines[0].split()
                timestamp = " ".join(header[:10])
                options = header[10:]
                channel = "amplitude"
                style = "default"
                for o in options:
                    if o.startswith("--channel="):
                        channel = o[10:]
                    elif o.startswith("--style="):
                        style = o[8:]
                    else:  # pragma: no cover
                        raise ValueError(f"Unknown option {repr(o)}")
                num_minutes = len(lines) - 2
                if channel == "both":
                    num_minutes = len(lines) // 3

                num_headers = sum(line.startswith("WWVB timecode") for line in lines)
                if num_headers > 1:
                    all_timecodes = True
                    num_minutes = num_headers
                else:
                    all_timecodes = False

                w = wwvb.WWVBMinute.fromstring(timestamp)
                result = io.StringIO()
                wwvb.print_timecodes(
                    w,
                    num_minutes,
                    channel=channel,
                    style=style,
                    all_timecodes=all_timecodes,
                    file=result,
                )
                result_str = result.getvalue()
                self.assertEqual(text, result_str)


class WWVBRoundtrip(unittest.TestCase):
    """Round-trip tests"""

    def test_decode(self) -> None:
        """Test that a range of minutes including a leap second are correctly decoded by the state-based decoder"""
        minute = wwvb.WWVBMinuteIERS.from_datetime(
            datetime.datetime(1992, 6, 30, 23, 50)
        )
        decoder = decode.wwvbreceive()
        next(decoder)
        decoder.send(wwvb.AmplitudeModulation.MARK)
        any_leap_second = False
        for _ in range(20):
            timecode = minute.as_timecode()
            decoded: Optional[wwvb.WWVBTimecode] = None
            if len(timecode.am) == 61:
                any_leap_second = True
            for code in timecode.am:
                decoded = decoder.send(code) or decoded
            assert decoded
            self.assertEqual(
                timecode.am[:60],
                decoded.am,
                f"Checking equality of minute {minute}: [expected] {timecode.am} != [actual] {decoded.am}",
            )
            minute = minute.next_minute()
        self.assertTrue(any_leap_second)

    def test_cover_fill_pm_timecode_extended(  # pylint: disable=no-self-use
        self,
    ) -> None:
        """Get full coverage of the function pm_timecode_extended"""
        for dt in (
            datetime.datetime(1992, 1, 1),
            datetime.datetime(1992, 4, 5),
            datetime.datetime(1992, 6, 1),
            datetime.datetime(1992, 10, 25),
        ):
            for hour in (0, 4, 11):
                dt = dt.replace(hour=hour, minute=10)
                minute = wwvb.WWVBMinuteIERS.from_datetime(dt)
                assert minute is not None
                timecode = minute.as_timecode().am
                assert timecode

    def test_roundtrip(self) -> None:
        """Test that a wide of minutes are correctly decoded by the state-based decoder"""
        dt = datetime.datetime(1992, 1, 1, 0, 0)
        delta = datetime.timedelta(
            minutes=915 if sys.implementation.name == "cpython" else 86400 - 915
        )
        while dt.year < 1993:
            minute = wwvb.WWVBMinuteIERS.from_datetime(dt)
            assert minute is not None
            timecode = minute.as_timecode().am
            assert timecode
            decoded_minute: Optional[
                wwvb.WWVBMinute
            ] = wwvb.WWVBMinuteIERS.from_timecode_am(minute.as_timecode())
            assert decoded_minute
            decoded = decoded_minute.as_timecode().am
            self.assertEqual(
                timecode,
                decoded,
                f"Checking equality of minute {minute}: [expected] {timecode} != [actual] {decoded}",
            )
            dt = dt + delta

    def test_noise(self) -> None:
        """Test against pseudorandom noise"""
        minute = wwvb.WWVBMinuteIERS.from_datetime(
            datetime.datetime(1992, 6, 30, 23, 50)
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
        decoder = decode.wwvbreceive()
        next(decoder)
        for code in test_input[:-1]:
            decoded = decoder.send(code)
            self.assertIsNone(decoded)
        decoded = decoder.send(wwvb.AmplitudeModulation.MARK)
        assert decoded
        self.assertIsNotNone(decoded)
        self.assertEqual(
            timecode.am[:60],
            decoded.am,
            f"Checking equality of minute {minute}: [expected] {timecode.am} != [actual] {decoded.am}",
        )

    def test_noise2(self) -> None:
        """Test of the full minute decoder with targeted errors to get full coverage"""
        minute = wwvb.WWVBMinuteIERS.from_datetime(
            datetime.datetime(2012, 6, 30, 23, 50)
        )
        timecode = minute.as_timecode()
        decoded = wwvb.WWVBMinute.from_timecode_am(timecode)
        self.assertIsNotNone(decoded)
        for position in uwwvb.always_mark:
            test_input = copy.deepcopy(timecode)
            for noise in (0, 1):
                test_input.am[position] = wwvb.AmplitudeModulation(noise)
                decoded = wwvb.WWVBMinute.from_timecode_am(test_input)
                self.assertIsNone(decoded)
        for position in uwwvb.always_zero:
            test_input = copy.deepcopy(timecode)
            for noise in (1, 2):
                test_input.am[position] = wwvb.AmplitudeModulation(noise)
                decoded = wwvb.WWVBMinute.from_timecode_am(test_input)
                self.assertIsNone(decoded)
        for i in range(8):
            if i in (0b101, 0b010):  # Test the 6 impossible bit-combos
                continue
            test_input = copy.deepcopy(timecode)
            test_input.am[36] = wwvb.AmplitudeModulation(i & 1)
            test_input.am[37] = wwvb.AmplitudeModulation((i >> 1) & 1)
            test_input.am[38] = wwvb.AmplitudeModulation((i >> 2) & 1)
            decoded = wwvb.WWVBMinute.from_timecode_am(test_input)
            self.assertIsNone(decoded)
        # Invalid year-day
        test_input = copy.deepcopy(timecode)
        test_input.am[22] = wwvb.AmplitudeModulation(1)
        test_input.am[23] = wwvb.AmplitudeModulation(1)
        test_input.am[25] = wwvb.AmplitudeModulation(1)
        decoded = wwvb.WWVBMinute.from_timecode_am(test_input)
        self.assertIsNone(decoded)

    def test_noise3(self) -> None:
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
                test_input = copy.deepcopy(timecode)
                for pi in poslist:
                    test_input.am[pi] = wwvb.AmplitudeModulation(1)
                decoded = wwvb.WWVBMinute.from_timecode_am(test_input)
                self.assertIsNone(decoded)

    def test_previous_next_minute(self) -> None:
        """Test that previous minute and next minute are inverses"""
        minute = wwvb.WWVBMinuteIERS.from_datetime(
            datetime.datetime(1992, 6, 30, 23, 50)
        )
        self.assertEqual(minute, minute.next_minute().previous_minute())

    def test_timecode_str(self) -> None:
        """Test the str() and repr() methods"""
        minute = wwvb.WWVBMinuteIERS.from_datetime(
            datetime.datetime(1992, 6, 30, 23, 50)
        )
        timecode = minute.as_timecode()
        self.assertEqual(
            str(timecode),
            "₂₁⁰¹⁰₀⁰⁰₀²₀₀₁₀₀⁰₀¹¹₂₀⁰⁰¹₀₁⁰⁰₀₂₀⁰₁⁰₀₀⁰₁⁰²⁰¹¹₀⁰¹₀⁰¹²⁰⁰¹₀₀¹₁₁₁₂",
        )
        timecode.phase = [wwvb.PhaseModulation.UNSET] * 60
        self.assertEqual(
            repr(timecode),
            "<WWVBTimecode 210100000200100001120001010002001000010201100100120010011112>",
        )

    def test_extreme_dut1(self) -> None:
        """Test extreme dut1 dates"""
        s = iersdata.DUT1_DATA_START
        sm1 = s - datetime.timedelta(days=1)
        self.assertEqual(wwvb.get_dut1(s), wwvb.get_dut1(sm1))

        e = iersdata.DUT1_DATA_START + datetime.timedelta(
            days=len(iersdata.DUT1_OFFSETS) - 1
        )
        ep1 = e + datetime.timedelta(days=1)

        self.assertEqual(wwvb.get_dut1(e), wwvb.get_dut1(ep1))

    def test_epoch(self) -> None:
        """Test the 1970-to-2069 epoch"""
        m = wwvb.WWVBMinute(69, 1, 1, 0, 0)
        n = wwvb.WWVBMinute(2069, 1, 1, 0, 0)
        self.assertEqual(m, n)

        m = wwvb.WWVBMinute(70, 1, 1, 0, 0)
        n = wwvb.WWVBMinute(1970, 1, 1, 0, 0)
        self.assertEqual(m, n)

    def test_fromstring(self) -> None:
        """Test the fromstring() classmethod"""

        s = "WWVB timecode: year=1998 days=365 hour=23 min=56 dst=0 ut1=-300 ly=0 ls=1"
        t = "year=1998 days=365 hour=23 min=56 dst=0 ut1=-300 ly=0 ls=1"
        self.assertEqual(
            wwvb.WWVBMinuteIERS.fromstring(s), wwvb.WWVBMinuteIERS.fromstring(t)
        )
        t = "year=1998 days=365 hour=23 min=56 dst=0 ut1=-300 ls=1"
        self.assertEqual(
            wwvb.WWVBMinuteIERS.fromstring(s), wwvb.WWVBMinuteIERS.fromstring(t)
        )
        t = "year=1998 days=365 hour=23 min=56 dst=0"
        self.assertEqual(
            wwvb.WWVBMinuteIERS.fromstring(s), wwvb.WWVBMinuteIERS.fromstring(t)
        )

    def test_from_datetime(self) -> None:
        """Test the from_datetime() classmethod"""
        d = datetime.datetime(1998, 12, 31, 23, 56, 0)
        self.assertEqual(
            wwvb.WWVBMinuteIERS.from_datetime(d),
            wwvb.WWVBMinuteIERS.from_datetime(d, newls=True, newut1=-300),
        )

    def test_exceptions(self) -> None:
        """Test some error detection"""
        with self.assertRaises(ValueError):
            wwvb.WWVBMinute(2021, 1, 1, 1, dst=4)

        with self.assertRaises(ValueError):
            wwvb.WWVBMinute(2021, 1, 1, 1, ut1=1)

        with self.assertRaises(ValueError):
            wwvb.WWVBMinute(2021, 1, 1, 1, ls=False)

        with self.assertRaises(ValueError):
            wwvb.WWVBMinute.fromstring(
                "year=1998 days=365 hour=23 min=56 dst=0 ut1=-300 ly=0 ls=1 boo=1"
            )

    def test_deprecated(self) -> None:
        """Ensure that the 'maybe_warn_update' function is covered"""
        with self.assertWarnsRegex(DeprecationWarning, "use ly"):
            wwvb.WWVBMinute(2020, 1, 1, 1).is_ly()

    def test_update(self) -> None:
        """Ensure that the 'maybe_warn_update' function is covered"""
        with self.assertWarnsRegex(Warning, "updateiers"):
            wwvb._maybe_warn_update(datetime.date(1970, 1, 1))

    def test_undefined(self) -> None:
        """Ensure that the check for unset elements in am works"""
        with self.assertWarnsRegex(Warning, "is unset"):
            str(wwvb.WWVBTimecode(60))

    def test_tz(self) -> None:
        """Get a little more coverage in the dst change functions"""
        date, row = wwvb.get_dst_change_date_and_row(datetime.datetime(1960, 1, 1))
        self.assertIsNone(date)
        self.assertIsNone(row)

        self.assertIsNone(wwvb.get_dst_change_hour(datetime.datetime(1960, 1, 1)))

        self.assertEqual(wwvb.get_dst_next(datetime.datetime(1960, 1, 1)), 0b000111)

        # Cuba followed year-round DST for several years
        self.assertEqual(
            wwvb.get_dst_next(datetime.datetime(2005, 1, 1), tz=tz.ZoneInfo("Cuba")),
            0b101111,
        )
        date, row = wwvb.get_dst_change_date_and_row(
            datetime.datetime(2005, 1, 1), tz=tz.ZoneInfo("Cuba")
        )
        self.assertIsNone(date)
        self.assertIsNone(row)

        # California was weird in 1948
        self.assertEqual(
            wwvb.get_dst_next(
                datetime.datetime(1948, 1, 1), tz=tz.ZoneInfo("America/Los_Angeles")
            ),
            0b100011,
        )

        # Berlin had DST changes on Monday in 1917
        self.assertEqual(
            wwvb.get_dst_next(
                datetime.datetime(1917, 1, 1), tz=tz.ZoneInfo("Europe/Berlin")
            ),
            0b100011,
        )

        #
        # Australia observes DST in the other half of the year compared to the
        # Northern hemisphere
        self.assertEqual(
            wwvb.get_dst_next(
                datetime.datetime(2005, 1, 1), tz=tz.ZoneInfo("Australia/Melbourne")
            ),
            0b100011,
        )

    def test_epoch2(self) -> None:
        """Test that the settable epoch feature works"""
        self.assertEqual(wwvb.WWVBMinute(0, 1, 1, 0, 0).year, 2000)
        self.assertEqual(wwvb.WWVBMinute(69, 1, 1, 0, 0).year, 2069)
        self.assertEqual(wwvb.WWVBMinute(70, 1, 1, 0, 0).year, 1970)
        self.assertEqual(wwvb.WWVBMinute(99, 1, 1, 0, 0).year, 1999)

        # 4-digit years can always be used
        self.assertEqual(wwvb.WWVBMinute(2000, 1, 1, 0, 0).year, 2000)
        self.assertEqual(wwvb.WWVBMinute(2069, 1, 1, 0, 0).year, 2069)
        self.assertEqual(wwvb.WWVBMinute(1970, 1, 1, 0, 0).year, 1970)
        self.assertEqual(wwvb.WWVBMinute(1999, 1, 1, 0, 0).year, 1999)

        self.assertEqual(wwvb.WWVBMinute(1900, 1, 1, 0, 0).year, 1900)
        self.assertEqual(wwvb.WWVBMinute(1969, 1, 1, 0, 0).year, 1969)
        self.assertEqual(wwvb.WWVBMinute(2070, 1, 1, 0, 0).year, 2070)
        self.assertEqual(wwvb.WWVBMinute(2099, 1, 1, 0, 0).year, 2099)

        self.assertEqual(WWVBMinute2k(0, 1, 1, 0, 0).year, 2000)
        self.assertEqual(WWVBMinute2k(99, 1, 1, 0, 0).year, 2099)

        # 4-digit years can always be used
        self.assertEqual(WWVBMinute2k(2000, 1, 1, 0, 0).year, 2000)
        self.assertEqual(WWVBMinute2k(2069, 1, 1, 0, 0).year, 2069)
        self.assertEqual(WWVBMinute2k(1970, 1, 1, 0, 0).year, 1970)
        self.assertEqual(WWVBMinute2k(1999, 1, 1, 0, 0).year, 1999)

        self.assertEqual(WWVBMinute2k(1900, 1, 1, 0, 0).year, 1900)
        self.assertEqual(WWVBMinute2k(1969, 1, 1, 0, 0).year, 1969)
        self.assertEqual(WWVBMinute2k(2070, 1, 1, 0, 0).year, 2070)
        self.assertEqual(WWVBMinute2k(2099, 1, 1, 0, 0).year, 2099)


if __name__ == "__main__":  # pragma no cover
    unittest.main()
