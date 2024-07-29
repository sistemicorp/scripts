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
* Is custom developed depending on the DUT test measurement and stimulus requirements


Interface Controller
--------------------

* A device with USB connectivity and a processor in which Prism can control and
  otherwise interface to
* Examples that could be used, Teensy4 Arduino, and RaspBerry Pi.
* An ``Interface Controller`` may be designed into the ``Interface Board`` or
  it can be a daughter card that plugs into an ``Interface Board``
* Sistemi has developed a reference design based on Teensy4 Module


Bed of Nails
------------

* An arrangement of spring mounted probes that make electrical connection to test points
  on the DUT
* Bed of Nails (probes) can wear out over time, you may want to consider a design that
  allows the Bed Of Nails to be replaced independently of the Interface Board electronics.


Nest
----

* A landing site for the DUT
* designed to make alignment between the Bed of Nails and the DUT test points
* Usually has two "dowels" that will align with holes on the DUT for precise positioning



Teensy4 Interface Controller
============================

Teensy4 is a reference design that you may or may not be able to use, depending on your DUT testing
requirements.  The intent here is to re-use this design to bootstrap your test jig design.

Prism ``scripts`` repo includes Teensy4 code to support your Interface board requirements.  Note that
the support code is compatible with Teensy 4.0 and 4.1 modules.

Teensy4 information is here https://www.pjrc.com/store/teensy41.html

