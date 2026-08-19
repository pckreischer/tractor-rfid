"""Execute macros against an input backend."""

from __future__ import annotations

import logging

from ..backends.base import InputBackend
from .model import Macro, Profile, Step

log = logging.getLogger(__name__)


class MacroRunner:
    def __init__(self, profile: Profile, backend: InputBackend) -> None:
        self.profile = profile
        self.backend = backend
        self._at_home = False

    def run(self, macro: str | Macro, params: dict[str, str] | None = None) -> None:
        macro = self.profile.macro(macro) if isinstance(macro, str) else macro
        params = params or {}
        log.info("running macro %s with %s", macro.name, params)
        for step in macro.bind(params):
            self._execute(step)

    def go_home(self) -> None:
        """Replay the profile's reset sequence to reach a known state."""
        for step in self.profile.reset:
            self._execute(step, _internal=True)
        self._at_home = True

    def goto(self, screen_name: str) -> None:
        """Navigate to a screen, always via home so the route is deterministic."""
        screen = self.profile.screen(screen_name)
        self.go_home()
        for step in screen.path_from_home:
            self._execute(step, _internal=True)
        self._at_home = False

    # -- step dispatch ----------------------------------------------------
    def _execute(self, step: Step, _internal: bool = False) -> None:
        a = step.args
        if step.action == "key":
            name = a.get("name") or a.get("value")
            mods = tuple(a.get("mods") or ())
            for _ in range(int(a.get("repeat", 1))):
                self.backend.key(name, mods)
        elif step.action == "text":
            self.backend.text(str(a.get("value", "")))
        elif step.action == "tap":
            self.backend.tap(int(a["x"]), int(a["y"]))
        elif step.action == "swipe":
            self.backend.swipe(
                int(a["x1"]), int(a["y1"]), int(a["x2"]), int(a["y2"]),
                int(a.get("ms", 300)),
            )
        elif step.action == "wait":
            self.backend.sleep(int(a.get("ms", self.profile.settle_ms)))
            return  # an explicit wait needs no settle after it
        elif step.action == "goto":
            if _internal:
                raise ValueError("'goto' is not allowed inside a navigation path")
            self.goto(str(a.get("screen") or a["value"]))
            return
        elif step.action == "note":
            log.info("note: %s", a.get("value", ""))
            return

        # Displays repaint slowly; give every real input time to land.
        self.backend.sleep(self.profile.settle_ms)
