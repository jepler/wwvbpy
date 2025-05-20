#!/usr/bin/python3
"""A package and CLI for WWVB timecodes

This is the full featured library suitable for use on 'real computers'.
For a reduced version suitable for use on MicroPython & CircuitPython,
see `uwwvb`.

This package also includes the commandline programs listed above,
perhaps most importantly ``wwvbgen`` for generating WWVB timecodes.
"""

# SPDX-FileCopyrightText: 2011-2024 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import datetime
import enum
import json
import warnings
from typing import TYPE_CHECKING, Any, NamedTuple, TextIO, TypeVar

from . import iersdata
from .tz import Mountain

if TYPE_CHECKING:
    from collections.abc import Generator

HOUR = datetime.timedelta(seconds=3600)
SECOND = datetime.timedelta(seconds=1)
T = TypeVar("T")


def _removeprefix(s: str, p: str) -> str:
    if s.startswith(p):
        return s[len(p) :]
    return s


def _date(dt: datetime.date) -> datetime.date:
    """Return the date object itself, or the date property of a datetime"""
    if isinstance(dt, datetime.datetime):
        return dt.date()
    return dt


def _maybe_warn_update(dt: datetime.date, stacklevel: int = 1) -> None:
    """Maybe print a notice to run updateiers, if it seems useful to do so."""
    # We already know this date is not covered.
    # If the date is less than 300 days after today, there should be (possibly)
    # prospective available now.
    today = datetime.datetime.now(tz=datetime.timezone.utc).date()
    if _date(dt) < today + datetime.timedelta(days=330):
        warnings.warn(
            "Note: Running `updateiers` may provide better DUT1 and LS information",
            stacklevel=stacklevel + 1,
        )


def get_dut1(dt: datetime.date, *, warn_outdated: bool = True) -> float:
    """Return the DUT1 number for the given timestamp"""
    date = _date(dt)
    i = (date - iersdata.DUT1_DATA_START).days
    if i < 0:
        v = iersdata.DUT1_OFFSETS[0]
    elif i >= len(iersdata.DUT1_OFFSETS):
        if warn_outdated:
            _maybe_warn_update(dt, stacklevel=2)
        v = iersdata.DUT1_OFFSETS[-1]
    else:
        v = iersdata.DUT1_OFFSETS[i]
    return (ord(v) - ord("k")) / 10.0


def isly(year: int) -> bool:
    """Return True if the year is a leap year"""
    d1 = datetime.date(year, 1, 1)
    d2 = d1 + datetime.timedelta(days=365)
    return d1.year == d2.year


def isls(t: datetime.date) -> bool:
    """Return True if a leap second occurs at the end of this month"""
    dut1_today = get_dut1(t)
    month_today = t.month
    while t.month == month_today:
        t += datetime.timedelta(1)
    dut1_next_month = get_dut1(t)
    return dut1_today * dut1_next_month < 0


def isdst(t: datetime.date, tz: datetime.tzinfo = Mountain) -> bool:
    """Return true if daylight saving time is active at the start of the given UTC day"""
    utc_daystart = datetime.datetime(t.year, t.month, t.day, tzinfo=datetime.timezone.utc)
    return bool(utc_daystart.astimezone(tz).dst())


def _first_sunday_on_or_after(dt: datetime.date) -> datetime.date:
    """Return the first sunday on or after the reference time"""
    days_to_go = 6 - dt.weekday()
    if days_to_go:
        return dt + datetime.timedelta(days_to_go)
    return dt


def _first_sunday_in_month(y: int, m: int) -> datetime.date:
    """Find the first sunday in a given month"""
    return _first_sunday_on_or_after(datetime.datetime(y, m, 1, tzinfo=datetime.timezone.utc))


def _is_dst_change_day(t: datetime.date, tz: datetime.tzinfo = Mountain) -> bool:
    """Return True if the day is a DST change day"""
    return isdst(t, tz) != isdst(t + datetime.timedelta(1), tz)


def _get_dst_change_hour(t: datetime.date, tz: datetime.tzinfo = Mountain) -> int | None:
    """Return the hour when DST changes"""
    lt0 = datetime.datetime(t.year, t.month, t.day, hour=0, tzinfo=tz)
    dst0 = lt0.dst()
    for i in (1, 2, 3):
        lt1 = (lt0.astimezone(datetime.timezone.utc) + HOUR * i).astimezone(tz)
        dst1 = lt1.dst()
        lt2 = lt1 - SECOND
        dst2 = lt2.dst()
        if dst0 == dst2 and dst0 != dst1:
            return i - 1
    return None


