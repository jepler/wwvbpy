#!/usr/bin/python3
#    WWVB timecode generator test for pulse modulated signal
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
#    WWVB timecode generator test for pulse modulated signal
import wwvbgen
import time
import glob
import os
import io

ref_minute = wwvbgen.WWVBMinuteIERS(2012, 186, 17, 30)
ref_time = ref_minute.as_timecode()

ref_am = (
    '2011000002'
    '0001001112'
    '0001010002'
    '0110001012'
    '0100000012'
    '0010010112'
)

ref_pm = (
    '0011101101'
    '0001001000'
    '0011001000'
    '0110001101'
    '0011010001'
    '0110110110'
)

test_am = ref_time.to_am_string('012')
test_pm = ref_time.to_pm_string('01')

assert ref_am == test_am, (ref_am, test_am)
assert ref_pm == test_pm, (ref_pm, test_pm)
