#!/usr/bin/python3
#    Print leap seconds according to iers data
#    Copyright (C) 2012 Jeff Epler <jepler@unpythonic.net>
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
import datetime
import iersdata

d = iersdata.dut1_data_start
e = d + datetime.timedelta(len(iersdata.dut1_offsets))
while d < e:
    if wwvbgen.isls(d):
        sense = wwvbgen.get_dut1(d) > 0
        print("%s leap second in %s" % (("positive", "negative")[sense],
            d.strftime("%b %Y")))
    m = d.utctimetuple().tm_mon
    while d.utctimetuple().tm_mon == m: d += datetime.timedelta(1)
