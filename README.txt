Purpose
=======

wwvbgen generates WWVB timecodes for any desired time.  These timecodes
may be useful intesting WWVB decoder software.

Where possible, wwvbgen uses existing facilities for calendar and time
manipulation (datetime) and DST rules (time.localtime).  It uses DUT1/leap
second data derived from IERS Bulletin "A".  With regular updates to
iersdata.py, wwvbgen should be able to correctly encode the time anywhere
within the 100-year WWVB epoch.  (yes, WWVB uses a 2-digit year!)


WWVB Timecodes
==============
The National Institute of Standards and Technology operates the WWVB time
signal service near Fort Collins, Colorado.  The signal can be received in most
of the continental US.  Every minute seconds, the signal transmits the current
time, including information about leap years, daylight saving time, and leap
seconds.  The signal can be visualized as a sequence of (usually) 60 symbols,
which wwvbgen displays as 0, 1, or 2.  The 0s and 1s encode information like
the current day of the year, while the 2s appear in fixed locations to allow a
receiver to determine the start of a minute.


Usage
=====
    Usage: wwvbgen.py [options] [year yday hour minute]

    Options:
      -h, --help            show this help message and exit
      -i, --iers            use IERS data for DUT1 and LS [Default]
      -I, --no-iers         do not use IERS data for DUT1 and LS
      -m MINUTES, --minutes=MINUTES
                            number of minutes to generate [Default: 10]

For example, to display the leap second that occurred at the end of 1998,
    $ python wwvbgen.py -m 7 1998 365 23 56
    WWVB timecode: year=98 days=365 hour=23 min=56 dst=0 ut1=-300 ly=0 ls=1
    '98+365 23:56  210100110200100001120011001102010100010200110100121000001002
    '98+365 23:57  210100111200100001120011001102010100010200110100121000001002
    '98+365 23:58  210101000200100001120011001102010100010200110100121000001002
    '98+365 23:59  2101010012001000011200110011020101000102001101001210000010022
    '99+001 00:00  200000000200000000020000000002000100101201110100121001000002
    '99+001 00:01  200000001200000000020000000002000100101201110100121001000002
    '99+001 00:02  200000010200000000020000000002000100101201110100121001000002
(the leap second is the extra digit at the end of the 23:59 line; that minute
consists of 61 seconds, instead of the normal 60)


Updating DUT1 data
==================

This program can get updated DUT1 data from a US Government-operated website.
If the details of this website's operation have not changed, the current
information can be retrieved by running the shell script `get-iers.sh` and
transformed into the compact representation `iersdata.py` by running
`iers2py.py > iersdata.py`.  `iersdata.py` has correctly-rounded data
for every day of IERS data retrieved.  For |UT1-UTC| < 0.05, it stores
+0.0, not the actual sign of UT1-UTC.

When invoked, `get-iers.sh` requests data for 1980 through the end of the
current year.  Reportedly, IERS "Bulletin A" DUT1 estimates are available
through 1 year from the current date.

NIST does not update the value daily and does not seem to follow any
specific rounding rule.  Rather, in WWVB "the resolution of the DUT1
correction is 0.1 s, and represents an average value for an extended
range of dates. Therefore, it will not agree exactly with the weekly
UT1-UTC(NIST) values shown in the earlier table, which have 1 ms
resolution and are updated weekly."  Like wwvbpy's compact
representation of DUT1 values, the real WWVB does not appear to ever
broadcast DUT1=-0.0.

http://www.nist.gov/pml/div688/grp50/leapsecond.cfm

Leap seconds are inferred from the UERS UT1-UTC data as follows: If X
and Y are the 1-digit-rounded DUT1 values for consecutive dates, and
X*Y<0, then there is a leap second at the end of day X.  The direction of
the leap second can be inferred from the sign of X, a positive leap
second if X is positive.  As long as DUT1 changes slowly enough during
other times that there is at least one day of DUT1=+0.0, no incorrect
(negative) leapsecond will be inferred. (something that should remain
true for the next few centuries, until the length of the day is 100ms
less than 86400 seconds)


Testing wwvbgen
===============

A set of test timecodes, generated with another WWVB timecode generator,
are in tests/.  To run the automatic self test (which does not use or
test IERS DUT1 data), `python wwvbtest.py`.
