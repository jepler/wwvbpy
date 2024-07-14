#!/usr/bin/python3
"""Test Phase Modulation Signal"""

# SPDX-FileCopyrightText: 2021-2024 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

import unittest

import wwvb


class TestPhaseModulation(unittest.TestCase):
    """Test Phase Modulation Signal"""

    def test_pm(self) -> None:
        """Compare the generated signal from a reference minute in NIST docs"""
        ref_am = "201100000200010011120001010002011000101201000000120010010112"

        ref_pm = "001110110100010010000011001000011000110100110100010110110110"

        ref_minute = wwvb.WWVBMinuteIERS(2012, 186, 17, 30, dst=3)
        ref_time = ref_minute.as_timecode()

        test_am = ref_time.to_am_string(["0", "1", "2"])
        test_pm = ref_time.to_pm_string(["0", "1"])

        self.assertEqual(ref_am, test_am)
        self.assertEqual(ref_pm, test_pm)


if __name__ == "__main__":
    unittest.main()
