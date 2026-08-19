"""Drives the John Deere Display Simulator (or any windowed display emulator)
on a normal desktop via synthetic OS input events.

This is the development target: it lets macros be authored and validated
without a tractor. ``origin`` is the top-left screen coordinate of the
simulated display area, so macro coordinates stay in display space and remain
portable to the USB HID backend.
"""

from __future__ import annotations

import time

from .base import InputBackend

# Macro key names -> pyautogui key names.
_KEYMAP = {
    "ENTER": "enter",
    "TAB": "tab",
    "ESC": "esc",
    "BACKSPACE": "backspace",
    "DELETE": "delete",
    "UP": "up",
    "DOWN": "down",
    "LEFT": "left",
    "RIGHT": "right",
    "HOME": "home",
    "END": "end",
    "SPACE": "space",
}


class DesktopBackend(InputBackend):
    def __init__(self, origin: tuple[int, int] = (0, 0), scale: float = 1.0) -> None:
        super().__init__()
        try:
            import pyautogui
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise RuntimeError(
                "DesktopBackend needs the 'desktop' extra: pip install -e '.[desktop]'"
            ) from exc
        pyautogui.FAILSAFE = True
        self._gui = pyautogui
        self._origin = origin
        self._scale = scale

    def _screen(self, x: int, y: int) -> tuple[int, int]:
        ox, oy = self._origin
        return int(ox + x * self._scale), int(oy + y * self._scale)

    def key(self, name: str, mods: tuple[str, ...] = ()) -> None:
        self._record("key", name=name, mods=mods)
        mapped = _KEYMAP.get(name.upper(), name.lower())
        if mods:
            self._gui.hotkey(*(m.lower() for m in mods), mapped)
        else:
            self._gui.press(mapped)

    def text(self, value: str) -> None:
        self._record("text", value=value)
        self._gui.typewrite(value, interval=0.02)

    def tap(self, x: int, y: int) -> None:
        self._record("tap", x=x, y=y)
        self._gui.click(*self._screen(x, y))

    def swipe(self, x1: int, y1: int, x2: int, y2: int, ms: int) -> None:
        self._record("swipe", x1=x1, y1=y1, x2=x2, y2=y2, ms=ms)
        self._gui.moveTo(*self._screen(x1, y1))
        self._gui.dragTo(*self._screen(x2, y2), duration=ms / 1000)

    def sleep(self, ms: int) -> None:
        self._record("sleep", ms=ms)
        time.sleep(ms / 1000)
