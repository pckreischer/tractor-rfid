"""Macro data model.

A macro is an open-loop sequence of input actions. Because the display gives us
no feedback channel, reliability comes from always starting at a known state:
every ``goto`` first replays the profile's ``home.reset`` sequence, then walks a
recorded path from home to the target screen. Never assume the display is where
the previous macro left it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator

VALID_ACTIONS = {"key", "text", "tap", "swipe", "wait", "goto", "note"}


@dataclass(frozen=True)
class Step:
    action: str
    args: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.action not in VALID_ACTIONS:
            raise ValueError(
                f"unknown action {self.action!r}; expected one of {sorted(VALID_ACTIONS)}"
            )

    def resolve(self, params: dict[str, str]) -> "Step":
        """Substitute ``{param}`` placeholders in string arguments."""
        resolved = {}
        for key, value in self.args.items():
            if isinstance(value, str):
                try:
                    value = value.format(**params)
                except KeyError as exc:
                    raise KeyError(
                        f"step {self.action!r} references undefined parameter {exc.args[0]!r}"
                    ) from None
            resolved[key] = value
        return Step(self.action, resolved)


@dataclass
class Screen:
    """A display screen and the recorded route to reach it from home."""

    name: str
    path_from_home: list[Step] = field(default_factory=list)


@dataclass
class Macro:
    name: str
    params: list[str] = field(default_factory=list)
    steps: list[Step] = field(default_factory=list)

    def bind(self, values: dict[str, str]) -> Iterator[Step]:
        missing = [p for p in self.params if p not in values]
        if missing:
            raise KeyError(f"macro {self.name!r} missing parameters: {missing}")
        for step in self.steps:
            yield step.resolve(values)


@dataclass
class Profile:
    """Everything model-specific about one display: geometry, how to get home,
    the screen map, and the macros defined against it."""

    display: str
    resolution: tuple[int, int] = (1024, 600)
    settle_ms: int = 400
    reset: list[Step] = field(default_factory=list)
    screens: dict[str, Screen] = field(default_factory=dict)
    macros: dict[str, Macro] = field(default_factory=dict)

    def screen(self, name: str) -> Screen:
        if name not in self.screens:
            raise KeyError(
                f"profile {self.display!r} has no screen {name!r}; "
                f"known screens: {sorted(self.screens)}"
            )
        return self.screens[name]

    def macro(self, name: str) -> Macro:
        if name not in self.macros:
            raise KeyError(
                f"profile {self.display!r} has no macro {name!r}; "
                f"known macros: {sorted(self.macros)}"
            )
        return self.macros[name]
