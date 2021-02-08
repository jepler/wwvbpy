#!/usr/bin/python3
#    WWVB timecode generator test harness
#    Copyright (C) 2011-2020 Jeff Epler <jepler@gmail.com.net>
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
import datetime
import unittest

import wwvbgen
import wwvbdec
import time
import glob
import os
import io


old_tz = None


# It's impotant that the tests run in this time zone because information about
# DST rules comes from it.
def setUpModule():
    global old_tz
    old_tz = os.environ.get("TZ")
    os.environ["TZ"] = ":America/Denver"  # Home of WWVB
    time.tzset()


def tearDownModule():
    if old_tz is None:
        del os.environ["TZ"]
    else:
        os.environ["TZ"] = old_tz
    time.tzset()


class WWVBTestCase(unittest.TestCase):
    maxDiff = 131072

    def test_cases(self):
        for test in glob.glob("tests/*"):
            with self.subTest(test=test):
                with open(test) as f:
                    text = f.read()
                lines = text.strip().split("\n")
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
                    else:
                        raise ValueError("Unknown option %r" % o)
                num_minutes = len(lines) - 1
                if channel == "both":
                    num_minutes = len(lines) // 3
                w = wwvbgen.WWVBMinute.fromstring(timestamp)
                result = io.StringIO()
                wwvbgen.print_timecodes(
                    w, num_minutes, channel=channel, style=style, file=result
                )
                result = result.getvalue()
                self.assertEqual(text, result)


class WWVBRoundtrip(unittest.TestCase):
    def test_decode(self):
        minute = wwvbgen.WWVBMinuteIERS.from_datetime(
            datetime.datetime(1992, 6, 30, 23, 50)
        )
        decoder = wwvbdec.wwvbreceive()
        next(decoder)
        decoder.send(wwvbgen.AmplitudeModulation.MARK)
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
            minute = wwvbgen.WWVBMinuteIERS.from_datetime(dt)
            timecode = minute.as_timecode().am
            decoded = (
                wwvbgen.WWVBMinuteIERS.from_timecode_am(minute.as_timecode())
                .as_timecode()
                .am
            )
            self.assertEqual(
                timecode,
                decoded,
                f"Checking equality of minute {minute}: [expected] {timecode} != [actual] {decoded}",
            )
            dt = dt + datetime.timedelta(minutes=915)


if __name__ == "__main__":
    unittest.main()
