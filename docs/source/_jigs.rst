Test Jigs
#########

Test Jigs are used in production to test your product, which is referred to as Device Under Test (DUT).
These are custom designed fixtures that interface your product (DUT) to the Prism programs.

In general, it is your responsibility to develop your own test jigs based on your requirements.
Sistemi (in general) does not build jigs.  That being said, Sistemi has a reference platform that you may
be able to use, perhaps with some modifications.

.. image:: static/Screenshot_jigs_01.png


.. contents::
   :local:


Definitions
===========

Interface Board
---------------

* A Printed Circuit Board (PCB) that has spring probes and some type of controller that
  the Prism can talk to, to take measurements, and otherwise control the stimulus to the DUT.
* Are custom developed depending on the DUT requirements

  * Sistemi has developed a reference design based on MicroPython board, see TBD

Interface Controller
--------------------

* A device with USB connectivity and a processor in which Prism can control and
  otherwise interface to
* Examples that could be used, Arduino, MicroPython, RaspBerry Pi, etc
* An ``Interface Controller`` may be designed into the ``Interface Board`` or
  it can be a daughter card that plugs into an ``Interface Board``

  * Sistemi has developed a reference design based on MicroPython board, see TBD

Bed of Nails
------------

* An arrangement of spring mounted probes that make electrical connection to the DUT
* the DUT has test points, which are large pads that the spring probes will make contact with

Nest
----

* A landing site for the DUT
* designed to make alignment between the Bed of Nails and the DUT test points

Considerations
==============

* Bed of Nails (probes) can wear out over time, you may want to consider a design that
  allows the Bed Of Nails to be replaced.  This ultimately depends on the cost of replacement.

MicroPython Interface Board
===========================

NOTE: This is a work in progress and incomplete.

This is a reference design that you may or may not be able to use, depending on your DUT testing
requirements.  The intent here is to re-use this design to bootstrap your test jig design.

This design is open sourced on CircuitMaker tool.  This tool allows you to fork the design, make it your own.

There are two boards, one is the MicroPython Interface board, the other is a Probe Board.  Ribbon
cable makes the connection between the two boards.  The probe positions are on a separate board to allow them
to change without affecting the layout of the Interface Board, and to accommodate the test jig design.

The idea is that when you design your PCB, you place test points on the grid pattern of the probe points
without concern for the function (measurement or stimulous) type of the probe point.
**Although you must take care that all the functions you do need can be addressed by the MicroPython Interface board.**

During the test jig development cycle you use the MicroPython Interface board and manually wire connections from the probe
points to the function on the MicroPython board.  The MicroPython Interface board design also includes a prototyping area so
that you could also manually assemble extra functions.

Finally once the development is done, you fork this MicroPython Interface design and make the PCB connections.  You may also use
the MicroPython Interface design in production if that works for you.

If the test point grid for V1 doesn't meet your needs, or the pin mux capability of the MicroPython board
doesn't have all the features you need, then you will have to design your own interface board.

MicroPython Pin Mux
-------------------

Full information is here https://docs.micropython.org/en/latest/pyboard/quickref.html

.. image:: static/Screenshot_upybrd_01.png


3D View
-------

.. image:: static/micropythonboard_a0103.PNG

* The MicroPython board is in the upper right corner (a 3D model was not available)
* There are two through hole headers below the MicroPython board that connect signals to the Probe Board

.. image:: static/ProbeBoard_a0201_3d.PNG

* The two DIP headers connect signals between the two boards

Beyond the MicroPython functions, the Interface board has,

* Two Texas Instruments LP3886, linear step down adjustable DC/DC converters, 1 Amp, 0.8-4V
* Two Texas Instruments INA220 current measurement ICs (to monitor current on any one of three supplies)
* One Virtual Serial Port via USB
* Prototyping area
* Digital Resistor IC, TPL0102
* Level translator, TXS0104
* 2 SMA connectors
* One 12V buffer Amplifier, LTC6090


Probe Board Grid Pattern
------------------------

Image gridline is 25mils.

.. image:: static/ProbeBoard_a0201.PNG

None of these probe points are wired to any function on the MicroPython Interface Board V1.  There are convenient
landing sites on the PCB however to make it easy to attach a wire to every probe point.


Schematic
---------

The complete schematic is available to be forked on CircuitMaker.
The Schematic and PCB layout are in PDF form in ./public/prism/drivers/micropythonbrd


Configuring MicroPythgon Board
------------------------------

Initially the MicroPython board must be configured with an ID, so that it is unique from other MicroPython boards
in the test system.

The `~/git/scripts/public/prism/drivers/micropythonbrd/upybrd.py` script file provides various functions for setting up
a MicroPython Board.

::

    computer:~/git/scripts/public/prism/drivers/micropythonbrd$ python3 upybrd.py --help
    usage: upybrd.py [-h] [-p PORT] [-s SET_ID] [-l] [-i] [-f] [-g READ_GPIO] [-v]
                     [--version]

    upybrd

    optional arguments:
      -h, --help            show this help message and exit
      -p PORT, --port PORT  Active serial port
      -s SET_ID, --set-id SET_ID
                            Set channel <#> to <port>, ex: -s 0 -p COM3
      -l, --list            list micropython boards
      -i, --identify        blink red LED on specified port
      -f, --files           List files on pyboard
      -g READ_GPIO, --read-gpio READ_GPIO
                            read gpio (X1, X2, ...)
      -v, --verbose         Increase verbosity
      --version             Show version and exit

        Usage examples:
        1) List all MicroPython boards attached to the system,
           python3 upybrd.py --list
        2) Setting the ID to 1 for the MicroPython board on COM3,
           python3 upybrd.py --port COM3 --set-id 1

Notes

* The ID of the MicroPython board is represented as an empty file on the MicroPython filesystem with the name of format `ID<#>`

