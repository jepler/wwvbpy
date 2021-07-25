#!/usr/bin/python3
"""A command-line program for generating wwvb timecodes"""

# Copyright (C) 2011-2020 Jeff Epler <jepler@gmail.com>
# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

import datetime
import sys
import click

import dateutil.parser

from . import (
    print_timecodes,
    WWVBMinute,
    WWVBMinuteIERS,
    styles,
)


def parse_timespec(ctx, param, value):  # pylint: disable=unused-argument
    """Parse a time specifier from the commandline"""
    try:
        if len(value) == 5:
            year, month, day, hour, minute = map(int, value)
            return datetime.datetime(year, month, day, hour, minute)
        if len(value) == 4:
            year, yday, hour, minute = map(int, value)
            return datetime.datetime(year, 1, 1, hour, minute) + datetime.timedelta(
                days=yday
            )
        if len(value) == 1:
            return dateutil.parser.parse(value[0])
        if len(value) == 0:
            return datetime.datetime.utcnow()
        raise ValueError("Unexpected number of arguments")
    except ValueError as e:
        raise click.UsageError(f"Could not parse timespec: {e}") from e
    return value


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
    "--all-timecodes/--no-all-timecodes",
    "-t/-T",
    default=False,
    type=bool,
    help="Show the 'WWVB timecode' line before each minute",
)
@click.option(
    "--channel",
    type=click.Choice(["amplitude", "phase", "both"]),
    default="amplitude",
    help="Modulation to show (default: amplitude)",
)
@click.argument("timespec", type=str, nargs=-1, callback=parse_timespec)
# pylint: disable=too-many-arguments, too-many-locals
def main(iers, leap_second, dut1, minutes, style, channel, all_timecodes, timespec):
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

    if timespec is None:
        timespec = datetime.datetime.utcnow()

    w = Constructor.from_datetime(timespec, **extra_args)
    print_timecodes(
        w, minutes, channel, style, all_timecodes=all_timecodes, file=sys.stdout
    )


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
