# -*- python3 -*-
"""Retrieve iers data, possibly from user or site data or from the wwvbpy distribution"""

# SPDX-FileCopyrightText: 2011-2024 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

import binascii
import datetime
import gzip
import importlib.resources
import json

import platformdirs

__all__ = ["DUT1_DATA_START", "DUT1_OFFSETS", "end", "span", "start"]

content: dict[str, str] = {"START": "1970-01-01", "OFFSETS_GZ": "H4sIAFNx1mYC/wMAAAAAAAAAAAA="}

path = importlib.resources.files("wwvb") / "iersdata.json"
content = json.loads(path.read_text(encoding="utf-8"))

for location in [  # pragma no cover
    platformdirs.user_data_path("wwvbpy", "unpythonic.net"),
    platformdirs.site_data_path("wwvbpy", "unpythonic.net"),
]:
    path = location / "iersdata.json"
    if path.exists():
        content = json.loads(path.read_text(encoding="utf-8"))
        break

DUT1_DATA_START = datetime.date.fromisoformat(content["START"])
DUT1_OFFSETS = gzip.decompress(binascii.a2b_base64(content["OFFSETS_GZ"])).decode("ascii")

start = datetime.datetime.combine(DUT1_DATA_START, datetime.time(), tzinfo=datetime.timezone.utc)
span = datetime.timedelta(days=len(DUT1_OFFSETS))
end = start + span
