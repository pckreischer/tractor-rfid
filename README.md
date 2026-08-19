# tractor-rfid

Dynamic macro engine for entering the current seed or chemical into John Deere
on-board displays (GreenStar 3 2630, Gen 4 / 4640, G5), intended to run on a
Raspberry Pi.

**Read [docs/hardware-notes.md](docs/hardware-notes.md) first.** There is a
hardware question that has to be answered before macro content is worth
writing.

## Status

Proof of concept. The engine, CLI, recorder, and both input transports work.
The macro *content* in `profiles/` is a placeholder skeleton — every
coordinate marked `TODO` must be captured from a real screen.

## Install

```bash
python3 -m venv .venv && .venv/bin/pip install -e '.[dev,desktop]'
```

## Use

```bash
jdmacro list                                    # screens and macros in a profile
jdmacro run set_seed_variety --set crop=Corn --set variety=P1197AM
jdmacro run set_chemical --set product="Roundup PowerMAX" --set rate="32 oz/ac" \
        --backend desktop --origin 120,80
jdmacro record set_seed_variety -o profiles/captured.yaml
```

`run` defaults to the `dry-run` backend, which prints the input events it
*would* send without emitting any. Always review a macro this way first.

## How it works

```
profiles/*.yaml   →  Profile / Macro / Step   →  MacroRunner  →  InputBackend
 (what to press)      (parsed, parameterised)     (dispatch)      (how to press it)
```

The backend split is the point: the same macro drives the John Deere Display
Simulator on a laptop (`DesktopBackend`, synthetic OS input) or a physical
display over USB (`UsbHidBackend`, Pi in USB gadget mode). Macro coordinates
are always in display pixels, so they port between the two.

### Reliability model

The displays give us no feedback channel — we cannot read the screen, so we
cannot verify state. Macros are therefore strictly open-loop, and reliability
comes from one rule: **never assume where the display is.** Every `goto`
replays the profile's `home.reset` sequence (which also dismisses stray modal
dialogs) before walking a recorded path from home. Nothing chains off the
previous macro's end state.

This is the weak point of the approach, and it is inherent. If closed-loop
verification is ever needed, the route is a small camera on the display plus
template matching — a `verify` step type would slot into `MacroRunner._execute`.

## Layout

| Path | What |
|---|---|
| `src/tractor_rfid/macro/` | model, YAML loader, runner |
| `src/tractor_rfid/backends/` | `dry_run`, `desktop`, `usb_hid` |
| `src/tractor_rfid/hid/` | USB HID usage tables |
| `src/tractor_rfid/recorder.py` | capture a macro by demonstration |
| `profiles/` | per-display navigation maps and macros |
| `scripts/setup_hid_gadget.sh` | configure the Pi as a USB HID device |

## Not yet built

- Profiles for the 2630 and G5 (blocked on the HID test)
- Real captured coordinates for Gen 4
- Anything that decides *which* seed or chemical is in use — the RFID side
