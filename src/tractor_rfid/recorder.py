"""Capture a human driving the John Deere Display Simulator and emit macro YAML.

Coordinates for these displays cannot be guessed -- they have to come from a
real screen. Run this, perform the data-entry task by hand once, and the
resulting steps become the skeleton of a macro. Replace the literal text you
typed with a ``{param}`` placeholder to make it dynamic.
"""

from __future__ import annotations

import time
from pathlib import Path

_MIN_GAP_MS = 150  # gaps shorter than this are typing rhythm, not real waits


class Recorder:
    def __init__(self, origin: tuple[int, int] = (0, 0)) -> None:
        self.origin = origin
        self.steps: list[dict] = []
        self._last = time.monotonic()
        self._pending_text: list[str] = []

    def _gap(self) -> None:
        now = time.monotonic()
        ms = int((now - self._last) * 1000)
        self._last = now
        if ms >= _MIN_GAP_MS:
            self.steps.append({"action": "wait", "ms": min(ms, 5000)})

    def _flush_text(self) -> None:
        if self._pending_text:
            self.steps.append({"action": "text", "value": "".join(self._pending_text)})
            self._pending_text.clear()

    def on_click(self, x: int, y: int) -> None:
        self._flush_text()
        self._gap()
        self.steps.append(
            {"action": "tap", "x": x - self.origin[0], "y": y - self.origin[1]}
        )

    def on_char(self, ch: str) -> None:
        if not self._pending_text:
            self._gap()
        self._pending_text.append(ch)

    def on_key(self, name: str) -> None:
        self._flush_text()
        self._gap()
        self.steps.append({"action": "key", "name": name})

    def to_yaml(self, macro_name: str) -> str:
        import yaml

        self._flush_text()
        doc = {"macros": {macro_name: {"params": [], "steps": self.steps}}}
        return yaml.safe_dump(doc, sort_keys=False, default_flow_style=False)

    def save(self, path: str | Path, macro_name: str) -> Path:
        path = Path(path)
        path.write_text(self.to_yaml(macro_name))
        return path


def record_interactive(macro_name: str, out: str | Path, origin=(0, 0)) -> Path:
    """Record until Esc is pressed twice in a row."""
    try:
        from pynput import keyboard, mouse
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("recording needs pynput: pip install pynput") from exc

    rec = Recorder(origin)
    stop = {"escapes": 0}

    def on_click(x, y, button, pressed):
        if pressed:
            rec.on_click(int(x), int(y))

    def on_press(key):
        if key == keyboard.Key.esc:
            stop["escapes"] += 1
            if stop["escapes"] >= 2:
                return False
            rec.on_key("ESC")
            return None
        stop["escapes"] = 0
        if hasattr(key, "char") and key.char:
            rec.on_char(key.char)
        else:
            rec.on_key(str(key).removeprefix("Key.").upper())
        return None

    print(f"Recording '{macro_name}'. Perform the task, then press Esc twice.")
    with mouse.Listener(on_click=on_click):
        with keyboard.Listener(on_press=on_press) as kl:
            kl.join()
    return rec.save(out, macro_name)
