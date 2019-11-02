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
import bs4

with open("iers-data.txt") as f:
    rows = f.readlines()

with open("wwvb-data.html") as f:
    wwvb_data = bs4.BeautifulSoup(f, features='lxml')
wwvb_dut1_table = wwvb_data.findAll('table')[2]

offsets = []
print "# File generated from public data - not subject to copyright"
print "import datetime"
for i, r in enumerate(rows):
    if len(r) < 69: continue
    if r[57] not in 'IP': continue
    jd = float(r[7:12])
    offs = int(round(float(r[58:68])*10))
    if not offsets:
        start = datetime.datetime(1858,11,17) + datetime.timedelta(jd)
    offsets.append(offs)

wwvb_dut1 = None
wwvb_off = None
for row in wwvb_dut1_table.findAll('tr')[1:][::-1]:
    cells = row.findAll('td')    
    when = datetime.datetime.strptime(cells[0].text, '%Y-%m-%d')
    dut1 = cells[2].text.replace('s', '').replace(' ', '')
    dut1 = int(round(float(dut1) * 10))
    off = (when - start).days
    if wwvb_dut1 is not None:
        offsets[wwvb_off:off] = [wwvb_dut1] * (off - wwvb_off)
    wwvb_dut1 = dut1
    wwvb_off = off


# this is the final (most recent) wwvb DUT1 value broadcast.  We want to
# extend it some distance into the future, but how far?  It seems that
# generally the wwvb change slightly anticipates the change in our rounded
# bulletin B value, so slide the last wwvb data forward until bulletin B
# catches up.  When I tested this, it involved sliding a single day.

def better(off0, off1):
    if off0 < off1: return True
    if off1 < 0 and off0 > 0: return True
    return False

if wwvb_dut1 is not None:
    off = wwvb_off
    while better(wwvb_dut1, offsets[off]):
        offsets[off] = wwvb_dut1
        off += 1

print "__all__ = ['dut1_data_start, dut1_offsets']"
print "dut1_data_start = %r" % start
c = sorted(chr(ord('a') + ch + 10) for ch in set(offsets))
print "%s = '%s'" % (",".join(c), "".join(c))
print "dut1_offsets = ( # %04d%02d%02d" % (start.year,start.month,start.day)
line = ''
now = start
j = 0

for ch, it in itertools.groupby(offsets):
    part = ""
    ch = chr(ord('a') + ch + 10)
    sz = len(list(it))
    if j: part = part + "+"
    if sz < 2:
        part = part + "%s" % ch
    else:
        part = part + "%s*%d" % (ch, sz)
    j += sz
    if len(line + part) > 60:
        d = start + datetime.timedelta(j-1)
        print "    %-60s # %04d%02d%02d" % (line, d.year, d.month, d.day)
        line = part
    else:
        line = line + part
d = start + datetime.timedelta(j-1)
print "    %-60s # %04d%02d%02d" % (line, d.year, d.month, d.day)
print ")"
