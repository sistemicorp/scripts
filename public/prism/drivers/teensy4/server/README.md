Instructions for uploading server file to Teensy.

Tested versions (2026-10-25), use these unless you are updating and re-testing,

    Arduino IDE 2.3.6 (zip, see the BOND server README for the install steps)
    Teensy core (teensy:avr) 1.62.0
    simpleRPC 3.2.0
    ArduinoJson 7.4.3

1) Install the Arduino IDE and the Teensy add in.

   - Arduino IDE: https://www.arduino.cc/en/software
   - Teensy add in: https://www.pjrc.com/teensy/td_download.html
   - Linux UDEV rules (also in this folder): https://www.pjrc.com/teensy/00-teensy.rules

   The teensy CLI loader is used by Prism scripts to load teensy, and that binary
   is stored in `scripts` repo. libusb-dev is required to use it.

        sudo apt-get install libusb-dev

   Optional CLI loader source and information:
      https://www.pjrc.com/teensy/loader_cli.html
      https://github.com/PaulStoffregen/teensy_loader_cli

2) Start the Arduino IDE
   - Select the board, Tools->Board->TeensyArduino->Teensy41

3) Install the libraries with the Library Manager (Sketch->Include Library->Manage Libraries),
   simpleRPC and ArduinoJson, at the versions above. The libraries are not stored in this repo.

4) Open teensy4_server/teensy4_server.ino with the Arduino IDE.
   - `version.h` (next to the sketch) holds the firmware version, the Python driver reads the
     same file and refuses a Teensy running a different version. Bump it on every change.

5) Build and program,
   - In the IDE, Verify (check mark) then Upload, or
   - from the command line, using the arduino-cli bundled with the IDE,

         ~/git/scripts/public/prism/drivers/teensy4/server/teensy4_server$ \
           /opt/arduino-ide_2.3.6_Linux_64bit/resources/app/lib/backend/resources/arduino-cli compile \
             --config-file ~/.arduinoIDE/arduino-cli.yaml -b teensy:avr:teensy41 --output-dir /tmp/t4_build .

   - Copy the hex to the script assets, for Prism to program Teensys,

         cp /tmp/t4_build/teensy4_server.ino.hex ~/git/scripts/public/prism/scripts/example/teensy4_v0/assets/

6) Plug your Teensy into your computer.

7) Go to Arduino IDE and upload the sketch onto the Teensy.

8) Program Teensy with command line tool,


    martin@martin-staric2:~/git/scripts/public/prism/drivers/teensy4/server$ ./teensy_loader_cli --mcu=TEENSY41 -w -v ../../../../prism/scripts/example/teensy4_v0/assets/teensy4_server.ino.hex 
    Teensy Loader, Command Line, Version 2.2
    Read "../../../../prism/scripts/example/teensy4_v0/assets/teensy4_server.ino.hex": 70656 bytes, 0.9% usage
    Found HalfKay Bootloader
    Programming..................................................................
    Booting



9) Showing Teensy devices with lsusb,


    martin@martin-virtual-machine:~/git/scripts/public/prism/drivers/teensy4/server$ lsusb
    Bus 001 Device 050: ID 16c0:0486 Van Ooijen Technische Informatica Teensyduino RawHID
    Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
    Bus 002 Device 004: ID 0e0f:0008 VMware, Inc. Virtual Bluetooth Adapter
    Bus 002 Device 003: ID 0e0f:0002 VMware, Inc. Virtual USB Hub
    Bus 002 Device 002: ID 0e0f:0003 VMware, Inc. Virtual Mouse
    Bus 002 Device 001: ID 1d6b:0001 Linux Foundation 1.1 root hub


After programming, the teensy will show up as a serial, like so,

    martin@martin-virtual-machine:~/git/scripts/public/prism/drivers/teensy4/server$ lsusb
    Bus 001 Device 053: ID 16c0:0483 Van Ooijen Technische Informatica Teensyduino Serial



10) Teensy RPC Development

    - Prism calls Teensy's RPC server from Python, and there is a way to test that API from Python using 
      a command line (CLI) interface.
    - Using the Teensy_cli.py program is how you will be testing/developing new APIs to the Teensy4 server.

--Teensy4 CLI Examples--


    martin@martin-virtual-machine:~/git/scripts$ source venv/bin/activate  # only if using venv
    (venv) martin@martin-virtual-machine:~/git/scripts$ python3 public/prism/drivers/teensy4/Teensy4_cli.py -p /dev/ttyACM0 --version
          Teensy4.py       INFO   79 attempting to install Teensy on port /dev/ttyACM0
          Teensy4.py       INFO   97 Installed Teensy on port /dev/ttyACM0
          Teensy4_cli.py   INFO   90 Version 0.1.0
    (venv) martin@martin-virtual-machine:~/git/scripts$ python3 public/prism/drivers/teensy4/Teensy4_cli.py -p /dev/ttyACM0 led --on
              Teensy4.py   INFO   79 attempting to install Teensy on port /dev/ttyACM0
              Teensy4.py   INFO   97 Installed Teensy on port /dev/ttyACM0
          Teensy4_cli.py   INFO   53 led: Namespace(port='/dev/ttyACM0', verbose=0, show_version=False, _cmd='led', _on=True, _off=False)
          Teensy4_cli.py   INFO   56 ON: turn on LED
          Teensy4_cli.py   INFO   60 {'success': True, 'method': 'set_led', 'result': {'state': 'on'}}
          Teensy4_cli.py   INFO  100 all tests passed
              Teensy4.py   INFO  105 closing
    (venv) martin@martin-virtual-machine:~/git/scripts$ python3 public/prism/drivers/teensy4/Teensy4_cli.py -p /dev/ttyACM0 led --off
              Teensy4.py   INFO   79 attempting to install Teensy on port /dev/ttyACM0
              Teensy4.py   INFO   97 Installed Teensy on port /dev/ttyACM0
          Teensy4_cli.py   INFO   53 led: Namespace(port='/dev/ttyACM0', verbose=0, show_version=False, _cmd='led', _on=False, _off=True)
          Teensy4_cli.py   INFO   64 OFF: turn off LED
          Teensy4_cli.py   INFO   68 {'success': True, 'method': 'set_led', 'result': {'state': 'off'}}
          Teensy4_cli.py   INFO  100 all tests passed
              Teensy4.py   INFO  105 closing


11) Your own Teensy Development

   - the code here (~/public/prism/drivers/teensy4) is a starting point (template) for creating
     your own Teensy4 code.
   - copy ~/public/prism/drivers/teensy4 to your own driver folder, for example, ~/public/prism/drivers/company_teensy4

