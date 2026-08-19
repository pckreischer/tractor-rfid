"""Raspberry Pi USB-gadget backend: the Pi presents itself to the display as a
physical USB keyboard and absolute-position mouse.

Requires the gadget to be configured first -- see scripts/setup_hid_gadget.sh.
Whether a given John Deere display honours HID input at all is a per-model
hardware question; see docs/hardware-notes.md.
"""

from __future__ import annotations

import time

from ..hid.keycodes import MODIFIERS, NAMED, char_to_usage
from .base import InputBackend

# Absolute pointer logical range, matching the report descriptor in the setup
# script. Macro coordinates are scaled from display pixels into this range.
ABS_MAX = 32767


class UsbHidBackend(InputBackend):
    def __init__(
        self,
        keyboard_dev: str = "/dev/hidg0",
        mouse_dev: str | None = "/dev/hidg1",
        display_size: tuple[int, int] = (1024, 600),
        key_hold_ms: int = 12,
    ) -> None:
        super().__init__()
        self._kbd = open(keyboard_dev, "wb", buffering=0)
        self._mouse = open(mouse_dev, "wb", buffering=0) if mouse_dev else None
        self._w, self._h = display_size
        self._hold = key_hold_ms / 1000

    # -- keyboard ---------------------------------------------------------
    def _kbd_report(self, mod: int = 0, usage: int = 0) -> None:
        self._kbd.write(bytes([mod, 0, usage, 0, 0, 0, 0, 0]))

    def _stroke(self, usage: int, mod: int) -> None:
        self._kbd_report(mod, usage)
        time.sleep(self._hold)
        self._kbd_report()  # all keys up
        time.sleep(self._hold)

    def key(self, name: str, mods: tuple[str, ...] = ()) -> None:
        self._record("key", name=name, mods=mods)
        upper = name.upper()
        if upper in NAMED:
            usage, shifted = NAMED[upper], False
        elif len(name) == 1:
            usage, shifted = char_to_usage(name)
        else:
            raise ValueError(f"unknown key name {name!r}")
        mod = sum(MODIFIERS[m.lower()] for m in mods)
        if shifted:
            mod |= MODIFIERS["shift"]
        self._stroke(usage, mod)

    def text(self, value: str) -> None:
        self._record("text", value=value)
        for ch in value:
            usage, shifted = char_to_usage(ch)
            self._stroke(usage, MODIFIERS["shift"] if shifted else 0)

    # -- pointer ----------------------------------------------------------
    def _require_mouse(self):
        if self._mouse is None:
            raise RuntimeError("no mouse gadget configured; this macro needs taps")
        return self._mouse

    def _abs_report(self, buttons: int, x: int, y: int) -> None:
        ax = max(0, min(ABS_MAX, round(x / self._w * ABS_MAX)))
        ay = max(0, min(ABS_MAX, round(y / self._h * ABS_MAX)))
        self._require_mouse().write(
            bytes([buttons, ax & 0xFF, ax >> 8, ay & 0xFF, ay >> 8])
        )

    def tap(self, x: int, y: int) -> None:
        self._record("tap", x=x, y=y)
        self._abs_report(0, x, y)  # move first so the press lands settled
        time.sleep(self._hold)
        self._abs_report(1, x, y)
        time.sleep(self._hold)
        self._abs_report(0, x, y)

    def swipe(self, x1: int, y1: int, x2: int, y2: int, ms: int) -> None:
        self._record("swipe", x1=x1, y1=y1, x2=x2, y2=y2, ms=ms)
        steps = max(2, ms // 10)
        self._abs_report(0, x1, y1)
        self._abs_report(1, x1, y1)
        for i in range(1, steps + 1):
            t = i / steps
            self._abs_report(1, round(x1 + (x2 - x1) * t), round(y1 + (y2 - y1) * t))
            time.sleep(ms / steps / 1000)
        self._abs_report(0, x2, y2)

    def sleep(self, ms: int) -> None:
        self._record("sleep", ms=ms)
        time.sleep(ms / 1000)

    def close(self) -> None:
        for handle in (self._kbd, self._mouse):
            if handle and not handle.closed:
                handle.close()
