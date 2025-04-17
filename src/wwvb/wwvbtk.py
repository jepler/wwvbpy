#!/usr/bin/python3
"""Visualize the WWVB signal in realtime"""

# SPDX-FileCopyrightText: 2021-2024 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import functools
import time
from tkinter import Canvas, TclError, Tk
from typing import TYPE_CHECKING, Any

import click

import wwvb

if TYPE_CHECKING:
    from collections.abc import Generator


@functools.cache
def _app() -> Tk:
    """Create the Tk application object lazily"""
    return Tk()


def validate_colors(ctx: Any, param: Any, value: str) -> list[str]:  # noqa: ARG001
    """Check that all colors in a string are valid, splitting it to a list"""
    app = _app()
    colors = value.split()
    if len(colors) not in (2, 3, 4, 6):
        raise click.BadParameter(f"Give 2, 3, 4 or 6 colors (not {len(colors)})")
    for c in colors:
        try:
            app.winfo_rgb(c)
        except TclError as e:
            raise click.BadParameter(f"Invalid color {c}") from e

    if len(colors) == 2:
        off, on = colors
        return [off, off, off, on, on, on]
    if len(colors) == 3:
        return colors + colors
    if len(colors) == 4:
        off, c1, c2, c3 = colors
        return [off, off, off, c1, c2, c3]
    return colors


DEFAULT_COLORS = "#3c3c3c #3c3c3c #3c3c3c #cc3c3c #88883c #3ccc3c"


@click.command
@click.option(
    "--colors",
    callback=validate_colors,
    default=DEFAULT_COLORS,
    metavar="COLORS",
    help="2, 3, 4, or 6 Tk color values",
)
@click.option("--size", default=48)
@click.option("--min-size", default=None)
def main(colors: list[str], size: int, min_size: int | None) -> None:  # noqa: PLR0915
    """Visualize the WWVB signal in realtime"""
    if min_size is None:
        min_size = size

    def deadline_ms(deadline: float) -> int:
        """Compute the number of ms until a deadline"""
        now = time.time()
        return int(max(0, deadline - now) * 1000)

    def wwvbtick() -> Generator[tuple[float, wwvb.AmplitudeModulation], None, None]:
        """Yield consecutive values of the WWVB amplitude signal, going from minute to minute"""
        timestamp = time.time() // 60 * 60

        while True:
            tt = time.gmtime(timestamp)
            key = tt.tm_year, tt.tm_yday, tt.tm_hour, tt.tm_min
            timecode = wwvb.WWVBMinuteIERS(*key).as_timecode()
            for i, code in enumerate(timecode.am):
                yield timestamp + i, code
            timestamp = timestamp + 60

    def wwvbsmarttick() -> Generator[tuple[float, wwvb.AmplitudeModulation], None, None]:
        """Yield consecutive values of the WWVB amplitude signal

        .. but deal with time progressing unexpectedly, such as when the
        computer is suspended or NTP steps the clock backwards

        When time goes backwards or advances by more than a minute, get a fresh
        wwvbtick object; otherwise, discard time signals more than 1s in the past.
        """
        while True:
            for stamp, code in wwvbtick():
                now = time.time()
                if stamp < now - 60:
                    break
                if stamp < now - 1:
                    continue
                yield stamp, code

    app = _app()
    app.wm_minsize(min_size, min_size)
    canvas = Canvas(app, width=size, height=size, highlightthickness=0)
    circle = canvas.create_oval(4, 4, 44, 44, outline="black", fill=colors[0])
    canvas.pack(fill="both", expand=True)
    app.wm_deiconify()

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
        canvas.itemconfigure(circle, fill=colors[i + 3])

    def led_off(i: int) -> None:
        """Turn the canvas's virtual LED off"""
        canvas.itemconfigure(circle, fill=colors[i])

    def controller_func() -> Generator[int]:
        """Update the canvas virtual LED, yielding the number of ms until the next change"""
        for stamp, code in wwvbsmarttick():
            yield deadline_ms(stamp)
            led_on(code)
            app.update()
            yield deadline_ms(stamp + 0.2 + 0.3 * int(code))
            led_off(code)
            app.update()

    controller = controller_func().__next__

    def after_func() -> None:
        """Repeatedly run the controller after the desired interval"""
        app.after(controller(), after_func)

    app.after_idle(after_func)
    app.mainloop()


if __name__ == "__main__":
    main()
