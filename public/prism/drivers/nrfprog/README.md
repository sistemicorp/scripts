NRF prog Install 
================

Versions for these instructions:

    nrfjprog version: 10.18.1 external
    JLinkARM.dll version: 7.82f


1) Download tools

https://www.nordicsemi.com/Products/Development-tools/nrf-command-line-tools/download

Open the `deb` file with "software installer" (not archive manager) and install.

NRF tools should get installed here,

    $ ll /opt/nrf-command-line-tools/bin
    total 16132
    drwxr-xr-x 2 root root     4096 Dec 12 13:57 ./
    drwxr-xr-x 7 root root     4096 Dec 12 13:57 ../
    -rwxr-xr-x 1 root root 10238112 Oct 13 10:12 jlinkarm_nrf_worker_linux*
    -rwxr-xr-x 1 root root  2105336 Oct 13 10:12 mergehex*
    -rwxr-xr-x 1 root root  4164848 Oct 13 10:12 nrfjprog*

Get familiar with the CLI: 

    $ nrfjprog
    
    Usage: 
    -------------------------------------------------------------------------------
     -q  --quiet                 Reduces the stdout info. Must be combined with
                                 another command.
     -h  --help                  Displays this help.
     -v  --version               Displays the nrfjprog and dll versions.
    ... 



There also seems to be a Python wrapper:
https://www.nordicsemi.com/Products/Development-tools/nRF-Pynrfjprog/Download?lang=en#infotabs
(though would have to be supported in prism (a08) image, so don't use this until its supported)

2) In order for Prism to run this tool, it needs to be in scripts. 
 
Copy the NRF binaries to this folder


    cp /opt/nrf-command-line-tools/lib/* .
    cp /opt/nrf-command-line-tools/bin/* .
    cp /opt/nrf-command-line-tools/share/config.toml .


The directory should look like this when done,

    ~/git/scripts/public/prism/drivers/nrfprog$ ll
    total 87540
    drwxrwxr-x  3 martin martin     4096 Dec 12 15:41 ./
    drwxr-xr-x 10 martin martin     4096 Dec 12 13:54 ../
    -rw-r--r--  1 martin martin     5855 Dec 12 14:14 config.toml
    -rw-rw-r--  1 martin martin     4681 Dec 12 15:39 hwdrv_nrfprog.py
    -rwxr-xr-x  1 martin martin 10238112 Dec 12 14:11 jlinkarm_nrf_worker_linux*
    -rw-r--r--  1 martin martin  2821064 Dec 12 14:16 libhighlevelnrfjprog.so
    -rw-r--r--  1 martin martin 10511144 Dec 12 14:16 libjlinkarm_nrf51_nrfjprogdll.so
    -rw-r--r--  1 martin martin 10511144 Dec 12 14:16 libjlinkarm_nrf52_nrfjprogdll.so
    -rw-r--r--  1 martin martin 10511144 Dec 12 14:16 libjlinkarm_nrf53_nrfjprogdll.so
    -rw-r--r--  1 martin martin 10511144 Dec 12 14:16 libjlinkarm_nrf91_nrfjprogdll.so
    -rw-r--r--  1 martin martin 11176792 Dec 12 14:16 libjlinkarm_unknown_nrfjprogdll.so
    -rw-r--r--  1 martin martin  8149520 Dec 12 14:16 libnrfdfu.so
    -rw-r--r--  1 martin martin 10981656 Dec 12 14:16 libnrfjprogdll.so
    -rwxr-xr-x  1 martin martin  4164848 Dec 12 14:11 nrfjprog*
    -rw-rw-r--  1 martin martin     2460 Dec 12 15:39 NRFProg.py
    drwxrwxr-x  2 martin martin     4096 Dec 12 14:29 __pycache__/
    -rw-rw-r--  1 martin martin     2003 Dec 12 14:24 README.md
    -rw-rw-r--  1 martin martin      460 Dec  9 10:30 stublogger.py



3) Confirm tool is working, have JLINK connected and try,


    $ ./nrfjprog --ids --expand
    ---------- Emulators ----------
    serial number:      821009733
    connection type:    USB
    -------------------------------
    serial number:      821009774
    connection type:    USB
    -------------------------------


4) Confirm `hwdrv_nrfprog.py` can find the Seggers.  
   Run `hwdrv_nrfprog.py` from within PyCharm, and remember to set the
   working directory to `~/git/scripts`


    INFO:hwdrv_nrfprog.py:Start
    INFO:hwdrv_nrfprog.py:[{'id': 'SEGGER_J-Link_000821009733', 'usb_path': '/devices/pci0000:00/0000:00:08.1/0000:03:00.3/usb1/1-2/1-2.1/1-2.1.4/1-2.1.4.2', 'version': '0.0.1', 'serial': '000821009733'}, {'id': 'SEGGER_J-Link_000821009774', 'usb_path': '/devices/pci0000:00/0000:00:08.1/0000:03:00.3/usb1/1-2/1-2.2/1-2.2.4/1-2.2.4.2', 'version': '0.0.1', 'serial': '000821009774'}]
    INFO:sys_log:HWDriver:hwdrv_nrfprog.py: Found 2!
    INFO:hwdrv_nrfprog.py:Done: 2 channels
    INFO:root:Number channels: 2