def _get_dst_change_date_and_row(
    d: datetime.date,
    tz: datetime.tzinfo = Mountain,
) -> tuple[datetime.date | None, int | None]:
    """Classify DST information for the WWVB phase modulation signal"""
    if isdst(d, tz):
        n = _first_sunday_in_month(d.year, 11)
        for offset in range(-28, 28, 7):
            d1 = n + datetime.timedelta(days=offset)
            if _is_dst_change_day(d1, tz):
                return d1, (offset + 28) // 7
    else:
        m = _first_sunday_in_month(d.year + (d.month > 3), 3)
        for offset in range(0, 52, 7):
            d1 = m + datetime.timedelta(days=offset)
            if _is_dst_change_day(d1, tz):
                return d1, offset // 7

    return None, None


# "Table 8", likely with transcrption errors
_dsttable = [
    [
        [
            0b110001,
            0b100110,
            0b100101,
            0b010101,
            0b111110,
            0b010110,
            0b110111,
            0b111101,
        ],
        [
            0b101010,
            0b011011,
            0b001110,
            0b000001,
            0b000010,
            0b001000,
            0b001101,
            0b101001,
        ],
        [
            0b000100,
            0b100000,
            0b110100,
            0b101100,
            0b111000,
            0b010000,
            0b110010,
            0b011100,
        ],
    ],
    [
        [
            0b110111,
            0b010101,
            0b110001,
            0b010110,
            0b100110,
            0b111110,
            0b100101,
            0b111101,
        ],
        [
            0b001101,
            0b000001,
            0b101010,
            0b001000,
            0b011011,
            0b000010,
            0b001110,
            0b101001,
        ],
        [
            0b110010,
            0b101100,
            0b000100,
            0b010000,
            0b100000,
            0b111000,
            0b110100,
            0b011100,
        ],
    ],
]


def _lfsr_gen(x: list[int]) -> None:
    """Generate the next bit of the 6-minute codes sequence"""
    x.append(x[-7] ^ x[-6] ^ x[-5] ^ x[-2])


_lfsr_seq = [1] * 7
while len(_lfsr_seq) < 255:
    _lfsr_gen(_lfsr_seq)

# Table 12 - Fixed 106-bit timing word
_ftw = [
    int(c)
    for c in "1101000111"
    "0101100101"
    "1001101110"
    "0011000010"
    "1101001110"
    "1001010100"
    "0010111000"
    "1011010110"
    "1101111111"
    "1000000100"
    "100100"
]


def _get_dst_next(d: datetime.date, tz: datetime.tzinfo = Mountain) -> int:
    """Find the "dst next" value for the phase modulation signal"""
    dst_now = isdst(d, tz)  # dst_on[1]
    dst_midwinter = isdst(datetime.datetime(d.year, 1, 1, tzinfo=datetime.timezone.utc), tz)
    dst_midsummer = isdst(datetime.datetime(d.year, 7, 1, tzinfo=datetime.timezone.utc), tz)

    if dst_midwinter and dst_midsummer:
        return 0b101111
    if not (dst_midwinter or dst_midsummer):
        return 0b000111

    # Southern hemisphere
    if dst_midwinter or not dst_midsummer:
        return 0b100011

    dst_change_date, dst_next_row = _get_dst_change_date_and_row(d, tz)
    if dst_change_date is None:
        return 0b100011
    assert dst_next_row is not None

    dst_change_hour = _get_dst_change_hour(dst_change_date, tz)
    if dst_change_hour is None:
        return 0b100011

    return _dsttable[dst_now][dst_change_hour][dst_next_row]


_hamming_weight = [
    [23, 21, 20, 17, 16, 15, 14, 13, 9, 8, 6, 5, 4, 2, 0],
    [24, 22, 21, 18, 17, 16, 15, 14, 10, 9, 7, 6, 5, 3, 1],
    [25, 23, 22, 19, 18, 17, 16, 15, 11, 10, 8, 7, 6, 4, 2],
    [24, 21, 19, 18, 15, 14, 13, 12, 11, 7, 6, 4, 3, 2, 0],
    [25, 22, 20, 19, 16, 15, 14, 13, 12, 8, 7, 5, 4, 3, 1],
]

