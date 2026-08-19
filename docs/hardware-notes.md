# Hardware notes and open questions

## The core constraint

John Deere displays are sealed embedded devices. They do not run an operating
system we can log into, and there is no software channel for injecting input.
A Raspberry Pi cannot "send keystrokes to the screen" the way `pyautogui` does
on a desktop. The only way in is to make the Pi *look like a physical USB
keyboard/mouse* (USB gadget mode) and hope the display's firmware accepts HID
peripherals.

That "hope" is the single biggest risk in this project, and it is cheap to
resolve.

## Test to run before writing any macro content

For each of the 2630, 4640, and G5, in a parked tractor:

1. Plug an ordinary USB keyboard into the display's USB port.
2. Navigate to any screen with a text field (a name, a variety, a note).
3. Tap into the field and type.

Record for each display:

- Does typing appear? (If no: HID injection is dead for that model.)
- Does `Tab` move between fields? `Enter` commit? `Esc` cancel?
- Can the UI be navigated by arrow keys alone, without touching the screen?
- Then repeat with a USB **mouse**: does a cursor appear, do clicks register?

**Expected outcome:** Gen 4 and G5 are plausible — they have real USB stacks
and handle peripherals like WiFi adapters. The 2630 is unlikely; it is an older
resistive-touch design whose USB port is essentially for file transfer.

The keyboard-only navigation question matters enormously. If arrow keys and
Tab can reach every field, macros become far more robust, because keystroke
sequences survive firmware UI changes that would break hard-coded tap
coordinates.

## Development target: the John Deere Display Simulator

John Deere publishes an official Display & CommandARM Simulator covering the
GreenStar 3 2630, Gen 4 CommandCenter, and 4640. It runs on Windows and needs a
John Deere account. Gen 4 simulation is online-only; older displays can run
offline.

This is where macros should be authored and validated. On a desktop the
original `pyautogui` approach works exactly as intended, which is what
`DesktopBackend` targets. Coordinates captured in the simulator transfer to
real hardware as long as the display resolution matches.

## The supported alternative: file-based product import

Gen 4 and G5 import setup data and ISO-XML `TASKDATA` from a USB drive,
including products, varieties, and chemicals. This is a documented, supported
path, and it is dramatically more reliable than typing names into fields blind.

It does not fully replace macros: importing a catalog still leaves an operator
to *select* the active product on screen. But the hybrid is worth considering
seriously:

- Write the product catalog by file (robust, supported, no UI dependency).
- Let the macro do only the short selection gesture (few steps, less fragile).

If the HID test above fails, the file path is the fallback that keeps the
project alive, with the Pi writing files to a mounted USB gadget instead of
typing.

## Sources

- https://displaysimulator.deere.com/
- https://stellarsupport.deere.com/en_US/categories/training/simulators/gs_1800_2630/
- https://displaysimulator.deere.com/onscreen_help/4640/current/en/file_manager/file_manager_import_data.htm
- https://support.koenigequipment.com/how-to-import-setup-data-into-a-john-deere-gen-4-display
