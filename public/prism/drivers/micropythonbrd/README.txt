How to use these files...

0) How to setup a "fresh" MicroPython Pyboard ver 1.1 for use with Sistemi Prism:

    A) Boot the Pyboard into DFU mode, by shorting the 3V3 pin to the BOOT0 pin and resetting (button) the board.
        See https://github.com/micropython/micropython/wiki/Pyboard-Firmware-Update
    B) Update the firmware with this command,
        $ sudo python3 pydfu.py -u pybv11-thread-20190730-v1.11-182-g7c15e50eb.dfu
    C) Set the ID of the board, (All MicroPython boards should have a unique ID),
        $ python3 upybrd_cli.py --port /dev/ttyACM0 --set-id 2

1) All files names upyb_*.py need to be copied to the MicroPyboard.
   Use rshell (put link to install rshell here) or ampy.

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
        /home/martin/sistemi/git/scripts/public/prism/drivers/micropythonbrd> cp upyb_*.py /flash
        /home/martin/sistemi/git/scripts/public/prism/drivers/micropythonbrd>


2) MicroPyboards must get an "ID file" written to them to be used with the Prism system.
   Use the upybrd_cli.py program to set the ID.

   Example session:
          martin@martin-Lenovo:~/sistemi/git/scripts/public/prism/drivers/micropythonbrd$ python3 upybrd_cli.py --port /dev/ttyACM0 --set-id 2
          INFO  112 Looking for Pyboard in ['/dev/ttyACM0']
          INFO  130 Found [{'port': '/dev/ttyACM0', 'id': 2, 'version': '0.0.1'}]
          INFO  212 removing ID: /flash/ID2 - 3 bytes
          INFO  221 Setting ID: ID2


3) The upybrd_cli.py can be used for other things, like testing code.  See '--help' for all its functions.
   For example, instead of using rshell to copy files over, one can use upybrd_cly.py,

    martin@martin-Lenovo:~/sistemi/git/scripts/public/prism/drivers/micropythonbrd$ python3 upybrd_cli.py --port /dev/ttyACM0 --copy upyb_INA220.py -v
     DEBUG   95 Done
     DEBUG  137 open /dev/ttyACM0
     DEBUG  142 close


4) How to debug problems with code on the MicroPython?

   A) Run the code directly via rshell.  Here is an example session, starting after entering the rshell,

        /home/martin/sistemi/git/scripts/public/prism/drivers/micropythonbrd> repl
        Entering REPL. Use Control-X to exit.
        >
        MicroPython v1.11 on 2019-05-29; PYBv1.1 with STM32F405RG
        Type "help()" for more information.
        >>>
        >>> import upyb_server_01
        >>> upyb_server_01.server.adc_read_multi({"pins": ['X19']})
        >>> upyb_server_01.server.peek(all=True)
        [{'success': True, 'value': 'scheduled', 'method': 'adc_read_multi'}, {'success': True, 'value': [array('H', [329, 353, 388, 365, 393, 374, 381, 412, 374, 398, 388, 364, 400, 367, 400, 382, 384, 387, 361, 391, 384, 361, 398, 372, 398, 390, 367, 408, 374, 403, 382, 389, 395, 365, 393, 382, 391, 394, 368, 398, 390, 369, 398, 376, 395, 384, 364, 404, 374, 403, 389, 367, 405, 376, 400, 382, 388, 388, 365, 393, 379, 386, 387, 362, 398, 387, 364, 404, 375, 405, 388, 369, 403, 371, 394, 386, 364, 402, 373, 404, 387, 364, 406, 377, 400, 384, 365, 404, 374, 409, 387, 361, 403, 375, 406, 391, 372, 410, 375, 408])], 'method': 'adc_read_multi_results'}]
        True
        >>>

   B) Use the cli, upybrd_cli_server.py to write test code in a simple environment.

   C) Error "could not exec command" is often an issue with arguments, make sure new functions match argument patterns.
   

5) How to program/update the pyboard?

    See,
        https://github.com/micropython/micropython/wiki/Pyboard-Firmware-Update
        https://github.com/micropython/micropython/blob/master/tools/pydfu.py

    Example session,

        $ sudo python3 pydfu.py -u pybv11-thread-20190730-v1.11-182-g7c15e50eb.dfu
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




