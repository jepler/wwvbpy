#!/usr/bin/python3

# Copyright (C) 2011-2020 Jeff Epler <jepler@gmail.com>
# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-or-later

import datetime
import random
import unittest

import wwvblib
import wwvbdec
import glob
import os
import io


class WWVBTestCase(unittest.TestCase):
    maxDiff = 131072

    def test_cases(self):
        for test in glob.glob("tests/*"):
            with self.subTest(test=test):
                with open(test) as f:
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
                        raise ValueError("Unknown option %r" % o)
                num_minutes = len(lines) - 2
                if channel == "both":
                    num_minutes = len(lines) // 3
                w = wwvblib.WWVBMinute.fromstring(timestamp)
                result = io.StringIO()
                wwvblib.print_timecodes(
                    w, num_minutes, channel=channel, style=style, file=result
                )
                result = result.getvalue()
                self.assertEqual(text, result)


class WWVBRoundtrip(unittest.TestCase):
    def test_decode(self):
        minute = wwvblib.WWVBMinuteIERS.from_datetime(
            datetime.datetime(1992, 6, 30, 23, 50)
        )
        decoder = wwvbdec.wwvbreceive()
        next(decoder)
        decoder.send(wwvblib.AmplitudeModulation.MARK)
        any_leap_second = False
        for i in range(20):
            timecode = minute.as_timecode()
            decoded = None
            if len(timecode.am) == 61:
                any_leap_second = True
            for code in timecode.am:
                decoded = decoder.send(code) or decoded
            self.assertEqual(
                timecode.am[:60],
                decoded.am,
                f"Checking equality of minute {minute}: [expected] {timecode.am} != [actual] {decoded.am}",
            )
            minute = minute.next_minute()
        self.assertTrue(any_leap_second)

    def test_roundtrip(self):
        dt = datetime.datetime(1992, 1, 1, 0, 0)
        while dt.year < 1993:
            minute = wwvblib.WWVBMinuteIERS.from_datetime(dt)
            timecode = minute.as_timecode().am
            decoded = (
                wwvblib.WWVBMinuteIERS.from_timecode_am(minute.as_timecode())
                .as_timecode()
                .am
            )
            self.assertEqual(
                timecode,
                decoded,
                f"Checking equality of minute {minute}: [expected] {timecode} != [actual] {decoded}",
            )
            dt = dt + datetime.timedelta(minutes=915)

    def test_noise(self):
        minute = wwvblib.WWVBMinuteIERS.from_datetime(
            datetime.datetime(1992, 6, 30, 23, 50)
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
        decoder = wwvbdec.wwvbreceive()
        next(decoder)
        for code in test_input[:-1]:
            decoded = decoder.send(code)
            self.assertIsNone(decoded)
        decoded = decoder.send(wwvblib.AmplitudeModulation.MARK)
        self.assertIsNotNone(decoded)
        self.assertEqual(
            timecode.am[:60],
            decoded.am,
            f"Checking equality of minute {minute}: [expected] {timecode.am} != [actual] {decoded.am}",
        )

    def test_previous_next_minute(self):
        minute = wwvblib.WWVBMinuteIERS.from_datetime(
            datetime.datetime(1992, 6, 30, 23, 50)
        )
        self.assertEqual(minute, minute.next_minute().previous_minute())

    def test_data_next_minute(self):
        minute = wwvblib.WWVBMinuteIERS.from_datetime(
            datetime.datetime(1992, 6, 30, 23, 50)
        )
        self.assertEqual(minute.as_timecode().data, minute.as_timecode().am)

    def test_timecode_str(self):
        minute = wwvblib.WWVBMinuteIERS.from_datetime(
            datetime.datetime(1992, 6, 30, 23, 50)
        )
        timecode = minute.as_timecode()
        self.assertEqual(
            str(timecode),
            "₂₁⁰¹⁰₀⁰⁰₀²₀₀₁₀₀⁰₀¹¹₂₀⁰⁰¹₀₁⁰⁰₀₂₀⁰₁⁰₀₀⁰₁⁰²⁰¹¹₀⁰¹₀⁰¹²⁰⁰¹₀₀¹₁₁₁₂",
        )
        timecode.phase = [wwvblib.PhaseModulation.UNSET] * 60
        self.assertEqual(
            repr(timecode),
            "<WWVBTimecode 210100000200100001120001010002001000010201100100120010011112>",
        )


if __name__ == "__main__":  # pragma no cover
    unittest.main()
