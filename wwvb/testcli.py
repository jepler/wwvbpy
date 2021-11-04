#!/usr/bin/python3
"""Test most wwvblib commandline programs"""

# Copyright (C) 2011-2020 Jeff Epler <jepler@gmail.com>
# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

# pylint: disable=invalid-name

import os
import sys
import subprocess
import unittest

coverage_add = (
    ("-m", "coverage", "run", "--branch", "-p") if "COVERAGE_RUN" in os.environ else ()
)


class CLITestCase(unittest.TestCase):
    """Test various CLI commands within wwvbpy"""

    def assertProgramOutput(self, expected: str, *args: str) -> None:
        """Check the output from invoking a program matches the expected"""
        actual = subprocess.check_output(
            args, stdin=subprocess.DEVNULL, encoding="utf-8"
        )
        self.assertMultiLineEqual(expected, actual, "args={args}")

    def assertModuleOutput(self, expected: str, *args: str) -> None:
        """Check the output from invoking a `python -m modulename` program matches the expected"""
        return self.assertProgramOutput(
            expected, sys.executable, *coverage_add, "-m", *args
        )

    def assertProgramError(self, *args: str) -> None:
        """Check the output from invoking a program fails"""
        with self.assertRaises(subprocess.SubprocessError):
            subprocess.check_output(
                args,
                stdin=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                encoding="utf-8",
            )

    def assertModuleError(self, *args: str) -> None:
        """Check the output from invoking a `python -m modulename` program fails"""
        return self.assertProgramError(sys.executable, *coverage_add, "-m", *args)

    def test_gen(self) -> None:
        """test wwvb.gen"""
        self.assertModuleOutput(
            """\
WWVB timecode: year=2020 days=001 hour=12 min=30 dst=0 ut1=-200 ly=1 ls=0
2020-001 12:30  201100000200010001020000000002000100010200100001020000010002
""",
            "wwvb.gen",
            "-m",
            "1",
            "2020-1-1 12:30",
        )

        self.assertModuleOutput(
            """\
WWVB timecode: year=2020 days=001 hour=12 min=30 dst=0 ut1=-200 ly=1 ls=0
2020-001 12:30  201100000200010001020000000002000100010200100001020000010002
""",
            "wwvb.gen",
            "-m",
            "1",
            "2020",
            "1",
            "12",
            "30",
        )

        self.assertModuleOutput(
            """\
WWVB timecode: year=2020 days=001 hour=12 min=30 dst=0 ut1=-200 ly=1 ls=0
2020-001 12:30  201100000200010001020000000002000100010200100001020000010002
""",
            "wwvb.gen",
            "-m",
            "1",
            "2020",
            "1",
            "1",
            "12",
            "30",
        )

        self.assertModuleError("wwvb.gen", "-m", "1", "2021", "7")

        # Asserting a leap second
        self.assertModuleOutput(
            """\
WWVB timecode: year=2020 days=001 hour=12 min=30 dst=0 ut1=-500 ly=1 ls=1
2020-001 12:30  201100000200010001020000000002000100010201010001020000011002
""",
            "wwvb.gen",
            "-m",
            "1",
            "-s",
            "2020-1-1 12:30",
        )

        # Asserting a different ut1 value
        self.assertModuleOutput(
            """\
WWVB timecode: year=2020 days=001 hour=12 min=30 dst=0 ut1=-300 ly=1 ls=0
2020-001 12:30  201100000200010001020000000002000100010200110001020000010002
""",
            "wwvb.gen",
            "-m",
            "1",
            "-d",
            "-300",
            "2020-1-1 12:30",
        )
