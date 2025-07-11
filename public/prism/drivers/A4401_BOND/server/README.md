Instructions for Teensy 4.x development:

These instructions are for developers who need to modify BOND behaviour, or to add additional
functionality.  You should not need to modify Teensy code if you are just using BOND.  The 
Teensy code found in the Prism BOND example is sufficient to use BOND.

1) Follow setup instructions here, https://www.pjrc.com/teensy/td_download.html

   ![A test image](readme_images/rm_install_arduino_01.png)

   Do not use the AppImage version, use the Linux Zip file.
   
   Download and install the Linux UDEV rules: https://www.pjrc.com/teensy/00-teensy.rules

   The teensy CLI loader is used by Prism scripts to load teensy, and that binary
   is stored in `scripts` repo. libusb-dev is required to use it.

        sudo apt-get install libusb-dev
   
   Optional CLI loader source and information:
      https://www.pjrc.com/teensy/loader_cli.html
      https://github.com/PaulStoffregen/teensy_loader_cli

2) Start the Arduino IDE
   - Select the board, Tools->Board->TeensyArduino->Teensy41

![A test image](readme_images/rm_install_arduino_02.png)

![A test image](readme_images/rm_install_arduino_03.png)


3) Install library dependencies: Go to the top ribbon menu and select 'Sketch'.
   - In the drop down menu select 'Include Library' then 'Manage Libraries' to open the Library Manager.
   - In the Library Manager put simpleRPC (ver 3.2.0) in the search bar. Install the library.
   - In the Library Manager put ArduinoJson (ver 7.4.2) in the search bar. Install the library.
   - In the Library Manager put INA219_WE (ver 1.3.8) in the search bar. Install the library.

4) Open teensy4_server.ino with the Arduino IDE.  This is where you will find `setup()` and `loop()`.

5) Generating a Hex file from Arduino
    - In Arduino IDE, File->Preferences, turn on Show Verbose Output During: Compilation
    - Compile the sketch by pressing the Arduino IDE Verify (check mark) icon (top-left)
    - Note the panel output for the location of the compiled file, you will need this in later steps,


    /home/martin/.cache/arduino/sketches/AB98538F1B6B747D1325AD62F117F594/teensy4_server.ino.elf


6) Connect the BOND to power and Teensy to USB. Note than BOND has a built in USB Hub, and just
a short USB cable is needed to plug to the Teensy.

7) Go to Arduino IDE and upload the sketch onto the Teensy by pressing the `Upload` icon in the upper left.
A Teensy pop-up window will appear showing the status of the Teensy as it uploads.  You do not need to press
the button, things should happen automatically.

8) OPTIONAL: Program Teensy with command line tool,


    martin@martin-staric2:~/git/scripts/public/prism/drivers/teensy4/server$ ./teensy_loader_cli --mcu=TEENSY41 -w -v ../../../../prism/scripts/example/teensy4_v0/assets/teensy4_server.ino.hex 
    Teensy Loader, Command Line, Version 2.2
    Read "../../../../prism/scripts/example/teensy4_v0/assets/teensy4_server.ino.hex": 70656 bytes, 0.9% usage
    Found HalfKay Bootloader
    Programming..................................................................
    Booting

NOTE: The Teensy CLI loader is used to update BOND's Teensy from a Prism script.  The Teensy
ELF is copied to an assets folder and used by the CLI.

9) DEBUG: Showing Teensy devices with lsusb,


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
      a command line (CLI) interface, without using Prism.
    - Using the Teensy_cli.py program is how you will be testing/developing new APIs to the Teensy4 server.

--Teensy4 CLI Examples--


    (venv) martin@martin-ThinkPad-L13:~/git/scripts/public/prism/drivers/A4401_BOND$ python A4401_BOND_cli.py -p /dev/ttyACM0 version
           A4401_BOND.py   INFO  112 version 0.1.0
           A4401_BOND.py   INFO  121 attempting to install Teensy on port /dev/ttyACM0
           A4401_BOND.py   INFO  321 version
           A4401_BOND.py   INFO  266 {'success': True, 'method': 'version', 'result': {'version': '0.1.0'}}
           A4401_BOND.py   INFO  330 status
           A4401_BOND.py   INFO  266 {'success': True, 'method': 'status', 'result': {'setup_fail_code': 0, 'stack_kb': 402, 'heap_kb': 496, 'psram_kb': 786432}}
           A4401_BOND.py   INFO  182 1 init
           A4401_BOND.py   INFO  184 1 pin 1 init {'mode': 'DAC,GPO', 'port': '10,1'}
           A4401_BOND.py   INFO  184 1 pin 2 init {'mode': 'GPO', 'port': '7'}
           A4401_BOND.py   INFO  184 1 pin 3 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  184 1 pin 4 init {'mode': 'GPO', 'port': '8'}
           A4401_BOND.py   INFO  184 1 pin 5 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  184 1 pin 6 init {'mode': 'DAC', 'port': '9'}
           A4401_BOND.py   INFO  184 1 pin 7 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  184 1 pin 8 init {'mode': 'DAC', 'port': '5'}
           A4401_BOND.py   INFO  184 1 pin 9 init {'mode': 'ADC', 'port': '6'}
           A4401_BOND.py   INFO  184 1 pin 10 init {'mode': 'GPO', 'port': '4'}
           A4401_BOND.py   INFO  184 1 pin 11 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  184 1 pin 12 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  184 1 pin 13 init {'mode': 'GPI', 'port': '0'}
           A4401_BOND.py   INFO  184 1 pin 14 init {'mode': 'ADC', 'port': '3'}
           A4401_BOND.py   INFO  184 1 pin 15 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  184 1 pin 16 init {'mode': 'ADC', 'port': '2'}
           A4401_BOND.py   INFO  184 1 pin 17 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  184 1 pin 18 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  184 1 pin 19 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  184 1 pin 20 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  209 ports_dac [5, 9, 10]
           A4401_BOND.py   INFO  210 ports_adc [2, 3, 6, 11]
           A4401_BOND.py   INFO  211 ports_gpo [1, 4, 7, 8]
           A4401_BOND.py   INFO  212 ports_gpi [0]
           A4401_BOND.py   INFO  266 {'success': True, 'method': 'bond_max_hdr_init', 'result': {'regs_seq_len': 35}}
           A4401_BOND.py   INFO  154 Installed Teensy-A4401BOND on port /dev/ttyACM0
       A4401_BOND_cli.py   INFO  267 version: Namespace(port='/dev/ttyACM0', verbose=0, _cmd='version')
           A4401_BOND.py   INFO  321 version
           A4401_BOND.py   INFO  266 {'success': True, 'method': 'version', 'result': {'version': '0.1.0'}}
       A4401_BOND_cli.py   INFO  270 {'success': True, 'method': 'version', 'result': {'version': '0.1.0'}}
       A4401_BOND_cli.py   INFO  505 Success
           A4401_BOND.py   INFO  165 closing /dev/ttyACM0
    (venv) martin@martin-ThinkPad-L13:~/git/scripts/public/prism/drivers/A4401_BOND$ python A4401_BOND_cli.py -p /dev/ttyACM0 led --on
    ...
    (venv) martin@martin-ThinkPad-L13:~/git/scripts/public/prism/drivers/A4401_BOND$ python A4401_BOND_cli.py -p /dev/ttyACM0 led --off
    ...

