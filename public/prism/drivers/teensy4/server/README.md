Instructions for uploading server file to Teensy.

1) Install Arduino IDE (https://www.arduino.cc/en/software).
   Use version 1.8.19
   Do not use the AppImage version, use the Linux Zip file.

   Download the Teensy add in for Arduino from here: https://www.pjrc.com/teensy/td_download.html
   Download and install the Linux UDEV rules: https://www.pjrc.com/teensy/00-teensy.rules

   Optional CLI loader:
      https://www.pjrc.com/teensy/loader_cli.html
      https://github.com/PaulStoffregen/teensy_loader_cli

2) Start the Arduino IDE
   - Select the board, Tools->Board->TeensyArduino->Teensy41

3) Set the Prism Sketch folder
   - File->Preferences->Sketchbook Location
   - Set the path appropriately, for example,
     /home/martin/git/scripts/public/prism/drivers/teensy4/server

4) Open teensy4_server.ino with the Arduino IDE.

5) Go to the top ribbon menu and select 'Sketch'.

6) In the drop down menu select 'Include Library' then 'Manage Libraries' to open the Library Manager.

7) In the Library Manager put simpleRPC in the search bar. Install the library.

8) In the Library Manager put ArduinoJson in the search bar. Install the library.

9) Copy the version.h file in this directory.

10) Go to 'C:\YourPC\Documents\Arduino\libraries' or where your Arduino Libraries are installed.

11) Create a folder named 'version' and paste the version.h file into the folder.

12) Generating a Hex file from Arduino
    - In Arduino IDE, File->Preferences, turn on Show Verbose Output During: Compilation
    - Compile the sketch by pressing the Arduino IDE Verify (check mark) icon
    - Note the panel output for the location of the compiled files,


    /home/martin/Downloads/arduino-1.8.19-linux64/arduino-1.8.19/hardware/teensy/../tools/teensy_size /tmp/arduino_build_864038/teensy4_server.ino.elf

13) Plug your Teensy into your computer.

14) Go to Arduino IDE and upload the sketch onto the Teensy.

15) Program Teensy with command line tool,


    martin@martin-virtual-machine:~/git/scripts/public/prism/drivers/teensy4/server$ ./teensy_loader_cli --mcu=TEENSY41 -w -v /tmp/arduino_build_864038/teensy4_server.ino.hex 
    Teensy Loader, Command Line, Version 2.2
    Read "/tmp/arduino_build_864038/teensy4_server.ino.hex": 70656 bytes, 0.9% usage
    Waiting for Teensy device...
     (hint: press the reset button)
    Found HalfKay Bootloader
    Read "/tmp/arduino_build_864038/teensy4_server.ino.hex": 70656 bytes, 0.9% usage
    Programming..................................................................
    Booting


--Teensy4 CLI Examples--


    martin@martin-virtual-machine:~/git/scripts$ source venv/bin/activate
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

