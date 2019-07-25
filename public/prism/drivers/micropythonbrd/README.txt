How to use these files...

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


