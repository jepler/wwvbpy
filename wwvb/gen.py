#!/usr/bin/python3
"""A command-line program for generating wwvb timecodes"""

# Copyright (C) 2011-2020 Jeff Epler <jepler@gmail.com>
# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

import datetime
import sys
import click

from . import (
    print_timecodes,
    WWVBMinute,
    WWVBMinuteIERS,
    styles,
)


@click.command()
@click.option(
    "--iers/--no-iers",
    "-i/-I",
    default=True,
    help="Whether to use IESR data for DUT1 and LS.  (Default: --iers)",
)
@click.option(
    "--leap-second",
    "-s",
    "leap_second",
    flag_value=1,
    default=None,
    help="Force a positive leap second at the end of the GMT month (Implies --no-iers)",
)
@click.option(
    "--negative-leap-second",
    "-n",
    "leap_second",
    flag_value=-1,
    help="Force a negative leap second at the end of the GMT month (Implies --no-iers)",
)
@click.option(
    "--no-leap-second",
    "-S",
    "leap_second",
    flag_value=0,
    help="Force no leap second at the end of the month (Implies --no-iers)",
)
@click.option("--dut1", "-d", type=int, help="Force the DUT1 value (Implies --no-iers)")
@click.option(
    "--minutes", "-m", default=10, help="Number of minutes to show (default: 10)"
)
@click.option(
    "--style",
    default="default",
    type=click.Choice(styles.keys()),
    help="Style of output",
)
@click.option(
    "--channel",
    type=click.Choice(["amplitude", "phase", "both"]),
    default="amplitude",
    help="Modulation to show (default: amplitude)",
)
@click.argument("timespec", type=int, nargs=-1)
# pylint: disable=too-many-arguments, too-many-locals
def main(iers, leap_second, dut1, minutes, style, channel, timespec):
    """Generate WWVB timecodes

    TIMESPEC: one of "year yday hour minute" or "year month day hour minute", or else the current minute"""

    if (leap_second is not None) or (dut1 is not None):
        iers = False

    extra_args = {}
    if iers:
        Constructor = WWVBMinuteIERS
    else:
        Constructor = WWVBMinute
        if dut1 is None:
            extra_args["ut1"] = -500 * (leap_second or 0)
        else:
            extra_args["ut1"] = dut1
        extra_args["ls"] = bool(leap_second)

    if timespec:
        if len(timespec) == 4:
            year, yday, hour, minute = timespec
        elif len(timespec) == 5:
            year, month, day, hour, minute = timespec
            yday = datetime.datetime(year, month, day, 0, 0).timetuple().tm_yday
        else:  # pragma no cover
            raise click.UsageError("Expected 4 or 5 arguments, got %d" % len(timespec))
    else:
        now = datetime.datetime.utcnow().utctimetuple()
        year, yday, hour, minute = now.tm_year, now.tm_yday, now.tm_hour, now.tm_min

    w = Constructor(year, yday, hour, minute, **extra_args)
    print_timecodes(w, minutes, channel, style, file=sys.stdout)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
