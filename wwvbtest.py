#!/usr/bin/python
#    WWVB timecode generator
#    Copyright (C) 2011 Jeff Epler <jepler@unpythonic.net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
import wwvbgen
import time
import glob
import os
import StringIO

def dotestcase(testname):
    inf = "tests/%s" % testname
    text = open(inf).read()
    lines = text.strip().split("\n")
    w = wwvbgen.WWVBMinute.fromstring(lines[0])
    result = StringIO.StringIO()
    print >>result, "WWVB timecode: %s" % str(w)
    for i in range(1, len(lines)):
        print >>result, "'%02d+%03d %02d:%02d  %s" % (
            w.year % 100, w.days, w.hour, w.min, w.as_timecode())
        w = w.next_minute()
    result = result.getvalue()
    if result != text:
        outf = "out/%s" % testname
        open(outf, "w").write(result)
        print "vimdiff %s %s" % (inf, outf)
        return False
    else:
        return True

if __name__ == '__main__':
    import os
    import glob
    os.environ['TZ'] = ':America/Denver' # Home of WWVB
    time.tzset()
    total = success = 0
    for test in glob.glob("tests/*"):
        total += 1
        success += dotestcase(os.path.basename(test))
    print "%d success (%d failures) out of %d tests" % (success, total-success, total)
#    w = WWVBMinute(2000, 366, 23, 58)
#    print "WWVB timecode:", w
#    for i in range(4):
#        print "'%02d+%03d %02d:%02d  %s" % (
#            w.year % 100, w.days, w.hour, w.min, w.as_timecode())
##        w = w.next_minute()
