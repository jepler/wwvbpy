#!/usr/bin/python3
#    WWVB timecode generator
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

from tkinter import *
import time
import sys

import wwvbgen


def sleep_deadline(deadline):
    now = time.time()
    if deadline > now:
        time.sleep(deadline - now)


def wwvbtick():
    timestamp = time.time() // 60 * 60

    while True:
        tt = time.gmtime(timestamp)
        key = tt.tm_year, tt.tm_yday, tt.tm_hour, tt.tm_min
        timecode = wwvbgen.WWVBMinuteIERS(*key).as_timecode()
        for i, code in enumerate(timecode.am):
            yield timestamp + i, code
        timestamp = timestamp + 60


def wwvbsmarttick():
    # Deal with time progressing unexpectedly, such as when the computer is
    # suspended or NTP steps the clock backwards
    #
    # When time goes backwards or advances by more than a minute, get a fresh
    # wwvbtick object; otherwise, discard time signals more than 1s in the past.
    while True:
        for stamp, code in wwvbtick():
            now = time.time()
            if stamp < now - 60:
                break
            if stamp < now - 1:
                continue
            yield stamp, code


app = Tk()
canvas = Canvas(app, width=48, height=48)
canvas.pack()

colors = ["#3c3c3c", "#cc3c3c", "#88883c", "#3ccc3c"]

circle = canvas.create_oval(4, 4, 44, 44, outline="black", fill=colors[0])


def led_on(i):
    canvas.itemconfigure(circle, fill=colors[i + 1])


def led_off():
    canvas.itemconfigure(circle, fill=colors[0])


for stamp, code in wwvbsmarttick():
    sleep_deadline(stamp)
    led_on(code)
    app.update()
    sleep_deadline(stamp + 0.2 + 0.3 * int(code))
    led_off()
    app.update()