# Identifies the phase data as a time signal (SYNC_T bits present)
# or a message signal (SYNC_M bits present); No message signals are defined
# by NIST at this time.
SYNC_T = 0x768
SYNC_M = 0x1A3A


def _extract_bit(v: int, p: int) -> bool:
    """Extract bit 'p' from integer 'v' as a bool"""
    return bool((v >> p) & 1)


def _hamming_parity(value: int) -> int:
    """Compute the "hamming parity" of a 26-bit number, such as the minute-of-century

    For more details, see Enhanced WWVB Broadcast Format 4.3
    """
    parity = 0
    for i in range(4, -1, -1):
        bit = 0
        for j in range(15):
            bit ^= _extract_bit(value, _hamming_weight[i][j])
        parity = (parity << 1) | bit
    return parity


_dst_ls_lut = [
    0b01000,
    0b10101,
    0b10110,
    0b00011,
    0b01000,
    0b10101,
    0b10110,
    0b00011,
    0b00100,
    0b01110,
    0b10000,
    0b01101,
    0b11001,
    0b11100,
    0b11010,
    0b11111,
]


@enum.unique
class DstStatus(enum.IntEnum):
    """Constants that describe the DST status of a minute"""

    DST_NOT_IN_EFFECT = 0b00
    """DST not in effect today"""
    DST_STARTS_TODAY = 0b01
    """DST starts today at 0200 local standard time"""
    DST_ENDS_TODAY = 0b10
    """DST ends today at 0200 local standard time"""
    DST_IN_EFFECT = 0b11
    """DST in effect all day today"""


class _WWVBMinute(NamedTuple):
    """(implementation detail)"""

    year: int
    """2-digit year within the WWVB epoch"""

    days: int
    """1-based day of year"""

    hour: int
    """UTC hour of day"""

    min: int
    """Minute of hour"""

    dst: DstStatus
    """2-bit DST code """

    ut1: int
    """UT1 offset in units of 100ms, range -900 to +900ms"""

    ls: bool
    """Leap second warning flag"""

    ly: bool
    """Leap year flag"""


