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
import unittest

import wwvbgen
import time
import glob
import os
import io

class WWVBTestCase(unittest.TestCase):
    maxDiff = 131072
    @classmethod
    def setUpClass(cls):
        cls._old_tz = os.environ.get('TZ')
        os.environ['TZ'] = ':America/Denver' # Home of WWVB
        time.tzset()

    @classmethod
    def tearDownClass(cls):
        if cls._old_tz is None:
            del os.environ['TZ']
        else:
            os.environ['TZ'] = cls._old_tz

    def test_cases(self):
        for test in glob.glob("tests/*"):
            with self.subTest(test=test):
                with open(test) as f:
                    text = f.read()
                lines = text.strip().split("\n")
                header = lines[0].split()
                timestamp = " ".join(header[:10])
                options = header[10:]
                channel = 'amplitude'
                style = 'default'
                for o in options:
                    if o.startswith('--channel='):
                        channel=o[10:]
                    elif o.startswith('--style='):
                        style=o[8:]
                    else:
                        raise ValueError("Unknown option %r" % o)
                num_minutes = len(lines)-1
                if channel == 'both':
                    num_minutes = len(lines) // 3
                w = wwvbgen.WWVBMinute.fromstring(timestamp)
                result = io.StringIO()
                wwvbgen.print_timecodes(w, num_minutes, channel=channel, style=style, file=result)
                result = result.getvalue()
                self.assertEqual(text, result)

if __name__ == '__main__':
    unittest.main()
