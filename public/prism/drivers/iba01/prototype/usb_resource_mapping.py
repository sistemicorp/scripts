#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2019
Martin Guthrie

TODO: Add the other items found on the IBA01 hub,

    import pyudev
    context = pyudev.Context()
    for device in context.list_devices():
        print(device)

    Device('/sys/devices/pci0000:00/0000:00:14.0/usb1/1-2/1-2.4')
    Device('/sys/devices/pci0000:00/0000:00:14.0/usb1/1-2/1-2.4/1-2.4.1')
    Device('/sys/devices/pci0000:00/0000:00:14.0/usb1/1-2/1-2.4/1-2.4.1/1-2.4.1:1.0')
    Device('/sys/devices/pci0000:00/0000:00:14.0/usb1/1-2/1-2.4/1-2.4.1/1-2.4.1:1.0/ttyUSB0')
    Device('/sys/devices/pci0000:00/0000:00:14.0/usb1/1-2/1-2.4/1-2.4.1/1-2.4.1:1.0/ttyUSB0/tty/ttyUSB0')
    Device('/sys/devices/pci0000:00/0000:00:14.0/usb1/1-2/1-2.4/1-2.4.1/1-2.4.1:1.1')
    Device('/sys/devices/pci0000:00/0000:00:14.0/usb1/1-2/1-2.4/1-2.4.1/1-2.4.1:1.1/ttyUSB1')
    Device('/sys/devices/pci0000:00/0000:00:14.0/usb1/1-2/1-2.4/1-2.4.1/1-2.4.1:1.1/ttyUSB1/tty/ttyUSB1')
    Device('/sys/devices/pci0000:00/0000:00:14.0/usb1/1-2/1-2.4/1-2.4.3')
    Device('/sys/devices/pci0000:00/0000:00:14.0/usb1/1-2/1-2.4/1-2.4.3/1-2.4.3:1.0')
    Device('/sys/devices/pci0000:00/0000:00:14.0/usb1/1-2/1-2.4/1-2.4.3/1-2.4.3:1.0/host0')
    Device('/sys/devices/pci0000:00/0000:00:14.0/usb1/1-2/1-2.4/1-2.4.3/1-2.4.3:1.0/host0/scsi_host/host0')
    Device('/sys/devices/pci0000:00/0000:00:14.0/usb1/1-2/1-2.4/1-2.4.3/1-2.4.3:1.0/host0/target0:0:0')
    Device('/sys/devices/pci0000:00/0000:00:14.0/usb1/1-2/1-2.4/1-2.4.3/1-2.4.3:1.0/host0/target0:0:0/0:0:0:0')
    Device('/sys/devices/pci0000:00/0000:00:14.0/usb1/1-2/1-2.4/1-2.4.3/1-2.4.3:1.0/host0/target0:0:0/0:0:0:0/block/sda')
    Device('/sys/devices/pci0000:00/0000:00:14.0/usb1/1-2/1-2.4/1-2.4.3/1-2.4.3:1.0/host0/target0:0:0/0:0:0:0/block/sda/sda1')
    Device('/sys/devices/pci0000:00/0000:00:14.0/usb1/1-2/1-2.4/1-2.4.3/1-2.4.3:1.0/host0/target0:0:0/0:0:0:0/bsg/0:0:0:0')
    Device('/sys/devices/pci0000:00/0000:00:14.0/usb1/1-2/1-2.4/1-2.4.3/1-2.4.3:1.0/host0/target0:0:0/0:0:0:0/scsi_device/0:0:0:0')
    Device('/sys/devices/pci0000:00/0000:00:14.0/usb1/1-2/1-2.4/1-2.4.3/1-2.4.3:1.0/host0/target0:0:0/0:0:0:0/scsi_disk/0:0:0:0')
    Device('/sys/devices/pci0000:00/0000:00:14.0/usb1/1-2/1-2.4/1-2.4.3/1-2.4.3:1.0/host0/target0:0:0/0:0:0:0/scsi_generic/sg0')
    Device('/sys/devices/pci0000:00/0000:00:14.0/usb1/1-2/1-2.4/1-2.4.3/1-2.4.3:1.1')
    Device('/sys/devices/pci0000:00/0000:00:14.0/usb1/1-2/1-2.4/1-2.4.3/1-2.4.3:1.1/tty/ttyACM0')


    martin@martin-Lenovo-YOGA-900-13ISK2:~/sistemi/git/scripts/public/prism/drivers/iba01$ lsusb -t
    /:  Bus 02.Port 1: Dev 1, Class=root_hub, Driver=xhci_hcd/6p, 5000M
    /:  Bus 01.Port 1: Dev 1, Class=root_hub, Driver=xhci_hcd/12p, 480M
        |__ Port 2: Dev 103, If 0, Class=Hub, Driver=hub/4p, 480M
            |__ Port 1: Dev 104, If 1, Class=Human Interface Device, Driver=usbhid, 1.5M
            |__ Port 1: Dev 104, If 0, Class=Human Interface Device, Driver=usbhid, 1.5M
            |__ Port 4: Dev 22, If 0, Class=Hub, Driver=hub/4p, 12M
                |__ Port 3: Dev 24, If 1, Class=Communications, Driver=cdc_acm, 12M
                |__ Port 3: Dev 24, If 2, Class=CDC Data, Driver=cdc_acm, 12M
                |__ Port 3: Dev 24, If 0, Class=Mass Storage, Driver=usb-storage, 12M
                |__ Port 1: Dev 23, If 0, Class=Vendor Specific Class, Driver=ftdi_sio, 12M
                |__ Port 1: Dev 23, If 1, Class=Vendor Specific Class, Driver=ftdi_sio, 12M
            |__ Port 2: Dev 25, If 0, Class=Human Interface Device, Driver=usbhid, 1.5M
        |__ Port 7: Dev 3, If 0, Class=Wireless, Driver=btusb, 12M
        |__ Port 7: Dev 3, If 1, Class=Wireless, Driver=btusb, 12M

    >>> from pyftdi.ftdi import Ftdi
    >>> Ftdi().open_from_url('ftdi:///?')
    Available interfaces:
      ftdi://ftdi:2232/1   (Dual RS232-HS)
      ftdi://ftdi:2232/2   (Dual RS232-HS)


"""