class WWVBMinute(_WWVBMinute):
    """Uniquely identifies a minute of time in the WWVB system.

    To use ``ut1`` and ``ls`` information from IERS, create a `WWVBMinuteIERS`
    object instead.
    """

    epoch: int = 1970

    def __new__(  # noqa: PYI034
        cls,
        year: int,
        days: int,
        hour: int,
        minute: int,
        dst: DstStatus | int | None = None,
        ut1: int | None = None,
        ls: bool | None = None,
        ly: bool | None = None,
    ) -> WWVBMinute:
        """Construct a WWVBMinute

        :param year: The 2- or 4-digit year. This parameter is converted by the `full_year` method.
        :param days: 1-based day of year

        :param hour: UTC hour of day

        :param minute: Minute of hour
        :param dst: 2-bit DST code
        :param ut1: UT1 offset in units of 100ms, range -900 to +900ms
        :param ls: Leap second warning flag
        :param ly: Leap year flag
        """
        dst = cls.get_dst(year, days) if dst is None else DstStatus(dst)
        if ut1 is None and ls is None:
            ut1, ls = cls._get_dut1_info(year, days)
        elif ut1 is None or ls is None:
            raise ValueError("sepecify both ut1 and ls or neither one")
        year = cls.full_year(year)
        if ly is None:
            ly = isly(year)
        return _WWVBMinute.__new__(cls, year, days, hour, minute, dst, ut1, ls, ly)

    @classmethod
    def full_year(cls, year: int) -> int:
        """Convert a (possibly two-digit) year to a full year.

        If the argument is above 100, it is assumed to be a full year.
        Otherwise, the intuitive method is followed: Say the epoch is 1970,
        then 70..99 means 1970..99 and 00..69 means 2000..2069.

        To actually use a different epoch, derive a class from WWVBMinute (or
        WWVBMinuteIERS) and give it a different epoch property.  Then, create
        instances of that class instead of WWVBMinute.
        """
        century = cls.epoch // 100 * 100
        if year < (cls.epoch % 100):
            return year + century + 100
        if year < 100:
            return year + century
        return year

    @staticmethod
    def get_dst(year: int, days: int) -> DstStatus:
        """Get the 2-bit WWVB DST value for the given day"""
        d0 = datetime.datetime(year, 1, 1, tzinfo=datetime.timezone.utc) + datetime.timedelta(days - 1)
        d1 = d0 + datetime.timedelta(1)
        dst0 = isdst(d0)
        dst1 = isdst(d1)
        return DstStatus(dst1 * 2 + dst0)

    def __str__(self) -> str:
        """Implement str()"""
        return (
            f"year={self.year:4d} days={self.days:03d} hour={self.hour:02d} "
            f"min={self.min:02d} dst={self.dst} ut1={self.ut1} ly={int(self.ly)} "
            f"ls={int(self.ls)}"
        )

    def as_datetime_utc(self) -> datetime.datetime:
        """Convert to a UTC datetime

        The returned object has ``tzinfo=datetime.timezone.utc``.
        """
        d = datetime.datetime(self.year, 1, 1, tzinfo=datetime.timezone.utc)
        d += datetime.timedelta(self.days - 1, self.hour * 3600 + self.min * 60)
        return d

    as_datetime = as_datetime_utc

    def as_datetime_local(
        self,
        standard_time_offset: int = 7 * 3600,
        *,
        dst_observed: bool = True,
    ) -> datetime.datetime:
        """Convert to a local datetime according to the DST bits

        The returned object has ``tz=datetime.timezone(computed_offset)``.

        :param standard_time_offset: The UTC offset of local standard time, in seconds west of UTC.
            The default value, ``7 * 3600``, is for Colorado, the source of the WWVB broadcast.

        :param dst_observed: If ``True`` then the locale observes DST, and a
            one hour offset is applied according to WWVB rules. If ``False``, then
            the standard time offset is used at all times.

        """
        u = self.as_datetime_utc()
        offset = datetime.timedelta(seconds=-standard_time_offset)
        d = u - datetime.timedelta(seconds=standard_time_offset)
        if not dst_observed:
            dst = False
        elif self.dst == 0b10:
            transition_time = u.replace(hour=2)
            dst = d >= transition_time
        elif self.dst == 0b11:
            dst = True
        elif self.dst == 0b01:
            transition_time = u.replace(hour=1)
            dst = d < transition_time
        else:  # self.dst == 0b00
            dst = False
        if dst:
            offset += datetime.timedelta(seconds=3600)
        return u.astimezone(datetime.timezone(offset))

    def _is_end_of_month(self) -> bool:
        """Return True if minute is the last minute in a month"""
        d = self.as_datetime()
        e = d + datetime.timedelta(1)
        return d.month != e.month

    def minute_length(self) -> int:
        """Return the length of the minute, 60, 61, or (theoretically) 59 seconds"""
        if not self.ls:
            return 60
        if not self._is_end_of_month():
            return 60
        if self.hour != 23 or self.min != 59:
            return 60
        if self.ut1 > 0:
            return 59
        return 61

    def as_timecode(self) -> WWVBTimecode:
        """Fill a WWVBTimecode structure representing this minute.  Fills both the amplitude and phase codes."""
        t = WWVBTimecode(self.minute_length())

        self._fill_am_timecode(t)
        self._fill_pm_timecode(t)

        return t

    @property
    def _leap_sec(self) -> int:
        """Return the 2-bit _leap_sec value used by the PM code"""
        if not self.ls:
            return 0
        if self.ut1 < 0:
            return 3
        return 2

    @property
    def minute_of_century(self) -> int:
        """Return the minute of the century"""
        century = (self.year // 100) * 100
        # note: This relies on timedelta seconds never including leapseconds!
        return (
            int((self.as_datetime() - datetime.datetime(century, 1, 1, tzinfo=datetime.timezone.utc)).total_seconds())
            // 60
        )

    def _fill_am_timecode(self, t: WWVBTimecode) -> None:
        """Fill the amplitude (AM) portion of a timecode object"""
        for i in [0, 9, 19, 29, 39, 49]:
            t.am[i] = AmplitudeModulation.MARK
        if len(t.am) > 59:
            t.am[59] = AmplitudeModulation.MARK
        if len(t.am) > 60:
            t.am[60] = AmplitudeModulation.MARK
        for i in [4, 10, 11, 14, 20, 21, 24, 34, 35, 44, 54]:
            t.am[i] = AmplitudeModulation.ZERO
        t._put_am_bcd(self.min, 1, 2, 3, 5, 6, 7, 8)
        t._put_am_bcd(self.hour, 12, 13, 15, 16, 17, 18)
        t._put_am_bcd(self.days, 22, 23, 25, 26, 27, 28, 30, 31, 32, 33)
        ut1_sign = self.ut1 >= 0
        t.am[36] = t.am[38] = AmplitudeModulation(ut1_sign)
        t.am[37] = AmplitudeModulation(not ut1_sign)
        t._put_am_bcd(abs(self.ut1) // 100, 40, 41, 42, 43)
        t._put_am_bcd(self.year, 45, 46, 47, 48, 50, 51, 52, 53)  # Implicitly discards all but lowest 2 digits of year
        t.am[55] = AmplitudeModulation(self.ly)
        t.am[56] = AmplitudeModulation(self.ls)
        t._put_am_bcd(self.dst, 57, 58)

    def _fill_pm_timecode_extended(self, t: WWVBTimecode) -> None:
        """During minutes 10..15 and 40..45, the amplitude signal holds 'extended information'"""
        assert 10 <= self.min < 16 or 40 <= self.min < 46
        minno = self.min % 10
        assert minno < 6

        dst = self.dst
        # Note that these are 1 different than Table 11
        # because our LFSR sequence is zero-based
        seqno = (self.min // 30) * 2
        if dst == 0:
            pass
        elif dst == 3:
            seqno = seqno + 1
        elif dst == 2:
            if self.hour < 4:
                pass
            elif self.hour < 11:
                seqno = seqno + 90
            else:
                seqno = seqno + 1
        elif self.hour < 4:
            seqno = seqno + 1
        elif self.hour < 11:
            seqno = seqno + 91

        info_seq = _lfsr_seq[seqno : seqno + 127]
        full_seq = info_seq + _ftw + info_seq[::-1]
        assert len(full_seq) == 360

        offset = minno * 60
        for i in range(60):
            t._put_pm_bit(i, full_seq[i + offset])

    def _fill_pm_timecode_regular(self, t: WWVBTimecode) -> None:  # noqa: PLR0915
        """Except during minutes 10..15 and 40..45, the amplitude signal holds 'regular information'"""
        t._put_pm_bin(0, 13, SYNC_T)

        moc = self.minute_of_century
        _leap_sec = self._leap_sec
        dst_on = self.dst
        dst_ls = _dst_ls_lut[dst_on | (_leap_sec << 2)]
        dst_next = _get_dst_next(self.as_datetime())
        t._put_pm_bin(13, 5, _hamming_parity(moc))
        t._put_pm_bit(18, _extract_bit(moc, 25))
        t._put_pm_bit(19, _extract_bit(moc, 0))
        t._put_pm_bit(20, _extract_bit(moc, 24))
        t._put_pm_bit(21, _extract_bit(moc, 23))
        t._put_pm_bit(22, _extract_bit(moc, 22))
        t._put_pm_bit(23, _extract_bit(moc, 21))
        t._put_pm_bit(24, _extract_bit(moc, 20))
        t._put_pm_bit(25, _extract_bit(moc, 19))
        t._put_pm_bit(26, _extract_bit(moc, 18))
        t._put_pm_bit(27, _extract_bit(moc, 17))
        t._put_pm_bit(28, _extract_bit(moc, 16))
        t._put_pm_bit(29, False)  # noqa: FBT003 # Reserved
        t._put_pm_bit(30, _extract_bit(moc, 15))
        t._put_pm_bit(31, _extract_bit(moc, 14))
        t._put_pm_bit(32, _extract_bit(moc, 13))
        t._put_pm_bit(33, _extract_bit(moc, 12))
        t._put_pm_bit(34, _extract_bit(moc, 11))
        t._put_pm_bit(35, _extract_bit(moc, 10))
        t._put_pm_bit(36, _extract_bit(moc, 9))
        t._put_pm_bit(37, _extract_bit(moc, 8))
        t._put_pm_bit(38, _extract_bit(moc, 7))
        t._put_pm_bit(39, True)  # noqa: FBT003 # Reserved
        t._put_pm_bit(40, _extract_bit(moc, 6))
        t._put_pm_bit(41, _extract_bit(moc, 5))
        t._put_pm_bit(42, _extract_bit(moc, 4))
        t._put_pm_bit(43, _extract_bit(moc, 3))
        t._put_pm_bit(44, _extract_bit(moc, 2))
        t._put_pm_bit(45, _extract_bit(moc, 1))
        t._put_pm_bit(46, _extract_bit(moc, 0))
        t._put_pm_bit(47, _extract_bit(dst_ls, 4))
        t._put_pm_bit(48, _extract_bit(dst_ls, 3))
        t._put_pm_bit(49, True)  # noqa: FBT003 # Notice
        t._put_pm_bit(50, _extract_bit(dst_ls, 2))
        t._put_pm_bit(51, _extract_bit(dst_ls, 1))
        t._put_pm_bit(52, _extract_bit(dst_ls, 0))
        t._put_pm_bit(53, _extract_bit(dst_next, 5))
        t._put_pm_bit(54, _extract_bit(dst_next, 4))
        t._put_pm_bit(55, _extract_bit(dst_next, 3))
        t._put_pm_bit(56, _extract_bit(dst_next, 2))
        t._put_pm_bit(57, _extract_bit(dst_next, 1))
        t._put_pm_bit(58, _extract_bit(dst_next, 0))
        if len(t.phase) > 59:
            t._put_pm_bit(59, PhaseModulation.ZERO)
        if len(t.phase) > 60:
            t._put_pm_bit(60, PhaseModulation.ZERO)

    def _fill_pm_timecode(self, t: WWVBTimecode) -> None:
        """Fill the phase portion of a timecode object"""
        if 10 <= self.min < 16 or 40 <= self.min < 46:
            self._fill_pm_timecode_extended(t)
        else:
            self._fill_pm_timecode_regular(t)

    def next_minute(self, newut1: int | None = None, newls: bool | None = None) -> WWVBMinute:
        """Return an object representing the next minute"""
        d = self.as_datetime() + datetime.timedelta(minutes=1)
        return self.from_datetime(d, newut1, newls, self)

    def previous_minute(self, newut1: int | None = None, newls: bool | None = None) -> WWVBMinute:
        """Return an object representing the previous minute"""
        d = self.as_datetime() - datetime.timedelta(minutes=1)
        return self.from_datetime(d, newut1, newls, self)

    @classmethod
    def _get_dut1_info(cls: type, year: int, days: int, old_time: WWVBMinute | None = None) -> tuple[int, bool]:  # noqa: ARG003
        """Return the DUT1 information for a given day, possibly propagating information from a previous timestamp"""
        if old_time is not None:
            if old_time.minute_length() != 60:
                newls = False
                newut1 = old_time.ut1 + 1000 if old_time.ut1 < 0 else old_time.ut1 - 1000
            else:
                newls = old_time.ls
                newut1 = old_time.ut1
            return newut1, newls
        return 0, False

    @classmethod
    def fromstring(cls, s: str) -> WWVBMinute:
        """Construct a WWVBMinute from a string representation created by print_timecodes"""
        s = _removeprefix(s, "WWVB timecode: ")
        d: dict[str, int] = {}
        for part in s.split():
            k, v = part.split("=")
            if k == "min":
                k = "minute"
            d[k] = int(v)
        year = d.pop("year")
        days = d.pop("days")
        hour = d.pop("hour")
        minute = d.pop("minute")
        dst: int | None = d.pop("dst", None)
        ut1: int | None = d.pop("ut1", None)
        ls = d.pop("ls", None)
        d.pop("ly", None)
        if d:
            raise ValueError(f"Invalid options: {d}")
        return cls(year, days, hour, minute, dst, ut1, None if ls is None else bool(ls))

    @classmethod
    def from_datetime(
        cls,
        d: datetime.datetime,
        newut1: int | None = None,
        newls: bool | None = None,
        old_time: WWVBMinute | None = None,
    ) -> WWVBMinute:
        """Construct a WWVBMinute from a datetime, possibly specifying ut1/ls data or propagating it from an old time"""
        u = d.utctimetuple()
        if newls is None and newut1 is None:
            newut1, newls = cls._get_dut1_info(u.tm_year, u.tm_yday, old_time)
        return cls(u.tm_year, u.tm_yday, u.tm_hour, u.tm_min, ut1=newut1, ls=newls)

    @classmethod
    def from_timecode_am(cls, t: WWVBTimecode) -> WWVBMinute | None:  # noqa: PLR0912
        """Construct a WWVBMinute from a WWVBTimecode"""
        for i in (0, 9, 19, 29, 39, 49, 59):
            if t.am[i] != AmplitudeModulation.MARK:
                return None
        for i in (4, 10, 11, 14, 20, 21, 24, 34, 35, 44, 54):
            if t.am[i] != AmplitudeModulation.ZERO:
                return None
        if t.am[36] == t.am[37]:
            return None
        if t.am[36] != t.am[38]:
            return None
        minute = t._get_am_bcd(1, 2, 3, 5, 6, 7, 8)
        if minute is None:
            return None
        if minute >= 60:
            return None
        hour = t._get_am_bcd(12, 13, 15, 16, 17, 18)
        if hour is None:
            return None
        if hour >= 24:
            return None
        days = t._get_am_bcd(22, 23, 25, 26, 27, 28, 30, 31, 32, 33)
        if days is None:
            return None
        abs_ut1 = t._get_am_bcd(40, 41, 42, 43)
        if abs_ut1 is None:
            return None
        abs_ut1 *= 100
        ut1_sign = t.am[38]
        ut1 = abs_ut1 if ut1_sign else -abs_ut1
        year = t._get_am_bcd(45, 46, 47, 48, 50, 51, 52, 53)
        if year is None:
            return None
        ly = bool(t.am[55])
        if days > 366 or (not ly and days > 365):
            return None
        ls = bool(t.am[56])
        dst = t._get_am_bcd(57, 58)
        if dst is None:
            return None
        return cls(year, days, hour, minute, dst, ut1, ls, ly)


class WWVBMinuteIERS(WWVBMinute):
    """A WWVBMinute that uses a database of DUT1 information"""

    @classmethod
    def _get_dut1_info(cls, year: int, days: int, old_time: WWVBMinute | None = None) -> tuple[int, bool]:  # noqa: ARG003
        d = datetime.datetime(year, 1, 1, tzinfo=datetime.timezone.utc) + datetime.timedelta(days - 1)
        return round(get_dut1(d) * 10) * 100, isls(d)


def _bcd_bits(n: int) -> Generator[bool]:
    """Return the bcd representation of n, starting with the least significant bit"""
    while True:
        d = n % 10
        n = n // 10
        for i in (1, 2, 4, 8):
            yield bool(d & i)


@enum.unique
class AmplitudeModulation(enum.IntEnum):
    """Constants that describe an Amplitude Modulation value"""

    ZERO = 0
    """A zero bit (reduced carrier during the first 200ms of the second)"""
    ONE = 1
    """A one bit (reduced carrier during the first 500ms of the second)"""
    MARK = 2
    """A mark bit (reduced carrier during the first 800ms of the second)"""
    UNSET = -1
    """An unset or unknown amplitude modulation value"""


@enum.unique
class PhaseModulation(enum.IntEnum):
    """Constants that describe a Phase Modulation value"""

    ZERO = 0
    """A one bit (180° phase shift during the second)"""
    ONE = 1
    """A zero bit (No phase shift during the second)"""
    UNSET = -1
    """An unset or unknown phase modulation value"""


class WWVBTimecode:
    """Represent the amplitude and/or phase signal, usually over 1 minute"""

    am: list[AmplitudeModulation]
    """The amplitude modulation data"""

    phase: list[PhaseModulation]
    """The phase modulation data"""

    def __init__(self, sz: int) -> None:
        """Construct a WWVB timecode ``sz`` seconds long"""
        self.am = [AmplitudeModulation.UNSET] * sz
        self.phase = [PhaseModulation.UNSET] * sz

    def _get_am_bcd(self, *poslist: int) -> int | None:
        """Convert AM data to BCD

        The the bits ``self.am[poslist[i]]`` in MSB order are converted from
        BCD to integer
        """
        pos = list(poslist)[::-1]
        for p in pos:
            if self.am[p] not in {AmplitudeModulation.ZERO, AmplitudeModulation.ONE}:
                return None
        val = [bool(self.am[p]) for p in pos]
        result = 0
        base = 1
        for i in range(0, len(val), 4):
            digit = 0
            for j, b in enumerate(val[i : i + 4]):
                digit += b << j
            if digit > 9:
                return None
            result += digit * base
            base *= 10
        return result

    def _put_am_bcd(self, v: int, *poslist: int) -> None:
        """Insert BCD coded data into the AM signal

        The bits at ``self.am[poslist[i]]`` in MSB order are filled with
        the conversion of `v` to BCD
        Treating 'poslist' as a sequence of indices, update the AM signal with the value as a BCD number
        """
        pos = list(poslist)[::-1]
        for p, b in zip(pos, _bcd_bits(v)):
            if b:
                self.am[p] = AmplitudeModulation.ONE
            else:
                self.am[p] = AmplitudeModulation.ZERO

    def _put_pm_bit(self, i: int, v: PhaseModulation | int | bool) -> None:
        """Update a bit of the Phase Modulation signal"""
        self.phase[i] = PhaseModulation(v)

    def _put_pm_bin(self, st: int, n: int, v: int) -> None:
        """Update an n-digit binary number in the Phase Modulation signal"""
        for i in range(n):
            self._put_pm_bit(st + i, _extract_bit(v, (n - i - 1)))

    def __str__(self) -> str:
        """Implement str()"""
        undefined = [i for i in range(len(self.am)) if self.am[i] == AmplitudeModulation.UNSET]
        if undefined:
            warnings.warn(f"am{undefined} is unset", stacklevel=1)

        def convert_one(am: AmplitudeModulation, phase: PhaseModulation) -> str:
            if phase is PhaseModulation.UNSET:
                return ("0", "1", "2", "?")[am]
            if phase:
                return ("⁰", "¹", "²", "¿")[am]
            return ("₀", "₁", "₂", "⸮")[am]

        return "".join(convert_one(i, j) for i, j in zip(self.am, self.phase))

    def __repr__(self) -> str:
        """Implement repr()"""
        return "<WWVBTimecode " + str(self) + ">"

    def to_am_string(self, charset: list[str]) -> str:
        """Convert the amplitude signal to a string"""
        return "".join(charset[i] for i in self.am)

    to_string = to_am_string

    def to_pm_string(self, charset: list[str]) -> str:
        """Convert the phase signal to a string"""
        return "".join(charset[i] for i in self.phase)

    def to_both_string(self, charset: list[str]) -> str:
        """Convert both channels to a string"""
        return "".join(charset[i + j * 3] for i, j in zip(self.am, self.phase))


styles = {
    "default": ["0", "1", "2"],
    "duration": ["2", "5", "8"],
    "cradek": ["0", "1", "-"],
    "bar": ["🬍🬎", "🬋🬎", "🬋🬍"],
    "sextant": ["🬍🬎", "🬋🬎", "🬋🬍", "🬩🬹", "🬋🬹", "🬋🬩"],
}


def print_timecodes(
    w: WWVBMinute,
    minutes: int,
    channel: str,
    style: str,
    file: TextIO,
    *,
    all_timecodes: bool = False,
) -> None:
    """Print a range of timecodes with a header.  This header is in a format understood by WWVBMinute.fromstring"""
    channel_text = "" if channel == "amplitude" else f" --channel={channel}"
    style_text = "" if style == "default" else f" --style={style}"
    style_chars = styles.get(style, ["0", "1", "2"])
    first = True
    for _ in range(minutes):
        if not first and channel == "both":
            print(file=file)
        if first or all_timecodes:
            if not first:
                print(file=file)
            print(f"WWVB timecode: {w!s}{channel_text}{style_text}", file=file)
        first = False
        pfx = f"{w.year:04d}-{w.days:03d} {w.hour:02d}:{w.min:02d} "
        tc = w.as_timecode()
        if len(style_chars) == 6:
            print(f"{pfx} {tc.to_both_string(style_chars)}", file=file)
            print(file=file)
            pfx = " " * len(pfx)
        else:
            if channel in ("amplitude", "both"):
                print(f"{pfx} {tc.to_am_string(style_chars)}", file=file)
                pfx = " " * len(pfx)
            if channel in ("phase", "both"):
                print(f"{pfx} {tc.to_pm_string(style_chars)}", file=file)
        w = w.next_minute()


def print_timecodes_json(
    w: WWVBMinute,
    minutes: int,
    channel: str,
    file: TextIO,
) -> None:
    """Print a range of timecodes in JSON format.

    The result is a json array of minute data. Each minute data is an object with the following members:

        * year (int)
        * days (int)
        * hour (int)
        * minute (int)
        * amplitude (string; only if channel is amplitude or both)
        * phase: (string; only if channel is phase or both)

    The amplitude and phase strings are of length 60 during most minutes, length 61
    during a minute that includes a (positive) leap second, and theoretically
    length 59 in the case of a negative leap second.
    """
    result = []
    for _ in range(minutes):
        data: dict[str, Any] = {
            "year": w.year,
            "days": w.days,
            "hour": w.hour,
            "minute": w.min,
        }

        tc = w.as_timecode()
        if channel in ("amplitude", "both"):
            data["amplitude"] = tc.to_am_string(["0", "1", "2"])
        if channel in ("phase", "both"):
            data["phase"] = tc.to_pm_string(["0", "1"])

        result.append(data)
        w = w.next_minute()
    json.dump(result, file)
    print(file=file)
