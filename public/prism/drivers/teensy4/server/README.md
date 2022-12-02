Instructions for uploading server file to Teensy.

1)Install Arduino IDE (https://www.arduino.cc/en/software).
  Use version 1.8.19
  Do not use the AppImage version, use the Linux Zip file.

  Download the Teensy add in for Arduino from here: https://www.pjrc.com/teensy/td_download.html
  Download and install the Linux UDEV rules: https://www.pjrc.com/teensy/00-teensy.rules


2)Copy the absolute path of the server directory (Ctrl + Shift + C on the server directory)
    - ex. C:\Users\User's PC\PycharmProjects\scripts\public\prism\drivers\teensy4\server

3)Go to the top ribbon menu and select 'File'

4)In the drop down menu select 'Preferences' and past the server Path into 'Sketchbook Location'

5)Open teensy4_server.ino with the Arduino IDE.

6)Go to the top ribbon menu and select 'Sketch'.

7)In the drop down menu select 'Include Library' then 'Manage Libraries' to open the Library Manager.

8)In the Library Manager put simpleRPC in the search bar. Install the library.

9)In the Library Manager put ArduinoJson in the search bar. Install the library.

10)Copy the version.h file in this directory.

11)Go to 'C:\YourPC\Documents\Arduino\libraries' or where your Arduino Libraries are installed.

12)Create a folder named 'version' and paste the version.h file into the folder.

13)Plug your Teensy into your computer.

14)Go to Arduino IDE and upload the sketch onto the Teensy.

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


--Resources for automizing Server Code Updates--

    https://www.pjrc.com/teensy/loader_cli.html

    An Error I came across:

    C:\Users\User's PC\Documents\teensy_loader_cli-master>MinGW32-make
    rm -f teensy_loader_cli teensy_loader_cli.exe*
    process_begin: CreateProcess(NULL, rm -f teensy_loader_cli teensy_loader_cli.exe*, ...) failed.
    make (e=2): The system cannot find the file specified.
    Makefile:59: recipe for target 'clean' failed
    MinGW32-make: *** [clean] Error 2