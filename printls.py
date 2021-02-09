#!/usr/bin/python3

# Copyright (C) 2012-2020 Jeff Epler <jepler@gmail.com>
# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-or-later

import wwvbgen
import datetime
import iersdata

d = iersdata.dut1_data_start
e = d + datetime.timedelta(len(iersdata.dut1_offsets))
while d < e:
    if wwvbgen.isls(d):
        sense = wwvbgen.get_dut1(d) > 0
        print(
            "%s leap second in %s"
            % (("positive", "negative")[sense], d.strftime("%b %Y"))
        )
    m = d.utctimetuple().tm_mon
    while d.utctimetuple().tm_mon == m:
        d += datetime.timedelta(1)
