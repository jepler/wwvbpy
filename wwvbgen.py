#!/usr/bin/python3
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

import collections
import datetime
import math
import optparse
import time
import iersdata
import string

def get_dut1(t):
    i = (t - iersdata.dut1_data_start).days
    if i < 0: v = iersdata.dut1_offsets[0]
    elif i >= len(iersdata.dut1_offsets): v = iersdata.dut1_offsets[-1]
    else: v = iersdata.dut1_offsets[i]
    return (ord(v) - ord('k')) / 10.

def isls(t):
    dut1_today = get_dut1(t)
    month_today = t.month
    while t.month == month_today: t += datetime.timedelta(1)
    dut1_next_month = get_dut1(t)
    return dut1_today * dut1_next_month < 0

def isdst(t):
    t0 = datetime.datetime(1970,1,1)
    d = t - t0
    stamp = d.days * 86400 + d.seconds + d.microseconds * 1e-6
    return time.localtime(stamp).tm_isdst

_WWVBMinute = collections.namedtuple('_WWVBMinute',
    'year days hour min dst ut1 ls')
class WWVBMinute(_WWVBMinute):
    def __new__(cls, year, days, hour, min, dst=None, ut1=None, ls=None):
        if dst is None:
            dst = cls.get_dst(year, days)
        if ut1 is None and ls is None:
            ut1, ls = cls.get_dut1_info(year, days)
        elif ut1 is None or ls is None:
            raise ValueError("sepecify both ut1 and ls or neither one")
        if year < 70: year = year + 2000
        elif year < 100: year = year + 1900
        return _WWVBMinute.__new__(cls, year, days, hour, min, dst, ut1, ls)

    @staticmethod
    def get_dst(year, days):
        d0 = datetime.datetime(year, 1, 1) + datetime.timedelta(days-1)
        d1 = d0 + datetime.timedelta(1)
        dst0 = isdst(d0)
        dst1 = isdst(d1)
        return dst1*2 + dst0

    def __str__(self):
        return "year=%.2d days=%.3d hour=%.2d min=%.2d dst=%d ut1=%d ly=%d ls=%d" % (
            self.year%100, self.days, self.hour, self.min, self.dst,
            self.ut1, self.is_ly(), self.ls)

    def as_datetime(self):
        d = datetime.datetime(self.year, 1, 1)
        d += datetime.timedelta(self.days-1, self.hour * 3600 + self.min * 60)
        return d

    def is_ly(self):
        d = datetime.datetime(self.year, 1, 1) + datetime.timedelta(365)
        return d.year == self.year

    def is_end_of_month(self):
        d = self.as_datetime()
        e = d + datetime.timedelta(1)
        return d.month != e.month

    def minute_length(self):
        if not self.ls: return 60
        if not self.is_end_of_month(): return 60
        if self.hour != 23 or self.min != 59: return 60
        if self.ut1 > 0: return 59
        return 61

    def as_timecode(self):
        t = WWVBTimecode(self.minute_length())
        t[0, 9, 19, 29, 39, 49] = 2
        if len(t.data) > 59: t[59] = 2
        if len(t.data) > 60: t[60] = 2
        t[4, 10, 11, 14, 20, 21, 24, 34, 35, 44, 54] = 0
        t.put_bcd(self.min, 1, 2, 3, 5, 6, 7, 8)
        t.put_bcd(self.hour, 12, 13, 15, 16, 17, 18)
        t.put_bcd(self.days, 22, 23, 25, 26, 27, 28, 30, 31, 32, 33)
        ut1_sign = self.ut1 >= 0
        t[36, 38] = ut1_sign
        t[37] = not ut1_sign
        t.put_bcd(abs(self.ut1) // 100, 40, 41, 42, 43)
        t.put_bcd(self.year, 45, 46, 47, 48, 50, 51, 52, 53)
        t[55] = self.is_ly()
        t[56] = self.ls
        t.put_bcd(self.dst, 57, 58)
        return t

    def next_minute(self, newut1=None, newls=None):
        d = self.as_datetime() + datetime.timedelta(0,60)
        u = d.utctimetuple()
        if newls is None and newut1 is None:
            newut1, newls = self.get_dut1_info(u.tm_year, u.tm_yday, self)
        return type(self)(u.tm_year, u.tm_yday, u.tm_hour, u.tm_min, ut1=newut1,
                        ls=newls)

    @classmethod
    def get_dut1_info(cls, year, days, old_time=None):
        if old_time is not None:
            if old_time.minute_length() != 60:
                newls = 0
                if old_time.ut1 < 0:
                    newut1 = old_time.ut1 + 1000
                else:
                    newut1 = old_time.ut1 - 1000
            else:
                newls = old_time.ls
                newut1 = old_time.ut1
            return newut1, newls
        else:
            return 0, 0

    @classmethod
    def fromstring(cls, s):
        if s.startswith("WWVB timecode: "):
            s = s[len("WWVB timecode: "):]
        d = {}
        for part in s.split():
            k, v = part.split("=")
            d[k] = int(v)
        if 'ly' in d: d.pop('ly')
        return cls(**d)

class WWVBMinuteIERS(WWVBMinute):
    @classmethod
    def get_dut1_info(cls, year, days, old_time=None):
        d = datetime.datetime(year, 1, 1) + datetime.timedelta(days-1)
        return int(round(get_dut1(d)*10))*100, isls(d)
                
def ilog10(v):
    i = int(math.floor(math.log(v) / math.log(10)))
    if 10 ** i > 10*v: return i-1
    return i

def bcd(n, d):
    l = 10 ** ilog10(n)
    n = (n // l) % 10
    d = (d // l) % 10
    return int(bool(n & d))

bcd_weights = [1, 2, 4, 8, 10, 20, 40, 80, 100, 200, 400, 800]

class WWVBTimecode:
    def __init__(self, sz):
        self.data = [None] * sz

    def put_bcd(self, v, *poslist):
        pos = list(poslist)[::-1]
        weights = bcd_weights[:len(pos)]
        for p, w in zip(pos, weights):
            b = bcd(w, v)
            if b: self[p] = 1
            else: self[p] = 0

    def __setitem__(self, i, v):
        assert v in (0, 1, 2)
        v = int(v) # True -> 1
        if isinstance(i, tuple):
            for j in i:
                self.data[j] = v
        else:
            self.data[i] = v

    def __str__(self):
        undefined = [i for i in range(len(self.data)) if self.data[i] is None]
        if undefined:
            print("Warning: Timecode%s is undefined" % undefined)
        def ch(c):
            if c in (0, 1, 2): return str(c)
            return '?'

        return "".join(ch(i) for i in self.data)

    def __repr__(self):
        return "<WWVBTimecode " + str(self) + ">"

if __name__ == '__main__':
    import optparse
    parser = optparse.OptionParser(usage="Usage: %prog [options] [year yday hour minute]")
    parser.add_option("-i", "--iers", dest="iers",
        help="use IERS data for DUT1 and LS [Default]",
        action="store_true", default=True)
    parser.add_option("-I", "--no-iers", dest="iers",
        help="do not use IERS data for DUT1 and LS", action="store_false")
    parser.add_option("-s", "--leap-second", dest="forcels",
        help="force a leap second  [Requires --no-iers]",
        action="store_true", default=None)
    parser.add_option("-S", "--no-leap-second", dest="forcels",
        help="force no leap second [Requires --no-iers]", action="store_false")
    parser.add_option("-d", "--dut1", dest="forcedut1",
        help="force dut1           [Requires --no-iers]",
        metavar="DUT1", default=None)
    parser.add_option("-m", "--minutes", dest="minutes",
        help="number of minutes to generate [Default: 10]",
        metavar="MINUTES", type="int", default=10)
    options, args = parser.parse_args()

    if options.iers:
        constructor = WWVBMinuteIERS
    else:
        constructor = WWVBMinute

    if args:
        if len(args) != 4:
            parser.print_help()
            raise SystemExit("Expected 4 arguments, got %d" % len(args))
        try:
                year, yday, hour, minute = map(int, args)
        except ValueError:
            parser.print_help()
            raise SystemExit("Arguments must be numeric")
    else:
        now = datetime.datetime.utcnow().utctimetuple()
        year, yday, hour, minute = now.tm_year, now.tm_yday, now.tm_hour, now.tm_min

    w = constructor(year, yday, hour, minute)
    print("WWVB timecode: %s" % str(w))
    for i in range(options.minutes):
        print("'%02d+%03d %02d:%02d  %s" % (
            w.year % 100, w.days, w.hour, w.min, w.as_timecode()))
        w = w.next_minute()
