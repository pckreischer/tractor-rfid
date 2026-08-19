"""Load display profiles from YAML."""

from __future__ import annotations

from pathlib import Path

import yaml

from .model import Macro, Profile, Screen, Step


def _steps(raw: list | None, where: str) -> list[Step]:
    steps: list[Step] = []
    for i, item in enumerate(raw or []):
        if not isinstance(item, dict) or len(item) == 0:
            raise ValueError(f"{where}[{i}]: each step must be a mapping")
        # Steps are written as {action: <name>, ...args} or shorthand {<name>: arg}.
        if "action" in item:
            action = item["action"]
            args = {k: v for k, v in item.items() if k != "action"}
        elif len(item) == 1:
            (action, value), = item.items()
            args = value if isinstance(value, dict) else {"value": value}
        else:
            raise ValueError(f"{where}[{i}]: ambiguous step, add an explicit 'action'")
        steps.append(Step(action, args))
    return steps


def load_profile(path: str | Path) -> Profile:
    path = Path(path)
    data = yaml.safe_load(path.read_text()) or {}

    profile = Profile(
        display=data.get("display", path.stem),
        resolution=tuple(data.get("resolution", (1024, 600))),
        settle_ms=data.get("settle_ms", 400),
        reset=_steps((data.get("home") or {}).get("reset"), "home.reset"),
    )
    for name, body in (data.get("screens") or {}).items():
        body = body or {}
        profile.screens[name] = Screen(
            name=name,
            path_from_home=_steps(body.get("path_from_home"), f"screens.{name}"),
        )
    for name, body in (data.get("macros") or {}).items():
        body = body or {}
        profile.macros[name] = Macro(
            name=name,
            params=list(body.get("params") or []),
            steps=_steps(body.get("steps"), f"macros.{name}"),
        )
    return profile


def load_profiles(directory: str | Path) -> dict[str, Profile]:
    return {
        p.stem: load_profile(p) for p in sorted(Path(directory).glob("*.yaml"))
    }
