How to use these files... Read all of this, lots of info...

1) How to setup a "fresh" MicroPython Pyboard ver 1.1 for use with Sistemi Prism:

    A) Boot the Pyboard into DFU mode, by shorting the 3V3 pin to the BOOT0 pin and resetting (button) the board.
        See https://github.com/micropython/micropython/wiki/Pyboard-Firmware-Update
    B) Update the firmware with this command,
        $ sudo python3 pydfu.py -m -u pybv11-thread-20190730-v1.11-182-g7c15e50eb.dfu
    C) Copy all the upyb_*.py files to the MicroPython Board, use rshell, see #2.

    The pyboard should now be ready to go.

2) All files names iba01_*.py need to be copied to the MicroPyboard.

   Use the script: ampy_put_all.sh

   Or, use rshell (put link to install rshell here) or ampy to copy just one file.
   ampy (see script) is more reliable than rshell (v0.26).
   example rshell session:
        martin@martin-Lenovo:~/sistemi/git/scripts/public/prism/drivers/micropythonbrd$ rshell
        Connecting to /dev/ttyACM0 (buffer-size 512)...
        Trying to connect to REPL . connected
        Testing if sys.stdin.buffer exists ... Y
        Retrieving root directories ... /flash/
        Setting time ... Jul 23, 2019 22:04:02
        Evaluating board_name ... pyboard
        Retrieving time epoch ... Jan 01, 2000
        Welcome to rshell. Use Control-D (or the exit command) to exit rshell.
        /home/martin/sistemi/git/scripts/public/prism/drivers/micropythonbrd> cp iba01_*.py /flash
        /home/martin/sistemi/git/scripts/public/prism/drivers/micropythonbrd>


3) The MicroPyBoard_cli.py can be used for other things, like testing code.  See '--help' for all its functions.
   For example, instead of using rshell to copy files over, one can use upybrd_cly.py,

    martin@martin-Lenovo:~/sistemi/git/scripts/public/prism/drivers/micropythonbrd$ python3 MicroPyBoard_cli.py --port /dev/ttyACM0 --copy iba01_supply12.py -v
     DEBUG   95 Done
     DEBUG  137 open /dev/ttyACM0
     DEBUG  142 close


4) How to debug problems with code on the MicroPython?

   A) Run the code directly via rshell.  This is generally the ONLY way to find out if new code is syntax
      correct on the target.  If the MicroPython code has an error, the server hides the error message, so you
      don't see it.  Using the interactive REPL is the BEST way to see the issue.
      Here is an example session, starting after entering the rshell,

        $ rshell
        Connecting to /dev/ttyACM0 (buffer-size 512)...
        Trying to connect to REPL  connected
        Testing if sys.stdin.buffer exists ... Y
        Retrieving root directories ... /flash/
        Setting time ... Oct 25, 2019 15:39:48
        Evaluating board_name ... pyboard
        Retrieving time epoch ... Jan 01, 2000
        Welcome to rshell. Use Control-D (or the exit command) to exit rshell.
        /home/martin/sistemi/git/p01-upyrpc> repl
        Entering REPL. Use Control-X to exit.
        >
        MicroPython v1.11-182-g7c15e50eb on 2019-07-30; PYBv1.1 with STM32F405RG
        Type "help()" for more information.
        >>>
        >>> import upyrpc_main
        >>> upyrpc_main.upyrpc.cmd({'method': 'version', 'args': {}})
        True
        >>> upyrpc_main.upyrpc.ret(method='version')
        [{'success': True, 'value': 'upyrpc_main    :version   : 180: testing message', 'method': '_debug'}]
        True
        >>> upyrpc_main.upyrpc.ret(method='version')
        [{'success': True, 'value': {'uname': {'machine': 'PYBv1.1 with STM32F405RG', 'nodename': 'pyboard', 'version': 'v1.11-182-g7c15e50eb on 2019-07-30', 'release': '1.11.0', 'sysname': 'pyboard'}, 'version': '0.2'}, 'method': 'version'}]
        True
        >>> upyrpc_main.upyrpc.ret(method='version')
        []
        True
        >>>

   B) Use the cli, IBA01_cli.py to write test code in a simple environment.

   C) Error "could not exec command" is often an issue with arguments, make sure new functions match argument patterns.


5) How to program/update the pyboard?

    See,
        https://github.com/micropython/micropython/wiki/Pyboard-Firmware-Update
        https://github.com/micropython/micropython/blob/master/tools/pydfu.py

    Example session,

        $ sudo python3 pydfu.py -m -u pybv11-thread-20190730-v1.11-182-g7c15e50eb.dfu
        Mass erase...
        File: pybv11-thread-20190730-v1.11-182-g7c15e50eb.dfu
            b'DfuSe' v1, image size: 337101, targets: 1
            b'Target' 0, alt setting: 0, name: "ST...", size: 336816, elements: 2
              0, address: 0x08000000, size: 14816
              1, address: 0x08020000, size: 321984
            usb: 0483:df11, device: 0x0000, dfu: 0x011a, b'UFD', 16, 0x1801e670
        Writing memory...
        0x08000000   14816 [=========================] 100%
        0x08020000  321984 [=========================] 100%
        Exiting DFU...


6) How to run commands via the "server" on the MicroPython?

    A) steps in #1 must have been done previously.
    B) Run this command to get latest functions,

        python3 IBA01_cli.py --help

       or to get help on sub-commands,

        python3 IBA01_cli.py adc --help

7) Use SD card or flash filesystem?  The choice is predicated on a few factors,

    a) The PyBoard v1.1 filesystem has a capacity of ~110k.  If the files fit, you can use this.
    b) The notion of the SLOT# file determines the position of the IBA01 in the list of fixtures
       in Prism test view.  If, for example, SLOT0 IBA01 test fixture becomes broken and must be removed, then
       the order of fixtures becomes, SLOT1, SLOT2, SLOT3, and these will be mapped to channel 0, 1, 2
       in Prism.  This might be confusing.  If you use the SD card for the filesystem, then
       you can move the cards so that SLOT0 SD card is physically in a logical fixture.  The SD cards
       should be labelled with the SLOT#.

