"""Retrieve 'bulletin D' data"""

import json
import os
import xml.etree.ElementTree

import requests
import bs4
import platformdirs

# Copyright (C) 2011-2020 Jeff Epler <jepler@gmail.com>
# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

BULLETIN_D_INDEX = "https://datacenter.iers.org/availableVersions.php?id=17"

cache_path = platformdirs.user_cache_path(appname="wwvbpy")


def cache(url):
    """Download a specific Bulletin & cache it in json format"""
    base = url.split("/")[-1].split(".")[0]
    loc = os.path.join(cache_path, base) + ".json"

    if not os.path.exists(loc):
        print(f"Fetching {url} to {loc}")
        buld_xml = requests.get(url).text
        doc = xml.etree.ElementTree.XML(buld_xml)
        d = {
            "startDate": doc.find(
                ".//{http://www.iers.org/2003/schema/iers}startDate"
            ).text,
            "dut1": float(
                doc.find(".//{http://www.iers.org/2003/schema/iers}DUT1").text
            ),
        }
        with open(loc + ".tmp", "wt", encoding="utf-8") as f:
            json.dump(d, f)

        os.rename(loc + ".tmp", loc)

    with open(loc, "r", encoding="utf-8") as f:
        return json.load(f)


def get_bulletin_d_data():
    """Return all available Bulletin D data"""
    os.makedirs(cache_path, exist_ok=True)

    buld_text = requests.get(BULLETIN_D_INDEX).text
    buld_data = bs4.BeautifulSoup(buld_text, features="html.parser")
    refs = buld_data.findAll(lambda tag: "xml" in tag.get("href", ""))

    return [cache(r["href"]) for r in refs]


if __name__ == "__main__":
    data = get_bulletin_d_data()
    print(data)
