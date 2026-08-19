"""Command line entry point: jdmacro"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .macro.loader import load_profile
from .macro.runner import MacroRunner

DEFAULT_PROFILES = Path(__file__).resolve().parents[2] / "profiles"


def _make_backend(name: str, profile, origin):
    if name == "dry-run":
        from .backends.dry_run import DryRunBackend

        return DryRunBackend()
    if name == "desktop":
        from .backends.desktop import DesktopBackend

        return DesktopBackend(origin=origin)
    if name == "usb-hid":
        from .backends.usb_hid import UsbHidBackend

        return UsbHidBackend(display_size=profile.resolution)
    raise SystemExit(f"unknown backend {name!r}")


def _parse_params(pairs: list[str]) -> dict[str, str]:
    params = {}
    for pair in pairs:
        if "=" not in pair:
            raise SystemExit(f"bad --set {pair!r}, expected key=value")
        key, value = pair.split("=", 1)
        params[key] = value
    return params


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jdmacro", description=__doc__)
    parser.add_argument("-p", "--profile", default="gen4", help="profile name or path")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="list screens and macros in a profile")

    run = sub.add_parser("run", help="execute a macro")
    run.add_argument("macro")
    run.add_argument("--set", dest="params", action="append", default=[],
                     metavar="KEY=VALUE", help="macro parameter, repeatable")
    run.add_argument("--backend", default="dry-run",
                     choices=["dry-run", "desktop", "usb-hid"])
    run.add_argument("--origin", default="0,0",
                     help="desktop backend: screen coords of the display's top-left")

    rec = sub.add_parser("record", help="record a macro by demonstration")
    rec.add_argument("name")
    rec.add_argument("-o", "--out", required=True)
    rec.add_argument("--origin", default="0,0")

    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )

    if args.cmd == "record":
        from .recorder import record_interactive

        ox, oy = (int(v) for v in args.origin.split(","))
        out = record_interactive(args.name, args.out, origin=(ox, oy))
        print(f"wrote {out}")
        return 0

    path = Path(args.profile)
    if not path.exists():
        path = DEFAULT_PROFILES / f"{args.profile}.yaml"
    if not path.exists():
        raise SystemExit(f"no such profile: {args.profile}")
    profile = load_profile(path)

    if args.cmd == "list":
        print(f"{profile.display}  {profile.resolution[0]}x{profile.resolution[1]}")
        print("  screens:", ", ".join(sorted(profile.screens)) or "(none)")
        for name, macro in sorted(profile.macros.items()):
            params = ", ".join(macro.params)
            print(f"  macro {name}({params})  {len(macro.steps)} steps")
        return 0

    ox, oy = (int(v) for v in args.origin.split(","))
    backend = _make_backend(args.backend, profile, (ox, oy))
    runner = MacroRunner(profile, backend)
    try:
        runner.run(args.macro, _parse_params(args.params))
    finally:
        backend.close()

    if args.backend == "dry-run":
        for event in backend.transcript:
            print(" ", event)
    return 0


if __name__ == "__main__":
    sys.exit(main())
