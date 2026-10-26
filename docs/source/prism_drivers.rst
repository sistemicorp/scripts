Drivers
=======

These are typically pieces of test equipment that are used to measure, stimulate or otherwise "test"
the device under test (DUT).  Examples of test equipment could be power supplies, oscilloscopes,
JTAG programmers, etc..

`Drivers` required for a particular DUT are listed in the `config` section of scripts.  For example::

      "config": {
        // fail_fast: if true (default), testing will stop on first failed test
        "fail_fast": false,
        // list of driver code to initialize the test environment, must be specified
        // Drivers may or may not have args
        "drivers": ["public.prism.drivers.fake.hwdrv_fake",
                    ["public.prism.drivers.fake.hwdrv_fakeArgs", {"k0": 0, "k1": 1}] ]
      },



Prism will load/init each `driver` that is listed, when the script is validated.  A driver listed with
arguments (a list of the driver path and a dict, like `hwdrv_fakeArgs` above) has the dict passed to
`discover_channels(args)`.

The python file specified *MUST* have a class called `HWDriver`.  See the `fake` example for
implementation details and documentation.

By convention, the driver filename has the prefix `hwdrv_<name>.py`.

The Drivers files are stored by convention in a separate path relative to scripts in order to isolate
them.  `Drivers` are typically common to test multiple products.


Discover Channels
-----------------

The important method of the `HWDriver` class is `discover_channels`.

`discover_channels` method returns a list of dictionaries that represent the connected hardware used in
the test system.  Every driver that reports a number of channels must report the same number, otherwise
the script fails validation.  A driver that reports 0 channels is a shared resource for all channels,
see `Shared Drivers`_.  The list may contain one item that is shared among all the attached test jigs,
or it might be one item per test jig.

If there are multiple hardware items, the list of those items must be in the same order across the
different hardware types.  For example, if each test jig has a Teensy4 and a Segger programmer, the list
of Teensy4s and Seggers must be in the same order.  In this example, both Segger and the Teensy4s are
connected via USB, and if a prescribed USB (cabling) setup is used (one hub per test jig) then the USB
path can be used to synchronize the two lists.  This is done in the examples provided.

Per the code documentation, `discover_channels` must return a dictionary with prescribed keys.


::

    def discover_channels(self):
        """ determine the number of channels, and popultae hw drivers into shared state

        [ {"id": i,                    # ~slot number of the channel (see Note 1)
           "version": <VERSION>,       # version of the driver
           "hwdrv": <object>,          # instance of your hardware driver

           # optional
           "close": None,              # register a callback on closing the channel, or None
           "play": jig_closed_detect   # function for detecting jig closed
           "play_poll_sec": 1          # seconds between play calls, 0.2 to 2, default 1
           "show_pass_fail": jig_led   # function for indicating pass/fail (like LED)
           "show_msg": jig_display     # function for indicating test status (like display)

           # not part of the required block
           "unique_id": <unique_id>,   # unique id of the hardware (for tracking purposes)
           ...
          }, ...
        ]

        Note:
        1) The hw driver objects are expected to have an 'slot' field, the lowest
           id is assigned to channel 0, the next highest to channel 1, etc
           A shared driver (returns 0 channels) is not assigned a channel, all channels use it.

        :return: <#>, <driver_type>, <list> (use Zero for a device shared across all channels)
            where
                #:      >0 number of channels,
                        0 does not indicate num channels, like a shared hardware driver
                        <0 error
                driver_type: String constant identifying Installed drivers type
                list:   List of installed driver dicts
        """


Prism calls the `play` function every second to see if the jig has closed, and starts the test when it
does.  A driver can set `play_poll_sec` to change this, from 0.2 to 2 seconds, for example so a test
restarts sooner after the jig closes.  A value outside the range is logged and set to the nearest
limit, and a value that is not a number is logged and the default of 1 second is used.


Shared Drivers
--------------

A driver that returns 0 channels is shared by all channels, for example one label printer for
all the test jigs.  Its driver items are not assigned to a channel, and
`self.shared_state.get_drivers(self.chan, type=...)` returns them for every channel, along with
that channel's own drivers.

* At least one driver of the script must set the number of channels, a script with only shared
  drivers fails validation.
* A shared driver must return at least one item in its list, otherwise validation fails.
* The `play`, `show_pass_fail`, `show_msg` and `jig_reset` functions of a shared driver, if set,
  are called by every channel.  A shared driver usually sets them to `None`.

