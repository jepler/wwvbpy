#!/usr/bin/python3

# Copyright (C) 2011-2020 Jeff Epler <jepler@gmail.com>
# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Update the content of 'iersdata.py' based on online sources"""

import datetime
import itertools
import os
import bs4
import requests

IERS_URL = (
    "https://datacenter.iers.org/data/latestVersion/9_FINALS.ALL_IAU2000_V2013_019.txt"
)
NIST_URL = "https://www.nist.gov/pml/time-and-frequency-division/atomic-standards/leap-second-and-ut1-utc-information"


def get_url_with_cache(url, cache):
    """Fetch the content of a URL, storing it in a cache"""
    if not os.path.exists(cache):
        with requests.get(url) as f:
            text = f.text
        with open(cache, "w") as f:
            f.write(text)
    else:
        with open(cache, "r") as f:
            text = f.read()
    return text


def main():  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    """Update iersdata.py"""
    iers_text = get_url_with_cache(IERS_URL, "iersdata.txt")
    rows = iers_text.strip().split("\n")
    assert len(rows) > 100

    wwvb_text = get_url_with_cache(NIST_URL, "wwvbdata.html")
    wwvb_data = bs4.BeautifulSoup(wwvb_text, features="html.parser")
    wwvb_dut1_table = wwvb_data.findAll("table")[2]
    assert wwvb_dut1_table
    wwvb_data_stamp = datetime.datetime.fromisoformat(
        wwvb_data.find("meta", property="article:modified_time").attrs["content"]
    ).replace(tzinfo=None)

    offsets = []
    for r in rows:
        if len(r) < 69:
            continue
        if r[57] not in "IP":
            continue
        jd = float(r[7:12])
        offs = int(round(float(r[58:68]) * 10))
        if not offsets:
            start = datetime.datetime(1858, 11, 17) + datetime.timedelta(jd)
        offsets.append(offs)

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

    # this is the final (most recent) wwvb DUT1 value broadcast.  We want to
    # extend it some distance into the future, but how far?  We will use the
    # modified timestamp of the NIST data.

    off = wwvb_off
    while off < (wwvb_data_stamp - start).days:
        offsets[off] = wwvb_dut1
        off += 1

    with open("iersdata.py", "wt") as output:

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
