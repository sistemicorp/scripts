Instructions for uploading server file to Teensy.

1)Install Arduino IDE (https://www.arduino.cc/en/software).

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

--Teensy4 CLI Example--

    Microsoft Windows
    (c) 2019 Microsoft Corporation. All rights reserved.
    
    (venv) C:\Users\User's PC\PycharmProjects\scripts>cd public/prism/drivers/teensy4
    
    (venv) C:\Users\User's PC\PycharmProjects\scripts\public\prism\drivers\teensy4>python Teensy4_cli.py --p COM5 --version
              Teensy4.py   INFO   69 attempting to install Teensy on port COM5
              Teensy4.py   INFO   99 Installed Teensy on port COM5
          Teensy4_cli.py   INFO   92 Version 0.1.0