A driver can support both, with a script argument.  For example, the `brother_ql` driver with
`{"only_one": true}` expects one printer shared by all channels, and finding more than one is an
error.  Without it, there is one printer per channel, in USB hub port order::

    "drivers": ["public.prism.drivers.fake.hwdrv_fake",
                ["public.prism.drivers.brother_ql.hwdrv_brother_ql", {"only_one": true}]]


Slot Number
-----------

When implementing python code to implement tests, there is a `channel (self.chan)` number and a `slot` number.
The channel is how Prism indexes the running threads, usually from 0 to a max of 7.  The slot number
is a number used to setup configuration of the physical system.



VISA
----

VISA is a test equipment control protocol.  See `VISA <https://en.wikipedia.org/wiki/Virtual_instrument_software_architecture>`_
for more information.

Prism includes these two PyPi VISA modules,

* `pyvisa <https://pypi.org/project/PyVISA>`_
* `PyVISA-py <https://pypi.org/project/PyVISA-py>`_


An example of VISA driver based hardware is provided in the `agilent_dso_usb_1` driver example.
It finds the scope on USB by default, or on Ethernet (VXI-11) with driver arguments,

.. code-block:: JSON

    "drivers": [
      ["public.prism.drivers.agilent_dso_usb_1.hwdrv_agilent_dso_usb_1",
       {"interface": "ethernet", "ip": "192.168.1.100"}]
    ]

On USB, Prism in its Docker container needs no udev rule, see :doc:`Deployment <_deployment>`.
To run the driver or `prism_dev.py` on the host, your user account needs access to the scope,
either for all USB devices with `sudo ./udev-install-usbusers.sh` from the scripts repo, or just
for the scope with this rule (DSO7000 series, USB id `0957:175d`),

.. code-block:: bash

    echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="0957", ATTR{idProduct}=="175d", MODE="0666"' | \
        sudo tee /etc/udev/rules.d/99-agilent-dso.rules
    sudo udevadm control --reload-rules && sudo udevadm trigger

Then unplug and plug in the scope's USB cable.  Without access, pyvisa logs
`Found a USB INSTR device whose serial number cannot be read` and the driver finds no scope.

.. note::
    Error: Found a device whose serial number cannot be read

    This error can happen if your user account doesn't have correct privileges.

    See: `stackoverflow <https://stackoverflow.com/questions/52256123/unable-to-get-full-visa-address-that-includes-the-serial-number>`_


Included Drivers
----------------

These drivers are included in `public/prism/drivers`.  Several have a `README.md` with setup details.

* `fake` - simulated hardware, used by the example scripts, see `hwdrv_fake.py` for the driver API
* `teensy4` - Teensy 4 based jig controller
* `A4401_BOND` - Sistemi BOND (Bed of Nails Design) tester
* `agilent_dso_usb_1` - Agilent oscilloscope over USB or Ethernet (VISA)
* `brother_ql` - Brother QL label printer
* `ble_listener` - Bluetooth LE listener, uses the host BlueZ through the D-Bus mount in `prism.sh`.
  Loading a script fails if the Bluetooth adapter is off or missing.  Test the host with
  `python3 blelistener_cli.py scan -t 30` from the driver folder
* `prism_play` - trigger the Prism `play` (start test) feature from the command line, for CI
* `nrfprog` - Nordic nRF programmer (nrfjprog)
* `stlinkv3mods` - ST-LINK/V3 programmer (STM32CubeProgrammer)
* `segger` - placeholder, not complete
* `common` - shared helpers

.. note::

    The vendor programming tools used by `nrfprog` (Nordic nrfjprog) and `stlinkv3mods` (ST STM32CubeProgrammer)
    are not included in the scripts.  Each Prism station installs them in the `tools` folder of
    its `public` folder (the folder `prism.sh` is run from), for example `~/prism/public/tools/`
    on a station set up as in :ref:`Deployment <deployment-new-prism>`.
    This folder is ignored by git, is not synced from Lente, and Prism sees it through its
    existing `public` mount.  Each driver's `README.md` has the install steps, and the driver
    checks its tool runs when Prism loads a script.

    * `stlinkv3mods` - see `public/prism/drivers/stlinkv3mods/README.md`
    * `nrfprog` - see `public/prism/drivers/nrfprog/README.md`

    Segger J-Link is installed in the Prism Docker image (`/opt/SEGGER/JLink`) and needs no host install.
