#!/usr/bin/python3
"""Test most wwvblib commandline programs"""

# ruff: noqa: N802 D102
# SPDX-FileCopyrightText: 2021-2024 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

import json
import os
import subprocess
import sys
import unittest
from collections.abc import Sequence
from typing import Any

# These imports must remain, even though the module contents are not used directly!
import wwvb.dut1table
import wwvb.gen

# The asserts below are to help prevent their removal by a linter.
assert wwvb.dut1table.__name__ == "wwvb.dut1table"
assert wwvb.gen.__name__ == "wwvb.gen"

coverage_add = ("-m", "coverage", "run", "--branch", "-p") if "COVERAGE_RUN" in os.environ else ()


class CLITestCase(unittest.TestCase):
    """Test various CLI commands within wwvbpy"""

    def programOutput(self, *args: str) -> str:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        return subprocess.check_output(args, stdin=subprocess.DEVNULL, encoding="utf-8", env=env)

    def moduleArgs(self, *args: str) -> Sequence[str]:
        return (sys.executable, *coverage_add, "-m", *args)

    def moduleOutput(self, *args: str) -> str:
        return self.programOutput(sys.executable, *coverage_add, "-m", *args)

    def assertProgramOutput(self, expected: str, *args: str) -> None:
        """Check the output from invoking a program matches the expected"""
        actual = self.programOutput(*args)
        self.assertMultiLineEqual(expected, actual, f"args={args}")

    def assertProgramOutputStarts(self, expected: str, *args: str) -> None:
        """Check the output from invoking a program matches the expected"""
        actual = self.programOutput(*args)
        self.assertMultiLineEqual(expected, actual[: len(expected)], f"args={args}")

    def assertModuleOutput(self, expected: str, *args: str) -> None:
        """Check the output from invoking a `python -m modulename` program matches the expected"""
        actual = self.moduleOutput(*args)
        self.assertMultiLineEqual(expected, actual, f"args={args}")

    def assertStarts(self, expected: str, actual: str, *args: str) -> None:
        self.assertMultiLineEqual(expected, actual[: len(expected)], f"args={args}")

    def assertModuleJson(self, expected: Any, *args: str) -> None:
        """Check the output from invoking a `python -m modulename` program matches the expected"""
        actual = self.moduleOutput(*args)
        self.assertEqual(json.loads(actual), expected)

    def assertModuleOutputStarts(self, expected: str, *args: str) -> None:
        """Check the output from invoking a `python -m modulename` program matches the expected"""
        actual = self.moduleOutput(*args)
        self.assertStarts(expected, actual, *args)

    def assertProgramError(self, *args: str) -> None:
        """Check the output from invoking a program fails"""
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        with self.assertRaises(subprocess.SubprocessError):
            subprocess.check_output(
                args,
                stdin=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                encoding="utf-8",
                env=env,
            )

    def assertModuleError(self, *args: str) -> None:
        """Check the output from invoking a `python -m modulename` program fails"""
        self.assertProgramError(*self.moduleArgs(*args))

    def test_gen(self) -> None:
        """Test wwvb.gen"""
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

    def test_dut1table(self) -> None:
        """Test the dut1table program"""
        self.assertModuleOutputStarts(
            """\
1972-01-01 -0.2  182 LS on 1972-06-30 23:59:60 UTC
1972-07-01  0.8  123
1972-11-01  0.0   30
1972-12-01 -0.2   31 LS on 1972-12-31 23:59:60 UTC
""",
            "wwvb.dut1table",
        )

    def test_json(self) -> None:
        """Test the JSON output format"""
        self.assertModuleJson(
            [
                {
                    "year": 2021,
                    "days": 340,
                    "hour": 3,
                    "minute": 40,
                    "amplitude": "210000000200000001120011001002000000010200010001020001000002",
                    "phase": "111110011011010101000100100110011110001110111010111101001011",
                },
                {
                    "year": 2021,
                    "days": 340,
                    "hour": 3,
                    "minute": 41,
                    "amplitude": "210000001200000001120011001002000000010200010001020001000002",
                    "phase": "001010011100100011000101110000100001101000001111101100000010",
                },
            ],
            "wwvb.gen",
            "-m",
            "2",
            "--style",
            "json",
            "--channel",
            "both",
            "2021-12-6 3:40",
        )
        self.assertModuleJson(
            [
                {
                    "year": 2021,
                    "days": 340,
                    "hour": 3,
                    "minute": 40,
                    "amplitude": "210000000200000001120011001002000000010200010001020001000002",
                },
                {
                    "year": 2021,
                    "days": 340,
                    "hour": 3,
                    "minute": 41,
                    "amplitude": "210000001200000001120011001002000000010200010001020001000002",
                },
            ],
            "wwvb.gen",
            "-m",
            "2",
            "--style",
            "json",
            "--channel",
            "amplitude",
            "2021-12-6 3:40",
        )
        self.assertModuleJson(
            [
                {
                    "year": 2021,
                    "days": 340,
                    "hour": 3,
                    "minute": 40,
                    "phase": "111110011011010101000100100110011110001110111010111101001011",
                },
                {
                    "year": 2021,
                    "days": 340,
                    "hour": 3,
                    "minute": 41,
                    "phase": "001010011100100011000101110000100001101000001111101100000010",
                },
            ],
            "wwvb.gen",
            "-m",
            "2",
            "--style",
            "json",
            "--channel",
            "phase",
            "2021-12-6 3:40",
        )

    def test_sextant(self) -> None:
        """Test the sextant output format"""
        self.assertModuleOutput(
            """\
WWVB timecode: year=2021 days=340 hour=03 min=40 dst=0 ut1=-100 ly=0 ls=0 --style=sextant
2021-340 03:40  \
🬋🬩🬋🬹🬩🬹🬩🬹🬩🬹🬍🬎🬍🬎🬩🬹🬩🬹🬋🬍🬩🬹🬩🬹🬍🬎🬩🬹🬍🬎🬩🬹🬍🬎🬋🬹🬋🬎🬋🬍🬍🬎🬩🬹🬋🬎🬋🬎🬩🬹🬍🬎🬋🬎🬩🬹🬩🬹🬋🬍🬍🬎🬩🬹🬩🬹🬩🬹🬩🬹🬍🬎🬍🬎🬋🬎🬩🬹🬋🬩🬩🬹🬍🬎🬩🬹🬋🬹🬩🬹🬍🬎🬩🬹🬋🬎🬩🬹🬋🬩🬩🬹🬩🬹🬍🬎🬋🬹🬍🬎🬍🬎🬩🬹🬍🬎🬩🬹🬋🬩

2021-340 03:41  \
🬋🬍🬋🬎🬩🬹🬍🬎🬩🬹🬍🬎🬍🬎🬩🬹🬋🬹🬋🬩🬍🬎🬍🬎🬩🬹🬍🬎🬍🬎🬍🬎🬩🬹🬋🬹🬋🬎🬋🬍🬍🬎🬩🬹🬋🬎🬋🬹🬩🬹🬩🬹🬋🬎🬍🬎🬍🬎🬋🬍🬩🬹🬍🬎🬍🬎🬍🬎🬍🬎🬩🬹🬩🬹🬋🬎🬩🬹🬋🬍🬍🬎🬍🬎🬍🬎🬋🬎🬩🬹🬩🬹🬩🬹🬋🬹🬩🬹🬋🬍🬩🬹🬩🬹🬍🬎🬋🬎🬍🬎🬍🬎🬍🬎🬍🬎🬩🬹🬋🬍

""",
            "wwvb.gen",
            "-m",
            "2",
            "--style",
            "sextant",
            "2021-12-6 3:40",
        )

    def test_now(self) -> None:
        """Test outputting timecodes for 'now'"""
        self.assertModuleOutputStarts(
            "WWVB timecode: year=",
            "wwvb.gen",
            "-m",
            "1",
        )

    def test_decode(self) -> None:
        """Test the commandline decoder"""
        self.assertModuleOutput(
            """\
201100000200100001020011001012000000010200010001020001000002
year=2021 days=350 hour=22 min=30 dst=0 ut1=-100 ly=0 ls=0
""",
            "wwvb.decode",
            "201100000200100001020011001012000000010200010001020001000002",
        )

        self.assertModuleOutput(
            """\
201101111200100001020011001012000000010200010001020001000002
""",
            "wwvb.decode",
            "201101111200100001020011001012000000010200010001020001000002",
        )
