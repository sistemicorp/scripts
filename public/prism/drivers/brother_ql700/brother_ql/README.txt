

when printing in the entrypoint docker

docker command:
            docker run -ti -p 6590:6590 -v $(pwd):/app/public -e "DOCKER_HOST=$(ip -4 addr show wlan0 | grep -Po 'inet \K[\d.]+')" --device=/dev/usb/lp0 --entrypoint "/bin/sh" sistemicorp/prismrpi
shell print command:
    python3 ./public/prism/drivers/brother_printer/brother_ql/brother_ql_print.py ./public/prism/label/label.bin /dev/usb/lp0

to view usb devices
install usbutils
    - apt-get install usbutils
use lsusb for a short list of what is avalible
use usb-devices for more information about all the devices avalible

NOTE:
you do not need to install CUPS if you use /dev/usb/lp0 as your path to the printer
