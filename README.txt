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

This program gets DUT1 data from a website in a HTML format.  If the details of
this website's operation have not changed, the current information can be
retrieved by runnin the shell script `get-iers.sh` and transformed into the
compact representation `iersdata.py` by running `iers2py.py > iersdata.py`.

When invoked, `get-iers.sh` requests data for 1980 through the end of the
current year.  Reportedly, IERS "Bulletin A" DUT1 estimates are available
for 1 year from the current date.


Testing wwvbgen
===============

A set of test timecodes, generated with another WWVB timecode generator,
are in tests/.  To run the automatic self test (which does not test IERS
data), `python wwvbtest.py`.
