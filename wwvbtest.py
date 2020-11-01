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
import wwvbgen
import time
import glob
import os
import io

def dotestcase(testname):
    inf = "tests/%s" % testname
    with open(inf) as f:
        text = f.read()
    lines = text.strip().split("\n")
    w = wwvbgen.WWVBMinute.fromstring(lines[0])
    result = io.StringIO()
    print("WWVB timecode: %s" % str(w), file=result)
    for i in range(1, len(lines)):
        tc = w.as_timecode()
        print("'%02d+%03d %02d:%02d  %s" % (
            w.year % 100, w.days, w.hour, w.min, w.as_timecode().to_am_string("012")), file=result)
        w = w.next_minute()
    result = result.getvalue()
    if result != text:
        outf = "out/%s" % testname
        open(outf, "w").write(result)
        print("vimdiff %s %s" % (inf, outf))
        return False
    else:
        return True

if __name__ == '__main__':
    import os
    import glob
    os.environ['TZ'] = ':America/Denver' # Home of WWVB
    time.tzset()
    total = success = 0
    if not os.path.isdir("out"):
        os.mkdir("out")
    for test in glob.glob("tests/*"):
        total += 1
        success += dotestcase(os.path.basename(test))
    print("%d success (%d failures) out of %d tests" % (success, total-success, total))
    if success != total:
        raise SystemExit(1)
#    w = WWVBMinute(2000, 366, 23, 58)
#    print "WWVB timecode:", w
#    for i in range(4):
#        print "'%02d+%03d %02d:%02d  %s" % (
#            w.year % 100, w.days, w.hour, w.min, w.as_timecode())
##        w = w.next_minute()
