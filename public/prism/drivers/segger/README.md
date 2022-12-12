Segger Install 
==============


1) Download tools

    https://www.segger.com/downloads/jlink/JLink_Linux_x86_64.deb

    Open this file with "software installer" (not archive manager) and install.

   Get familiar with the CLI: https://wiki.segger.com/J-Link_Commander


   Is this useful?
   https://www.segger.com/products/debug-probes/j-link/technology/j-link-sdk/#the-j-link-sdk-package


2) Connect to Jlink

   The device may upgrade,


    $ JLinkExe
    SEGGER J-Link Commander V7.82f (Compiled Dec  8 2022 09:38:51)
    DLL version V7.82f, compiled Dec  8 2022 09:38:25
    
    Connecting to J-Link via USB...Updating firmware:  J-Link V11 compiled Dec  5 2022 13:50:41
    Replacing firmware: J-Link V11 compiled Nov  2 2021 11:11:52
    QPainter::setFont: Painter not active
    Waiting for new firmware to boot
    New firmware booted successfully
    O.K.
    Firmware: J-Link V11 compiled Dec  5 2022 13:50:41
    Hardware version: V11.00
    J-Link uptime (since boot): 0d 00h 00m 00s
    S/N: 821009733
    License(s): GDB
    USB speed mode: High speed (480 MBit/s)
    VTref=0.000V

3) TODO...

JLinkExe is not really a CLI... its a shell. Not sure how going to interface to that shell.

