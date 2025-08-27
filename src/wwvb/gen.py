#!/usr/bin/python3
"""A command-line program for generating wwvb timecodes"""

# SPDX-FileCopyrightText: 2011-2024 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import datetime
import sys

import click
import dateutil.parser

from . import WWVBMinute, WWVBMinuteIERS, print_timecodes, print_timecodes_json, styles

TYPE_CHECKING = False
if TYPE_CHECKING:
    from . import WWVBChannel


def parse_timespec(ctx: click.Context, param: click.Parameter, value: list[str]) -> datetime.datetime:  # noqa: ARG001
    """Parse a time specifier from the commandline"""
    try:
        if len(value) == 5:
            year, month, day, hour, minute = map(int, value)
            return datetime.datetime(year, month, day, hour, minute, tzinfo=datetime.timezone.utc)
        if len(value) == 4:
            year, yday, hour, minute = map(int, value)
            return datetime.datetime(year, 1, 1, hour, minute, tzinfo=datetime.timezone.utc) + datetime.timedelta(
                days=yday - 1,
            )
        if len(value) == 1:
            return dateutil.parser.parse(value[0])
        if len(value) == 0:
            return datetime.datetime.now(datetime.timezone.utc)
        raise ValueError("Unexpected number of arguments")
    except ValueError as e:
        raise click.UsageError(f"Could not parse timespec: {e}") from e


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
@click.option("--minutes", "-m", default=10, help="Number of minutes to show (default: 10)")
@click.option(
    "--style",
    default="default",
    type=click.Choice(sorted(["json", *list(styles.keys())])),
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
def main(
    *,
    iers: bool,
    leap_second: bool,
    dut1: int,
    minutes: int,
    style: str,
    channel: WWVBChannel,
    all_timecodes: bool,
    timespec: datetime.datetime,
) -> None:
    """Generate WWVB timecodes

    TIMESPEC: one of "year yday hour minute" or "year month day hour minute", or else the current minute
    """
    if (leap_second is not None) or (dut1 is not None):
        iers = False

    newut1 = None
    newls = None

    if iers:
        constructor: type[WWVBMinute] = WWVBMinuteIERS
    else:
        constructor = WWVBMinute
        newut1 = -500 * (leap_second or 0) if dut1 is None else dut1
        newls = bool(leap_second)

    w = constructor.from_datetime(timespec, newls=newls, newut1=newut1)
    if style == "json":
        print_timecodes_json(w, minutes, channel, file=sys.stdout)
    else:
        print_timecodes(w, minutes, channel, style, all_timecodes=all_timecodes, file=sys.stdout)


if __name__ == "__main__":
    main()
