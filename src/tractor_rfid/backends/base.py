"""Input transport abstraction.

Every backend turns the same abstract actions into real input events. The macro
layer never knows whether it is driving the John Deere Display Simulator on a
laptop or a physical 4640 over USB HID.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Event:
    """One input event, recorded for transcripts and test assertions."""

    kind: str
    detail: dict = field(default_factory=dict)

    def __str__(self) -> str:
        args = " ".join(f"{k}={v!r}" for k, v in self.detail.items())
        return f"{self.kind} {args}".rstrip()


class InputBackend(ABC):
    """Abstract keyboard/pointer transport.

    Coordinates are in display pixels, origin top-left. Backends that drive a
    windowed simulator are responsible for translating to screen coordinates.
    """

    def __init__(self) -> None:
        self.transcript: list[Event] = []

    def _record(self, kind: str, **detail) -> Event:
        event = Event(kind, detail)
        self.transcript.append(event)
        return event

    @abstractmethod
    def key(self, name: str, mods: tuple[str, ...] = ()) -> None:
        """Press and release a single named key, e.g. ``TAB``, ``ENTER``."""

    @abstractmethod
    def text(self, value: str) -> None:
        """Type a literal string."""

    @abstractmethod
    def tap(self, x: int, y: int) -> None:
        """Touch/click at a display coordinate."""

    @abstractmethod
    def swipe(self, x1: int, y1: int, x2: int, y2: int, ms: int) -> None:
        """Drag from one display coordinate to another."""

    @abstractmethod
    def sleep(self, ms: int) -> None:
        """Wait, giving the display time to redraw."""

    def close(self) -> None:
        """Release any hardware handles. Safe to call twice."""
