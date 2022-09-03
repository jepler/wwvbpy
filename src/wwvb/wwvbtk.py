#!/usr/bin/python3
"""Visualize the WWVB signal in realtime"""

# Copyright (C) 2011-2020 Jeff Epler <jepler@gmail.com>
# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

import threading
import time
from tkinter import Canvas, Tk  # pylint: disable=import-error
from typing import Any, Generator, Tuple

import wwvb


def main() -> None:
    """Visualize the WWVB signal in realtime"""

    def sleep_deadline(deadline: float) -> None:
        """Sleep until a deadline"""
        now = time.time()
        if deadline > now:
            time.sleep(deadline - now)

    def wwvbtick() -> Generator[Tuple[float, wwvb.AmplitudeModulation], None, None]:
        """Yield consecutive values of the WWVB amplitude signal, going from minute to minute"""
        timestamp = time.time() // 60 * 60

        while True:
            tt = time.gmtime(timestamp)
            key = tt.tm_year, tt.tm_yday, tt.tm_hour, tt.tm_min
            timecode = wwvb.WWVBMinuteIERS(*key).as_timecode()
            for i, code in enumerate(timecode.am):
                yield timestamp + i, code
            timestamp = timestamp + 60

    def wwvbsmarttick() -> Generator[
        Tuple[float, wwvb.AmplitudeModulation], None, None
    ]:
        """Yield consecutive values of the WWVB amplitude signal but deal with time
        progressing unexpectedly, such as when the computer is suspended or NTP steps
        the clock backwards

        When time goes backwards or advances by more than a minute, get a fresh
        wwvbtick object; otherwise, discard time signals more than 1s in the past."""
        while True:
            for stamp, code in wwvbtick():
                now = time.time()
                if stamp < now - 60:
                    break
                if stamp < now - 1:
                    continue
                yield stamp, code

    colors = ["#3c3c3c", "#cc3c3c", "#88883c", "#3ccc3c"]
    app = Tk()
    app.wm_minsize(48, 48)
    canvas = Canvas(app, width=48, height=48, highlightthickness=0)
    canvas.pack(fill="both", expand=True)
    circle = canvas.create_oval(4, 4, 44, 44, outline="black", fill=colors[0])

    def resize_canvas(event: Any) -> None:
        """Keep the circle filling the window when it is resized"""
        sz = min(event.width, event.height) - 8
        if sz < 0:
            return
        canvas.coords(
            circle,
            event.width // 2 - sz // 2,
            event.height // 2 - sz // 2,
            event.width // 2 + sz // 2,
            event.height // 2 + sz // 2,
        )

    canvas.bind("<Configure>", resize_canvas)

    def led_on(i: int) -> None:
        """Turn the canvas's virtual LED on"""
        canvas.itemconfigure(circle, fill=colors[i + 1])

    def led_off() -> None:
        """Turn the canvas's virtual LED off"""
        canvas.itemconfigure(circle, fill=colors[0])

    def thread_func() -> None:
        """Update the canvas virtual LED"""
        for stamp, code in wwvbsmarttick():
            sleep_deadline(stamp)
            led_on(code)
            app.update()
            sleep_deadline(stamp + 0.2 + 0.3 * int(code))
            led_off()
            app.update()

    thread = threading.Thread(target=thread_func, daemon=True)
    thread.start()
    app.mainloop()


if __name__ == "__main__":
    main()
