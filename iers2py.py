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
import datetime
import itertools

data = open("iers-data.html").read()
mark1 = '<pre><font size=3>'
mark2 = '</font></pre>'
mark3 = '<br>'
data = data.split(mark1, 1)[1]
data = data.split(mark2, 1)[0]
rows = data.split(mark3)
offsets = []
print "# File generated from public data - not subject to copyright"
print "import datetime"
for i, r in enumerate(rows):
    if not r: continue
    jd = float(r[26:34])
    if i == 0:
        start = datetime.datetime(1858,11,17) + datetime.timedelta(jd)
    offs = int(round(float(r[45:55])*10))
    offsets.append(offs)
print "__all__ = ['dut1_data_start, dut1_offsets']"
print "dut1_data_start = %r" % start
c = sorted(chr(ord('a') + ch + 10) for ch in set(offsets))
print "%s = '%s'" % (",".join(c), "".join(c))
print "dut1_offsets = ( # %02d%02d%02d" % (start.year%100,start.month,start.day)
line = ''
now = start
j = 0

for ch, it in itertools.groupby(offsets):
    part = ""
    ch = chr(ord('a') + ch + 10)
    sz = len(list(it))
    if j: part = part + "+"
    if sz < 4:
        part = part + "%s" % (ch * sz)
    else:
        part = part + "%s*%d" % (ch, sz)
    j += sz
    if len(line + part) > 60:
        d = start + datetime.timedelta(j-1)
        print "    %-60s # %02d%02d%02d" % (line, d.year%100, d.month, d.day)
        line = part
    else:
        line = line + part
d = start + datetime.timedelta(j-1)
print "    %-60s # %02d%02d%02d" % (line, d.year%100, d.month, d.day)
print ")"
