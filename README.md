<!--
SPDX-FileCopyrightText: 2021 Jeff Epler

SPDX-License-Identifier: GPL-3.0-only
-->
[![Test wwvbgen](https://github.com/jepler/wwvbpy/actions/workflows/test.yml/badge.svg)](https://github.com/jepler/wwvbpy/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/jepler/wwvbpy/branch/main/graph/badge.svg?token=Exx0c3Gp65)](https://codecov.io/gh/jepler/wwvbpy)
[![Update DUT1 data](https://github.com/jepler/wwvbpy/actions/workflows/cron.yml/badge.svg)](https://github.com/jepler/wwvbpy/actions/workflows/cron.yml)

# Purpose

wwvbpy generates WWVB timecodes for any desired time.  These timecodes
may be useful in testing WWVB decoder software.

Where possible, wwvbpy uses existing facilities for calendar and time
manipulation (datetime).  It uses code adapted from standard Python
documentation for the US DST rules (tzinfo\_us) regardless of the operating
system's time zone.

It uses DUT1/leap second data derived from IERS Bulletin "A" and from NIST's
"Leap second and UT1-UTC information" page.  With regular updates to
`iersdata.py`, wwvbpy should be able to correctly encode the time anywhere
within the 100-year WWVB epoch.  (yes, WWVB uses a 2-digit year! In order to
work with historical data, the epoch is arbitrarily assumed to run from 1970 to
2069.)

Programs include:
 * wwvbgen, the main commandline generator program
 * wwvbtk, visualize the simulated WWVB signal in real-time using Tkinter
 * dut1table, print the full history of dut1 values, including estimated future values

The package includes:
 * wwvb, for generating WWVB timecodes
 * wwvb.decode, a generator-based state machine for decoding WWVB timecodes (amplitude modulation only)
 * wwvb.tzinfo_us, an implementation of the US DST rules adapted from the Python doc examples.  tzinfo_us is an implementation detail and may change.
 * uwwvb, a version of the decoder intended for use on constrained environments such as [CircuitPython](https://circuitpython.org).

# Development status

The author (@jepler) occasionally develops and maintains this project, but
issues and pull requests are not likely to be acted on.  They would be
interested in adding co-maintainer(s).


# WWVB Timecodes
The National Institute of Standards and Technology operates the WWVB time
signal service near Fort Collins, Colorado.  The signal can be received in most
of the continental US.  Each minute, the signal transmits the current time,
including information about leap years, daylight saving time, and leap seconds.
The signal is composed of an amplitude channel and a phase modulation channel.

The amplitude channel can be visualized as a sequence of (usually) 60 symbols,
which by default wwvbgen displays as 0, 1, or 2.  The 0s and 1s encode
information like the current day of the year, while the 2s appear in fixed
locations to allow a receiver to determine the start of a minute.

The phase channel (which is displayed with `--channel=phase` or
`--channel=both`) consists of the same number of symbols per minute.  This
channel is substantially more complicated than the phase channel.  It encodes
the current time as minute-of-the-century, provides extended DST information,
and includes error-correction information not available in the amplitude
channel.

# Usage

~~~~
Usage: wwvbgen.py [options] [dateutil-string | year yday hour minute | year month day hour minute]

Options:
  -h, --help            show this help message and exit
  -i, --iers            use IERS data for DUT1 and LS [Default]
  -I, --no-iers         do not use IERS data for DUT1 and LS
  -s, --leap-second     force a leap second  [Implies --no-iers]
  -S, --no-leap-second  force no leap second [Implies --no-iers]
  -d DUT1, --dut1=DUT1  force dut1           [Implies --no-iers]
  -m MINUTES, --minutes=MINUTES
                        number of minutes to generate [Default: 10]
  --style=STYLE         Style of output (one of: default, duration, cradek,
                        bar)
  --channel=MODULATION  Modulation (amplitude, phase, both) to print
~~~~

For example, to display the leap second that occurred at the end of 1998,
~~~~
$ python wwvbgen.py -m 7 1998 365 23 56
WWVB timecode: year=98 days=365 hour=23 min=56 dst=0 ut1=-300 ly=0 ls=1
'98+365 23:56  210100110200100001120011001102010100010200110100121000001002
'98+365 23:57  210100111200100001120011001102010100010200110100121000001002
'98+365 23:58  210101000200100001120011001102010100010200110100121000001002
'98+365 23:59  2101010012001000011200110011020101000102001101001210000010022
'99+001 00:00  200000000200000000020000000002000100101201110100121001000002
'99+001 00:01  200000001200000000020000000002000100101201110100121001000002
'99+001 00:02  200000010200000000020000000002000100101201110100121001000002
~~~~
(the leap second is the extra digit at the end of the 23:59 line; that minute
consists of 61 seconds, instead of the normal 60)


# How wwvbpy handles DUT1 data

wwvbpy stores a compact representation of DUT1 values in `iersdata.py`.
In this representation, one value is used for one day (0000UTC through 2359UTC).
The letters `a` through `u` represent offsets of -1.0s through +1.0s
in 0.1s increments; `k` represents 0s.  (In practice, only a smaller range
of values, typically -0.7s to +0.8s, is seen)

For 2001 through present, NIST has published the actual DUT1 values broadcast,
and the date of each change, though it in the format of an HTML
table and not designed for machine readability:

https://www.nist.gov/pml/time-and-frequency-division/atomic-standards/leap-second-and-ut1-utc-information

NIST does not update the value daily and does not seem to follow any
specific rounding rule.  Rather, in WWVB "the resolution of the DUT1
correction is 0.1 s, and represents an average value for an extended
range of dates. Therefore, it will not agree exactly with the weekly
UT1-UTC(NIST) values shown in the earlier table, which have 1 ms
resolution and are updated weekly."  Like wwvbpy's compact
representation of DUT1 values, the real WWVB does not appear to ever
broadcast DUT1=-0.0.

For a larger range of dates spanning 1973 through approximately one year from
now, IERS publishes historical and prospective UT1-UTC values to multiple
decimal places, in a machine readable fixed length format.

wwvbpy merges the WWVB and IERS datasets, favoring the WWVB dataset for
dates when it is available.

The process for updating `iersdata.py` is intended to be executed monthly from
github actions.  You can also do it manually:
 * remove the cached `iersdata.txt` and `wwvbdata.html` files to get fresh data
 * run `python3 iers2py.py`
 * gut check the iersdata.py file, commit, and push it out.

Leap seconds are inferred from the DUT1 data as follows: If X and Y are the
1-digit-rounded DUT1 values for consecutive dates, and `X*Y<0`, then there is a
leap second at the end of day X.  The direction of the leap second can be
inferred from the sign of X, a positive leap second if X is positive.  As long
as DUT1 changes slowly enough during other times that there is at least one day
of DUT1=+0.0, no incorrect (negative) leapsecond will be inferred. (something
that should remain true for the next few centuries, until the length of the day
is 100ms less than 86400 seconds)


# The phase modulation channel

This should be considered more experimental than the AM channel, as the
tests only cover a single reference minute.  Further tests could be informed
by the [other implementation I know of](http://www.leapsecond.com/tools/wwvb_pm.c), except that implementation appears incomplete.


# Testing wwvbpy

Run the testsuite with `python3 -munittest`.  There are several test suites:
 * `testwwvb.py`: Check output against expected values.  Uses hard coded leap seconds.  Tests amplitude and phase data, though the phase testcases are dubious as they were also generated by wwvbpy.
 * `testuwwvb.py`: Test the reduced-functionality version against the main version
 * `testls.py`: Check the IERS data through 2020-1-1 for expected leap seconds
 * `testpm.py`: Check the phase modulation data against a test case from NIST documentation

A script `printls.py` prints all leap seconds represented in `iersdata.py`.
Verification of this data is manual.
