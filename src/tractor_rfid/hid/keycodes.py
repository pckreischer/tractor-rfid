"""USB HID Usage Table (page 0x07) subset needed for display data entry."""

from __future__ import annotations

MOD_CTRL = 0x01
MOD_SHIFT = 0x02
MOD_ALT = 0x04
MOD_GUI = 0x08

MODIFIERS = {"ctrl": MOD_CTRL, "shift": MOD_SHIFT, "alt": MOD_ALT, "gui": MOD_GUI}

# Named keys usable from macro YAML.
NAMED: dict[str, int] = {
    "ENTER": 0x28,
    "ESC": 0x29,
    "BACKSPACE": 0x2A,
    "TAB": 0x2B,
    "SPACE": 0x2C,
    "MINUS": 0x2D,
    "EQUAL": 0x2E,
    "CAPSLOCK": 0x39,
    "HOME": 0x4A,
    "PAGEUP": 0x4B,
    "DELETE": 0x4C,
    "END": 0x4D,
    "PAGEDOWN": 0x4E,
    "RIGHT": 0x4F,
    "LEFT": 0x50,
    "DOWN": 0x51,
    "UP": 0x52,
}
NAMED.update({f"F{i}": 0x39 + i for i in range(1, 13)})

# Printable ASCII -> (usage, needs_shift)
_UNSHIFTED = {
    "-": 0x2D, "=": 0x2E, "[": 0x2F, "]": 0x30, "\\": 0x31, ";": 0x33,
    "'": 0x34, "`": 0x35, ",": 0x36, ".": 0x37, "/": 0x38, " ": 0x2C,
    "\n": 0x28, "\t": 0x2B,
}
_SHIFTED = {
    "_": 0x2D, "+": 0x2E, "{": 0x2F, "}": 0x30, "|": 0x31, ":": 0x33,
    '"': 0x34, "~": 0x35, "<": 0x36, ">": 0x37, "?": 0x38,
    "!": 0x1E, "@": 0x1F, "#": 0x20, "$": 0x21, "%": 0x22,
    "^": 0x23, "&": 0x24, "*": 0x25, "(": 0x26, ")": 0x27,
}


def char_to_usage(ch: str) -> tuple[int, bool]:
    """Map one character to its (usage code, shift required).

    Raises ValueError for characters with no US-layout representation, which
    is deliberate: a silently dropped character in a chemical name is worse
    than a loud failure.
    """
    if "a" <= ch <= "z":
        return 0x04 + ord(ch) - ord("a"), False
    if "A" <= ch <= "Z":
        return 0x04 + ord(ch) - ord("A"), True
    if ch == "0":
        return 0x27, False
    if "1" <= ch <= "9":
        return 0x1E + ord(ch) - ord("1"), False
    if ch in _UNSHIFTED:
        return _UNSHIFTED[ch], False
    if ch in _SHIFTED:
        return _SHIFTED[ch], True
    raise ValueError(f"no US-layout HID usage for character {ch!r}")
