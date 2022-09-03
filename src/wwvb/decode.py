# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only
"""A stateful decoder of WWVB signals"""

import sys
from typing import Generator, List, Optional

import wwvb

# State 1: Unsync'd
#  Marker: State 2
#  Other: State 1
# State 2: One marker
#  Marker: State 3
#  Other: State 1
# State 3: Two markers
#  Marker: State 3
#  Other: State 4
# State 4: Decoding a minute, starting in second 1
#  Second

always_zero = set((4, 10, 11, 14, 20, 21, 34, 35, 44, 54))


def wwvbreceive() -> Generator[  # pylint: disable=too-many-branches
    Optional[wwvb.WWVBTimecode], wwvb.AmplitudeModulation, None
]:
    """A stateful decoder of WWVB signals"""
    minute: List[wwvb.AmplitudeModulation] = []
    state = 1

    value = yield None
    while True:
        # print(state, value, len(minute), "".join(str(int(i)) for i in minute))
        if state == 1:
            minute = []
            if value == wwvb.AmplitudeModulation.MARK:
                state = 2
            value = yield None

        elif state == 2:
            if value == wwvb.AmplitudeModulation.MARK:
                state = 3
            else:
                state = 1
            value = yield None

        elif state == 3:
            if value != wwvb.AmplitudeModulation.MARK:
                state = 4
                minute = [wwvb.AmplitudeModulation.MARK, value]
            value = yield None

        else:  #  state == 4:
            minute.append(value)
            if len(minute) % 10 == 0 and value != wwvb.AmplitudeModulation.MARK:
                # print("MISSING MARK", len(minute), "".join(str(int(i)) for i in minute))
                state = 1
            elif len(minute) % 10 and value == wwvb.AmplitudeModulation.MARK:
                # print("UNEXPECTED MARK")
                state = 1
            elif (
                len(minute) - 1 in always_zero
                and value != wwvb.AmplitudeModulation.ZERO
            ):
                # print("UNEXPECTED NONZERO")
                state = 1
            elif len(minute) == 60:
                # print("FULL MINUTE")
                tc = wwvb.WWVBTimecode(60)
                tc.am[:] = minute
                minute = []
                state = 2
                value = yield tc
            else:
                value = yield None


def main() -> None:
    """Read symbols on stdin and print any successfully-decoded minutes"""
    decoder = wwvbreceive()
    next(decoder)
    decoder.send(wwvb.AmplitudeModulation.MARK)
    for s in sys.argv[1:]:
        for c in s:
            decoded = decoder.send(wwvb.AmplitudeModulation(int(c)))
            if decoded:
                print(decoded)
                w = wwvb.WWVBMinute.from_timecode_am(decoded)
                if w:
                    print(w)


if __name__ == "__main__":  # pragma no cover
    main()
