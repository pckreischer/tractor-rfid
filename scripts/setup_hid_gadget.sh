#!/usr/bin/env bash
# Configure a Raspberry Pi as a USB HID keyboard + absolute-position mouse.
#
# Requires an OTG-capable USB port: Pi Zero / Zero 2 W (micro-USB "USB" port),
# Pi 4 or Pi 5 (USB-C power port). A Pi 3 or 3B+ cannot do this.
#
# Prerequisites, then reboot:
#   echo dtoverlay=dwc2 | sudo tee -a /boot/firmware/config.txt
#   echo dwc2           | sudo tee -a /etc/modules
#
# Run as root at boot (systemd unit or /etc/rc.local).
set -euo pipefail

G=/sys/kernel/config/usb_gadget/jdmacro
modprobe libcomposite

[ -d "$G" ] && { echo "gadget already configured"; exit 0; }

mkdir -p "$G"
cd "$G"
echo 0x1d6b > idVendor          # Linux Foundation
echo 0x0104 > idProduct         # Multifunction Composite Gadget
echo 0x0100 > bcdDevice
echo 0x0200 > bcdUSB

mkdir -p strings/0x409
echo "0001"            > strings/0x409/serialnumber
echo "tractor-rfid"    > strings/0x409/manufacturer
echo "JD Macro HID"    > strings/0x409/product

mkdir -p configs/c.1/strings/0x409
echo "HID Config" > configs/c.1/strings/0x409/configuration
echo 250          > configs/c.1/MaxPower

# --- boot keyboard: 8-byte report ---------------------------------------
mkdir -p functions/hid.kbd
echo 1 > functions/hid.kbd/protocol      # keyboard
echo 1 > functions/hid.kbd/subclass      # boot interface
echo 8 > functions/hid.kbd/report_length
printf '\x05\x01\x09\x06\xa1\x01\x05\x07\x19\xe0\x29\xe7\x15\x00\x25\x01\x75\x01\x95\x08\x81\x02\x95\x01\x75\x08\x81\x03\x95\x06\x75\x08\x15\x00\x25\x65\x05\x07\x19\x00\x29\x65\x81\x00\xc0' \
  > functions/hid.kbd/report_desc

# --- absolute-position mouse: 5-byte report (buttons, x16, y16) ---------
mkdir -p functions/hid.mouse
echo 0 > functions/hid.mouse/protocol
echo 0 > functions/hid.mouse/subclass
echo 5 > functions/hid.mouse/report_length
printf '\x05\x01\x09\x02\xa1\x01\x09\x01\xa1\x00\x05\x09\x19\x01\x29\x03\x15\x00\x25\x01\x95\x03\x75\x01\x81\x02\x95\x01\x75\x05\x81\x03\x05\x01\x09\x30\x09\x31\x15\x00\x26\xff\x7f\x75\x10\x95\x02\x81\x02\xc0\xc0' \
  > functions/hid.mouse/report_desc

ln -s functions/hid.kbd   configs/c.1/
ln -s functions/hid.mouse configs/c.1/

# Bind to the first available UDC.
ls /sys/class/udc > UDC

echo "gadget up: /dev/hidg0 (keyboard), /dev/hidg1 (mouse)"
