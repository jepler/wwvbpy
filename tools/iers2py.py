#!/usr/bin/python3

# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

"""Update the content of 'iersdata.py' based on online sources"""

import csv
import datetime
import itertools
import os
import bs4
import requests

IERS_URL = "https://datacenter.iers.org/data/csv/finals2000A.all.csv"
NIST_URL = "https://www.nist.gov/pml/time-and-frequency-division/atomic-standards/leap-second-and-ut1-utc-information"


def open_url_with_cache(url, cache):
    """Fetch the content of a URL, storing it in a cache, returning it as a file"""
    if not os.path.exists(cache):
        with requests.get(url) as f:
            text = f.text
        with open(cache, "w") as f:
            f.write(text)
    return open(cache, "r")  # pylint: disable=consider-using-with


def read_url_with_cache(url, cache):
    """Read the content of a URL, returning it as a string"""
    with open_url_with_cache(url, cache) as f:
        return f.read()


def main():  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    """Update iersdata.py"""

    offsets = []
    with open_url_with_cache(IERS_URL, "iersdata.csv") as iers_data:
        for r in csv.DictReader(iers_data, delimiter=";"):
            jd = float(r["MJD"])
            offs_str = r["UT1-UTC"]
            if not offs_str:
                break
            offs = int(round(float(offs_str) * 10))
            if not offsets:
                start = datetime.datetime(1858, 11, 17) + datetime.timedelta(jd)
            offsets.append(offs)

    wwvb_text = read_url_with_cache(NIST_URL, "wwvbdata.html")
    wwvb_data = bs4.BeautifulSoup(wwvb_text, features="html.parser")
    wwvb_dut1_table = wwvb_data.findAll("table")[2]
    assert wwvb_dut1_table
    wwvb_data_stamp = datetime.datetime.fromisoformat(
        wwvb_data.find("meta", property="article:modified_time").attrs["content"]
    ).replace(tzinfo=None)

    def patch(patch_start, patch_end, val):
        off_start = (patch_start - start).days
        off_end = (patch_end - start).days
        offsets[off_start:off_end] = [val] * (off_end - off_start)

    wwvb_dut1 = None
    wwvb_off = None
    for row in wwvb_dut1_table.findAll("tr")[1:][::-1]:
        cells = row.findAll("td")
        when = datetime.datetime.strptime(cells[0].text, "%Y-%m-%d")
        dut1 = cells[2].text.replace("s", "").replace(" ", "")
        dut1 = int(round(float(dut1) * 10))
        off = (when - start).days
        if wwvb_dut1 is not None:
            offsets[wwvb_off:off] = [wwvb_dut1] * (off - wwvb_off)
        wwvb_dut1 = dut1
        wwvb_off = off

    # As of 2021-06-14, NIST website incorrectly indicates the offset of -600ms
    # persisted through 2009-03-12, causing an incorrect leap second inference.
    # Assume instead that NIST started broadcasting +400ms on January 1, 2009,
    # causing the leap second to occur on 2008-12-31.
    patch(datetime.datetime(2009, 1, 1), datetime.datetime(2009, 3, 12), 4)

    # this is the final (most recent) wwvb DUT1 value broadcast.  We want to
    # extend it some distance into the future, but how far?  We will use the
    # modified timestamp of the NIST data.

    off = wwvb_off
    while off < (wwvb_data_stamp - start).days:
        offsets[off] = wwvb_dut1
        off += 1

    with open("wwvb/iersdata.py", "wt") as output:

        def code(*args):
            """Print to the output file"""
            print(*args, file=output)

        code("# -*- python3 -*-")
        code('"""File generated from public data - not subject to copyright"""')
        code("# SPDX" "-FileCopyrightText: Public domain")
        code("# SPDX" "-License-Identifier: CC0-1.0")
        code("# fmt: off")
        code("# pylint: disable=invalid-name")
        code("import datetime")

        code("__all__ = ['DUT1_DATA_START', 'DUT1_OFFSETS']")
        code("DUT1_DATA_START = %r" % start)
        c = sorted(chr(ord("a") + ch + 10) for ch in set(offsets))
        code("%s = '%s'" % (",".join(c), "".join(c)))
        code(
            "DUT1_OFFSETS = str( # %04d%02d%02d" % (start.year, start.month, start.day)
        )
        line = ""
        j = 0

        for ch, it in itertools.groupby(offsets):
            part = ""
            ch = chr(ord("a") + ch + 10)
            sz = len(list(it))
            if j:
                part = part + "+"
            if sz < 2:
                part = part + "%s" % ch
            else:
                part = part + "%s*%d" % (ch, sz)
            j += sz
            if len(line + part) > 60:
                d = start + datetime.timedelta(j - 1)
                code("    %-60s # %04d%02d%02d" % (line, d.year, d.month, d.day))
                line = part
            else:
                line = line + part
        d = start + datetime.timedelta(j - 1)
        code("    %-60s # %04d%02d%02d" % (line, d.year, d.month, d.day))
        code(")")


if __name__ == "__main__":
    main()
