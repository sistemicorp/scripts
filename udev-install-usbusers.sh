#!/bin/bash
# Run with user as argument
groupadd usbusers
usermod -a -G usbusers $1

echo 'SUBSYSTEM=="usb", MODE="0666", GROUP="usbusers"' | tee /etc/udev/rules.d/99-usbusers.rules
# Try to reload - if that does not work, reboot!
udevadm control --reload
udevadm trigger

# Print confirmation
echo "USB device configuration has been installed. Please log out and log back in or reboot"
