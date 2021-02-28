# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Implementation of a WWVB state machine & decoder for resource-constrained systems"""

try:
    import datetime
except ImportError:  # pragma no cover
    import adafruit_datetime as datetime

from collections import namedtuple

ZERO, ONE, MARK = range(3)

always_mark = set((0, 9, 19, 29, 39, 49, 59))
always_zero = set((4, 10, 11, 14, 20, 21, 34, 35, 44, 54))
bcd_weights = (1, 2, 4, 8, 10, 20, 40, 80, 100, 200, 400, 800)

WWVBMinute = namedtuple(
    "WWVBMinute", ["year", "days", "hour", "minute", "dst", "ut1", "ls"]
)


class WWVBDecoder:
    """A state machine for receiving WWVB timecodes."""

    def __init__(self):
        """Construct a WWVBDecoder"""
        self.minute = []
        self.state = 1

    def update(self, value):
        """Update the _state machine when a new symbol is received.  If a possible complete _minute is received, return it; otherwise, return None"""
        result = None
        if self.state == 1:
            self.minute = []
            if value == MARK:
                self.state = 2

        elif self.state == 2:
            if value == MARK:
                self.state = 3
            else:
                self.state = 1

        elif self.state == 3:
            if value != MARK:
                self.minute = [MARK, value]
                self.state = 4

        elif self.state == 4:
            idx = len(self.minute)
            self.minute.append(value)
            if (idx in always_mark) != (value == MARK):
                self.state = 1
            elif idx in always_zero and value != ZERO:
                self.state = 1

            elif idx == 59:
                result = self.minute
                self.minute = []
                self.state = 2

        return result

    def __str__(self):  # pragma no cover
        """Return a string representation of self"""
        return f"<WWVBDecoder {self.state} {self.minute}>"


def get_am_bcd(seq, *poslist):
    """Convert the bits seq[positions[0]], ... seq[positions[len(positions-1)]] [in MSB order] from BCD to decimal"""
    pos = list(poslist)[::-1]
    weights = bcd_weights[: len(pos)]
    result = 0
    for p, w in zip(pos, weights):
        if seq[p]:
            result += w
    return result


def decode_wwvb(t):  # pylint: disable=too-many-return-statements
    """Convert a received minute of wwvb symbols to a WWVBMinute.  Returns None if any error is detected."""
    if not t:
        return None
    if not all(t[i] == MARK for i in always_mark):
        return None
    if not all(t[i] == ZERO for i in always_zero):
        return None
    # Checking redundant DUT1 sign bits
    if t[36] == t[37]:
        return None
    if t[36] != t[38]:
        return None
    minute = get_am_bcd(t, 1, 2, 3, 5, 6, 7, 8)
    hour = get_am_bcd(t, 12, 13, 15, 16, 17, 18)
    days = get_am_bcd(t, 22, 23, 25, 26, 27, 28, 30, 31, 32, 33)
    abs_ut1 = get_am_bcd(t, 40, 41, 42, 43) * 100
    ut1_sign = t[38]
    ut1 = abs_ut1 if ut1_sign else -abs_ut1
    year = get_am_bcd(t, 45, 46, 47, 48, 50, 51, 52, 53)
    is_ly = t[55]
    if days > 366 or (not is_ly and days > 365):
        return None
    ls = t[56]
    # With just two bits, bcd and binary are the same
    dst = get_am_bcd(t, 57, 58)

    return WWVBMinute(year, days, hour, minute, dst, ut1, ls)


def as_datetime_utc(decoded_timestamp):
    """Convert a WWVBMinute to a UTC datetime"""
    year = decoded_timestamp.year
    if year < 2000:
        year = 2000 + year
    d = datetime.datetime(year, 1, 1)
    d += datetime.timedelta(
        decoded_timestamp.days - 1,
        decoded_timestamp.hour * 3600 + decoded_timestamp.minute * 60,
    )
    return d


def as_datetime_local(
    decoded_timestamp,
    standard_time_offset=7 * 3600,
    dst_observed=True,
):
    """Convert a WWVBMinute to a local datetime with tzinfo=None"""
    u = as_datetime_utc(decoded_timestamp)
    d = u - datetime.timedelta(seconds=standard_time_offset)
    dst = decoded_timestamp.dst
    if not dst_observed:
        is_dst = False
    elif dst == 0b10:
        transition_time = u.replace(hour=2)
        is_dst = d >= transition_time
    elif dst == 0b11:
        is_dst = True
    elif dst == 0b01:
        transition_time = u.replace(hour=1)
        is_dst = d < transition_time
    else:  # self.dst == 0b00
        is_dst = False
    if is_dst:
        d += datetime.timedelta(seconds=3600)
    return d
