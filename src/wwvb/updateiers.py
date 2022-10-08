#!/usr/bin/python3

# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

"""Update the DUT1 and LS data based on online sources"""

import csv
import datetime
import io
import itertools
import os
import pathlib
from typing import Callable, List, Optional

import bs4
import bulletind
import click
import platformdirs
import requests

DIST_PATH = str(pathlib.Path(__file__).parent / "iersdata_dist.py")

OLD_TABLE_START: Optional[datetime.date] = None
OLD_TABLE_END: Optional[datetime.date] = None
try:
    import wwvb.iersdata_dist

    OLD_TABLE_START = wwvb.iersdata_dist.DUT1_DATA_START
    OLD_TABLE_END = OLD_TABLE_START + datetime.timedelta(
        days=len(wwvb.iersdata_dist.DUT1_OFFSETS) - 1
    )
except (ImportError, NameError) as e:
    pass
IERS_URL = "https://datacenter.iers.org/data/csv/finals2000A.all.csv"


def update_iersdata(  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    target_file: str,
) -> None:
    """Update iersdata.py"""

    offsets: List[int] = []
    with requests.get(IERS_URL) as iers_data:
        for r in csv.DictReader(io.StringIO(iers_data.text), delimiter=";"):
            jd = float(r["MJD"])
            offs_str = r["UT1-UTC"]
            if not offs_str:
                break
            offs = int(round(float(offs_str) * 10))
            if not offsets:
                table_start = datetime.date(1858, 11, 17) + datetime.timedelta(jd)
                # If the table starts after June 1, 1972 (it does), add the 1972 leap second
                if table_start > datetime.date(1972, 6, 1):
                    when = datetime.date(1972, 6, 1)
                    while when < datetime.date(1972, 7, 1):
                        offsets.append(-2)
                        when = when + datetime.timedelta(days=1)
                    while when < table_start:
                        offsets.append(8)
                        when = when + datetime.timedelta(days=1)
                    table_start = datetime.date(1972, 6, 1)
            offsets.append(offs)

    def patch(patch_start: datetime.date, patch_end: datetime.date, val: int) -> None:
        off_start = (patch_start - table_start).days
        off_end = (patch_end - table_start).days
        offsets[off_start:off_end] = [val] * (off_end - off_start)

    wwvb_dut1: Optional[int] = None
    wwvb_start: Optional[datetime.date] = None
    for data in bulletind.get_cached_bulletin_d_data():
        when = data.start_date
        dut1 = round(10 * data.dut1)
        if wwvb_dut1 is not None:
            assert wwvb_start is not None
            patch(wwvb_start, when, wwvb_dut1)
        wwvb_dut1 = dut1
        wwvb_start = when

    # this is the final (most recent) Bulletin D DUT1 value specified.  We
    # might want to extend it some distance into the future, but how far?  The
    # textual Bulletin D says something like "Bulletin D 136 should be issued
    # in August 2017" or "Bulletin D 143 should be issued in 2023" but this is
    # not in the xml format and thus not in the data from the bulletind
    # package. Historically, bulletins have even been published AFTER their
    # effective date. As such, transition immediately back to the IERS Bulletin
    # A data immediately after the last Bulletin D data and do _NOT_ patch any
    # additonal days. This is in contrast to previous behavior, where the NIST
    # data was propagated until the reported modification date of the scraped
    # web page.

    with open(target_file, "wt", encoding="utf-8") as output:

        def code(*args: str) -> None:
            """Print to the output file"""
            print(*args, file=output)

        code("# -*- python3 -*-")
        code('"""File generated from public data - not subject to copyright"""')
        code("# SPDX" "-FileCopyrightText: Public domain")
        code("# SPDX" "-License-Identifier: CC0-1.0")
        code("# fmt: off")
        code("# isort: skip_file")
        code("# pylint: disable=invalid-name")
        code("import datetime")

        code("__all__ = ['DUT1_DATA_START', 'DUT1_OFFSETS']")
        code(f"DUT1_DATA_START = {repr(table_start)}")
        c = sorted(chr(ord("a") + ch + 10) for ch in set(offsets))
        code(f"{','.join(c)} = tuple({repr(''.join(c))})")
        code(
            f"DUT1_OFFSETS = str( # {table_start.year:04d}{table_start.month:02d}{table_start.day:02d}"
        )
        line = ""
        j = 0

        for val, it in itertools.groupby(offsets):
            part = ""
            ch = chr(ord("a") + val + 10)
            sz = len(list(it))
            if j:
                part = part + "+"
            if sz < 2:
                part = part + ch
            else:
                part = part + f"{ch}*{sz}"
            j += sz
            if len(line + part) > 60:
                d = table_start + datetime.timedelta(j - 1)
                code(f"    {line:<60s} # {d.year:04d}{d.month:02d}{d.day:02d}")
                line = part
            else:
                line = line + part
        d = table_start + datetime.timedelta(j - 1)
        code(f"    {line:<60s} # {d.year:04d}{d.month:02d}{d.day:02d}")
        code(")")
    table_end = table_start + datetime.timedelta(len(offsets) - 1)
    if OLD_TABLE_START:
        print(f"old iersdata covered {OLD_TABLE_START} .. {OLD_TABLE_END}")
    print(f"iersdata covers {table_start} .. {table_end}")


def iersdata_path(callback: Callable[[str, str], str]) -> str:
    """Find out the path for this directory"""
    return os.path.join(callback("wwvbpy", "unpythonic.net"), "wwvb_iersdata.py")


@click.command()
@click.option(
    "--user",
    "location",
    flag_value=iersdata_path(platformdirs.user_data_dir),
    default=iersdata_path(platformdirs.user_data_dir),
)
@click.option("--dist", "location", flag_value=DIST_PATH)
@click.option(
    "--site", "location", flag_value=iersdata_path(platformdirs.site_data_dir)
)
def main(location: str) -> None:
    """Update DUT1 data"""
    print("will write to", location)
    os.makedirs(os.path.dirname(location), exist_ok=True)
    update_iersdata(location)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
