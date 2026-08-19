"""Backend that records actions without emitting input. Used for tests and
for reviewing a macro before letting it touch a real display."""

from __future__ import annotations

from .base import InputBackend


class DryRunBackend(InputBackend):
    def key(self, name: str, mods: tuple[str, ...] = ()) -> None:
        self._record("key", name=name, mods=mods)

    def text(self, value: str) -> None:
        self._record("text", value=value)

    def tap(self, x: int, y: int) -> None:
        self._record("tap", x=x, y=y)

    def swipe(self, x1: int, y1: int, x2: int, y2: int, ms: int) -> None:
        self._record("swipe", x1=x1, y1=y1, x2=x2, y2=y2, ms=ms)

    def sleep(self, ms: int) -> None:
        self._record("sleep", ms=ms)
