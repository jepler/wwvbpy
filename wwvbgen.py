#!/usr/bin/python3

# Copyright (C) 2011-2020 Jeff Epler <jepler@gmail.com>
# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-or-later

import datetime
import sys

from wwvblib import (
    print_timecodes,
    WWVBMinute,
    WWVBMinuteIERS,
    styles,
)

if __name__ == "__main__":  # pragma no cover
    import optparse  # pylint: disable=deprecated-module

    parser = optparse.OptionParser(
        usage="Usage: %prog [options] [year yday hour minute | year month day hour minute]"
    )
    parser.add_option(
        "-i",
        "--iers",
        dest="iers",
        help="use IERS data for DUT1 and LS [Default]",
        action="store_true",
        default=True,
    )
    parser.add_option(
        "-I",
        "--no-iers",
        dest="iers",
        help="do not use IERS data for DUT1 and LS",
        action="store_false",
    )
    parser.add_option(
        "-s",
        "--leap-second",
        dest="forcels",
        help="force a leap second  [Implies --no-iers]",
        action="store_true",
        default=None,
    )
    parser.add_option(
        "-S",
        "--no-leap-second",
        dest="forcels",
        help="force no leap second [Implies --no-iers]",
        action="store_false",
    )
    parser.add_option(
        "-d",
        "--dut1",
        dest="forcedut1",
        help="force dut1           [Implies --no-iers]",
        metavar="DUT1",
        default=None,
    )
    parser.add_option(
        "-m",
        "--minutes",
        dest="minutes",
        help="number of minutes to generate [Default: 10]",
        metavar="MINUTES",
        type="int",
        default=10,
    )
    parser.add_option(
        "--style",
        dest="style",
        help="Style of output (one of: %s)" % ", ".join(styles.keys()),
        metavar="STYLE",
        type="str",
        default="default",
    )
    parser.add_option(
        "--channel",
        dest="channel",
        help="Modulation (amplitude, phase, both) to print",
        metavar="MODULATION",
        type="str",
        default="amplitude",
    )
    options, args = parser.parse_args()

    extra_args = {}
    if options.iers and options.forcedut1 is None and options.forcels is None:
        constructor = WWVBMinuteIERS
    else:  # pragma no coverage
        constructor = WWVBMinute
        if options.forcedut1 is None:
            extra_args["ut1"] = -500 if options.forcels else 0
        else:
            extra_args["ut1"] = options.forcedut1
        extra_args["ls"] = options.forcels

    if args:
        if len(args) == 4:
            try:
                year, yday, hour, minute = map(int, args)
            except ValueError as e:
                parser.print_help()
                raise SystemExit("Arguments must be numeric") from e
            parser.print_help()
        elif len(args) == 5:
            try:
                year, month, day, hour, minute = map(int, args)
            except ValueError as e:
                parser.print_help()
                raise SystemExit("Arguments must be numeric") from e
            yday = datetime.datetime(year, month, day, 0, 0).timetuple().tm_yday
        else:
            parser.print_help()
            raise SystemExit("Expected 4 or 5 arguments, got %d" % len(args))
    else:
        now = datetime.datetime.utcnow().utctimetuple()
        year, yday, hour, minute = now.tm_year, now.tm_yday, now.tm_hour, now.tm_min

    w = constructor(year, yday, hour, minute, **extra_args)
    print_timecodes(w, options.minutes, options.channel, options.style, file=sys.stdout)
