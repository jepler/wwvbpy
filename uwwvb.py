# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

"""Implementation of a WWVB state machine & decoder for resource-constrained systems"""

from __future__ import annotations

from collections import namedtuple

import adafruit_datetime as datetime

ZERO, ONE, MARK = range(3)

always_mark = set((0, 9, 19, 29, 39, 49, 59))
always_zero = set((4, 10, 11, 14, 20, 21, 34, 35, 44, 54))
bcd_weights = (1, 2, 4, 8, 10, 20, 40, 80, 100, 200, 400, 800)

WWVBMinute = namedtuple(
    "WWVBMinute", ["year", "days", "hour", "minute", "dst", "ut1", "ls", "ly"]
)


class WWVBDecoder:
    """A state machine for receiving WWVB timecodes."""

    def __init__(self) -> None:
        """Construct a WWVBDecoder"""
        self.minute: list[int] = []
        self.state = 1

    def update(self, value: int) -> list[int] | None:
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

        else:  # self.state == 4:
            idx = len(self.minute)
            self.minute.append(value)
            if (idx in always_mark) != (value == MARK):
                self.state = 3 if self.minute[-2] == MARK else 2
            elif idx in always_zero and value != ZERO:
                self.state = 1

            elif idx == 59:
                result = self.minute
                self.minute = []
                self.state = 2

        return result

    def __str__(self) -> str:
        """Return a string representation of self"""
        return f"<WWVBDecoder {self.state} {self.minute}>"


def get_am_bcd(seq: list[int], *poslist: int) -> int | None:
    """Convert the bits seq[positions[0]], ... seq[positions[len(positions-1)]] [in MSB order] from BCD to decimal"""
    pos = list(poslist)[::-1]
    val = [int(seq[p]) for p in pos]
    while len(val) % 4 != 0:
        val.append(0)
    result = 0
    base = 1
    for i in range(0, len(val), 4):
        digit = 0
        for j in range(4):
            digit += 1 << j if val[i + j] else 0
        if digit > 9:
            return None
        result += digit * base
        base *= 10
    return result


def decode_wwvb(  # pylint: disable=too-many-return-statements
    t: list[int] | None,
) -> WWVBMinute | None:
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
    if minute is None:
        return None

    hour = get_am_bcd(t, 12, 13, 15, 16, 17, 18)
    if hour is None:
        return None

    days = get_am_bcd(t, 22, 23, 25, 26, 27, 28, 30, 31, 32, 33)
    if days is None:
        return None

    abs_ut1 = get_am_bcd(t, 40, 41, 42, 43)
    if abs_ut1 is None:
        return None

    abs_ut1 *= 100
    ut1_sign = t[38]
    ut1 = abs_ut1 if ut1_sign else -abs_ut1
    year = get_am_bcd(t, 45, 46, 47, 48, 50, 51, 52, 53)
    if year is None:
        return None

    is_ly = t[55]
    if days > 366 or (not is_ly and days > 365):
        return None
    ls = t[56]
    dst = get_am_bcd(t, 57, 58)
    assert dst is not None  # No possibility of BCD decode error in 2 bits

    return WWVBMinute(year, days, hour, minute, dst, ut1, ls, is_ly)


def as_datetime_utc(decoded_timestamp: WWVBMinute) -> datetime.datetime:
    """Convert a WWVBMinute to a UTC datetime"""
    d = datetime.datetime(decoded_timestamp.year + 2000, 1, 1)
    d += datetime.timedelta(
        decoded_timestamp.days - 1,
        decoded_timestamp.hour * 3600 + decoded_timestamp.minute * 60,
    )
    return d


def is_dst(
    dt: datetime.datetime,
    dst_bits: int,
    standard_time_offset: int = 7 * 3600,
    dst_observed: bool = True,
) -> bool:
    """Return True iff DST is observed at the given moment"""
    d = dt - datetime.timedelta(seconds=standard_time_offset)
    if not dst_observed:
        return False
    if dst_bits == 0b10:
        transition_time = dt.replace(hour=2)
        return d >= transition_time
    if dst_bits == 0b11:
        return True
    if dst_bits == 0b01:
        # DST ends at 2AM *DST* which is 1AM *standard*
        transition_time = dt.replace(hour=1)
        return d < transition_time
    return False


def apply_dst(
    dt: datetime.datetime,
    dst_bits: int,
    standard_time_offset: int = 7 * 3600,
    dst_observed: bool = True,
) -> datetime.datetime:
    """Apply time zone and DST (if applicable) to the given moment"""
    d = dt - datetime.timedelta(seconds=standard_time_offset)
    if is_dst(dt, dst_bits, standard_time_offset, dst_observed):
        d += datetime.timedelta(seconds=3600)
    return d


def as_datetime_local(
    decoded_timestamp: WWVBMinute,
    standard_time_offset: int = 7 * 3600,
    dst_observed: bool = True,
) -> datetime.datetime:
    """Convert a WWVBMinute to a local datetime with tzinfo=None"""
    dt = as_datetime_utc(decoded_timestamp)
    return apply_dst(dt, decoded_timestamp.dst, standard_time_offset, dst_observed)
