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
that channel's own drivers.  `get_drivers(None, type=...)` returns only the shared drivers.

* At least one driver of the script must set the number of channels, a script with only shared
  drivers fails validation.
* A shared driver must return at least one item in its list, otherwise validation fails.
* The `play`, `show_pass_fail`, `show_msg` and `jig_reset` functions of a shared driver, if set,
  are called by every channel.  A shared driver usually sets them to `None`.
* The channels run at the same time, so lock shared equipment while a channel uses it, see
  `Locking Shared Equipment`_.

A driver can support both, with a script argument.  For example, the `brother_ql` and
`agilent_dso_usb_1` drivers with `{"only_one": true}` expect one instrument shared by all
channels, and finding more than one is an error.  Without it, there is one instrument per
channel, in USB hub port order::

    "drivers": ["public.prism.drivers.fake.hwdrv_fake",
                ["public.prism.drivers.brother_ql.hwdrv_brother_ql", {"only_one": true}]]

Equipment is shared by the jigs (channels) of one Prism computer.  Sharing one instrument
between Prism computers is not supported: Prism does not lock it between computers, and a
driver that resets its instrument when a script loads would reset it in the middle of
the other computer's test.


Locking Shared Equipment
~~~~~~~~~~~~~~~~~~~~~~~~

Each channel runs its test items in its own thread.  Without a lock, two channels can send
commands to a shared instrument at the same time, and each reads the other's settings or
results.

Hold `self.shared_lock(<name>)` for the whole sequence of commands that must not be
interleaved, for example set up, trigger and measure.  Every channel that uses the
instrument must use the same name, such as the driver type.  Use `with` so the lock is
released when the item fails, times out or is aborted::

    with self.shared_lock("AGILENT_DSO_USB_1"):
        self.dso.write(':AUT CHAN{}'.format(self.dso_ch))
        vpp = self.dso.query(':MEASure:VPP? CHANnel{}'.format(self.dso_ch))

Keep the time the lock is held short, the other channels wait for it.  A test that holds
a shared instrument for a long time makes the jigs take turns.


Slot Number
-----------

When implementing python code to implement tests, there is a `channel (self.chan)` number and a `slot` number.
The channel is how Prism indexes the running threads, usually from 0 to a max of 7.  The slot number
is a number used to setup configuration of the physical system.


Adding Test Equipment
---------------------

Test equipment, like an oscilloscope, a power supply or a programmer, is added to a test jig
with a driver.  Start from the included driver closest to your equipment, see
`Included Drivers`_, and copy its folder into `public/prism/drivers` with a new name.

#. **One per jig, or shared.**  Decide if each jig has its own instrument, or one instrument
   serves all the jigs of the Prism computer.  One per jig is simpler and lets the jigs test
   at the same time.  A shared instrument saves cost, but the jigs take turns using it.
#. **Find the instruments.**  `discover_channels` finds the instruments on USB, Ethernet or
   serial.  On USB, a driver can find every instrument by its USB vendor and product id.
   On Ethernet, the instruments are listed in the driver arguments by IP address.
#. **Put them in jig order.**  With one instrument per jig, channel 0 must get the
   instrument wired to jig 0, and so on.  Order USB instruments by the USB hub port they are
   plugged into, and use one hub per jig, or the same port on each hub.  Order Ethernet
   instruments by the list of IP addresses.  Instruments that report the same number of
   channels as the jig controller must be in the same order, see `Discover Channels`_.
#. **Fail if one is missing.**  If an instrument is not found, return an error rather than
   fewer channels.  Skipping a missing instrument moves the next one to the wrong jig.
#. **Wire a shared instrument.**  A shared instrument with several inputs usually has one
   input per jig, for example scope input `self.chan + 1` for the jig of `self.chan`.  The
   number of inputs limits the number of jigs.
#. **Lock a shared instrument**, see `Locking Shared Equipment`_.
#. **Record it.**  Return the instrument's serial number as the `unique_id`, and record it
   in a setup item as a string measurement, for a shared instrument also the input used.
   A problem found later can then be traced to one instrument or input, see
   :ref:`Test Equipment <_traceability:Test Equipment>`.
#. **Test it.**  Each driver file has a `__main__` section to run `discover_channels` from a
   terminal, without Prism.  Then run the script with `prism_dev.py --script <path>`, and
   with Prism.  Remember that the `discover_channels` of some drivers reset their
   instrument, as the script loads.
#. **Document it.**  Describe the driver arguments in the `discover_channels` doc string, and
   add a `README.md` to the driver folder with the equipment, how it connects, per jig or
   shared, and any setup such as udev rules or vendor tools.

The `agilent_dso_usb_1` driver and the `dso_v0` example do all of the above, for one scope
per jig or one shared scope, see `agilent_dso_usb_1`_.


VISA
----

VISA is a test equipment control protocol.  See `VISA <https://en.wikipedia.org/wiki/Virtual_instrument_software_architecture>`_
for more information.

Prism includes these two PyPi VISA modules,

* `pyvisa <https://pypi.org/project/PyVISA>`_
* `PyVISA-py <https://pypi.org/project/PyVISA-py>`_


An example of VISA driver based hardware is provided in the `agilent_dso_usb_1` driver example.
It finds the scope on USB by default, or on Ethernet (VXI-11) with driver arguments,
see `agilent_dso_usb_1`_.

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

These drivers are included in `public/prism/drivers`.  Each driver's `hwdrv_*.py` file
documents its arguments, and several have a `README.md` with setup details.  The driver type
is the `type` to use with `self.shared_state.get_drivers(self.chan, type=...)`.

.. list-table::
   :header-rows: 1
   :widths: 20 25 25 30

   * - Driver
     - Equipment
     - Channels
     - Example script
   * - `fake`
     - none, simulated
     - one per channel (`NUM_CHANNELS`)
     - `prod_v0`
   * - `agilent_dso_usb_1`
     - Agilent oscilloscope
     - per jig, or shared
     - `dso_v0`
   * - `brother_ql`
     - Brother QL label printer
     - per jig, or shared
     - `brother_v0`
   * - `ble_listener`
     - station Bluetooth adapter
     - shared
     - `prod_v0/prod_ble.scr`
   * - `scanners`
     - USB barcode scanner
     - one channel
     - `barcode_count_v0`
   * - `teensy4`
     - Teensy 4 jig controller
     - per jig
     - `teensy4_v0`
   * - `A4401_BOND`
     - Sistemi BOND tester
     - per jig
     - `BOND_v0`
   * - `nrfprog`
     - Nordic nRF programmer
     - per jig
     - `nRF52833-DK`
   * - `stlinkv3mods`
     - ST-LINK/V3 programmer
     - per jig
     - `stlinkv3mods`
   * - `prism_play`
     - none, command line start
     - one per channel (argument)
     - `prod_v0/githubci_0.scr`

The example scripts are in `public/prism/scripts/example`.  `segger` is a placeholder, not
complete, and `common` holds shared helpers, it is not a driver.

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


fake
~~~~

Simulated hardware, so the example scripts run without a jig.  `hwdrv_fake` makes
`NUM_CHANNELS` channels (1 to 8, set in the file), and its `show_pass_fail` and `show_msg`
functions only log.  `hwdrv_fakeArgs` shows how a driver takes arguments, the second item of
the driver in the script, which can be any JSON value.

* Driver types: `FAKE`, `FakeWithArgs`
* Start here to learn the driver API, `hwdrv_fake.py` documents every field of
  `discover_channels`.
* Because a shared driver cannot set the number of channels, several examples use `fake` to
  set it next to a shared driver.


agilent_dso_usb_1
~~~~~~~~~~~~~~~~~

Agilent InfiniiVision oscilloscope, tested with a DSO7104B, using VISA on USB or Ethernet.
`discover_channels` resets each scope it finds (`*RST`), so loading the script resets the
scope.  Only the models in the driver's `WHITE_LIST` are used.

* Driver type: `AGILENT_DSO_USB_1`, the scope's serial number is the `unique_id`
* `{"only_one": true}` - one scope shared by all channels, finding more than one is an
  error.  Without it, there is one scope per channel.
* `{"interface": "ethernet", "ip": ...}` - scopes on Ethernet (VXI-11), USB is the default.
  `ip` is one IP address, or a list with one IP per channel, in channel order.  Every scope in
  the list must be found.
* On USB, the scopes are ordered by the USB hub port they are plugged into.

.. code-block:: JSON

    "drivers": [
      "public.prism.drivers.fake.hwdrv_fake",
      ["public.prism.drivers.agilent_dso_usb_1.hwdrv_agilent_dso_usb_1", {"only_one": true}]
    ]

    "drivers": [
      ["public.prism.drivers.agilent_dso_usb_1.hwdrv_agilent_dso_usb_1",
       {"interface": "ethernet", "ip": ["192.168.1.100", "192.168.1.101"]}]
    ]

The first is one shared scope on USB, the second one scope per jig on Ethernet, with two
jigs.  The `dso_v0` example test code works with both.  A shared scope uses input
`self.chan + 1` for each jig, so up to 4 jigs on a 4 input scope, and is locked while a
channel uses it.  A scope per jig uses input 1.  See `VISA`_ for USB access on the host.


brother_ql
~~~~~~~~~~

Brother QL label printer (QL-700) on USB, to print a label such as a serial number barcode.

* Driver type: `Brother_QL`
* `{"only_one": true}` - one printer shared by all channels.  Without it, there is one printer
  per channel, in USB hub port order.
* `{"test_label": true}` - print a test label when the script loads, the script fails
  validation if it cannot print.


ble_listener
~~~~~~~~~~~~

Listens for Bluetooth LE advertisements, for example to check a DUT advertises, using the
station's Bluetooth adapter.  It is always shared, so another driver sets the number of
channels.

* Driver type: `BLE_LISTENER`
* Prism uses the host BlueZ through the D-Bus mount in `prism.sh`.
* Loading a script fails if the Bluetooth adapter is off or missing.  Test the host with
  `python3 blelistener_cli.py scan -t 30` from the driver folder.


scanners
~~~~~~~~

USB barcode scanner in keyboard mode (Datalogic).  It makes one channel, and its `play`
function restarts the script for each scan, see
:doc:`Barcode Count Example <prism_barcode_count>`.

* Driver type: `SCANNER`
* A scanner in keyboard mode types into the window that has focus, so scans cannot be told
  apart by scanner.  More scanners still make one channel.


teensy4
~~~~~~~

Teensy 4 based jig controller, the reference :doc:`Interface Controller <_jigs>`.  The Teensy4
runs the Prism simpleRPC server firmware, from `teensy4/server`, which gives Python access to
its pins.

* Driver types: `TEENSY4`, and `TEENSY4_PROG` for `hwdrv_teensy4_prog`
* `hwdrv_teensy4` makes one channel per Teensy4, in USB path order.  The jig closed GPIO, if
  set, is its `play` function, and it has `show_pass_fail` and `jig_reset` functions.
* `hwdrv_teensy4_prog` programs the firmware into a new Teensy4, with one Teensy4 connected,
  `teensy4_ProgFresh_0.scr`.  `teensy4_Update_0.scr` updates the firmware.
* The firmware version is checked, a Teensy4 running another version is not used.
* Building the firmware, see `public/prism/drivers/teensy4/server/README.md`


A4401_BOND
~~~~~~~~~~

Sistemi BOND (Bed of Nails Design), a Teensy 4.1 based tester with configurable analog and
digital pins, a DUT supply and a battery emulator, see :doc:`BOND <prism_bond>`.

* Driver types: `A4401_BOND`, and `A4401_BOND_PROG` for `hwdrv_A4401_BOND_prog`
* `hwdrv_A4401_BOND` takes the path of the Pogo board header definition file, and makes one
  channel per BOND, in USB path order.
* `hwdrv_A4401_BOND_prog` programs the firmware into a new BOND, `bond_progfresh_0.scr`.
* Setup and pin rules, see `public/prism/drivers/A4401_BOND/README.md`


nrfprog
~~~~~~~

Programs Nordic nRF devices with `nrfjprog`, through a SEGGER J-Link probe, such as the one on
a Nordic nRF DK.

* Driver type: `NRFJPROG`, the probe serial number is the `unique_id`
* One channel per probe, in USB path order.  The serial number selects the probe for
  `nrfjprog`.
* The nRF Command Line Tools are installed on each station, see the note above and
  `public/prism/drivers/nrfprog/README.md`.


stlinkv3mods
~~~~~~~~~~~~

Programs STM32 devices with STM32CubeProgrammer, through an ST-LINK/V3 probe, such as the
STLINK-V3MODS.

* Driver type: `STLINKV3MODS`, the probe serial number is the `unique_id`
* One channel per probe, in USB path order.  A probe that fails the version check is skipped.
* STM32CubeProgrammer is installed on each station, see the note above and
  `public/prism/drivers/stlinkv3mods/README.md`.


prism_play
~~~~~~~~~~

Starts a test from the command line instead of a jig, for example from a GitHub Actions runner
to test firmware in CI.  There is no hardware, a named pipe per channel takes the play command.

* Driver type: `PrismPlay`
* `{"work_dir": <path>, "channels": <#>}` - `work_dir` is required, the folder under `public`
  for the pipes.  `channels` defaults to 1.
* Run `prism_play_cli.py` to start a channel, see `public/prism/drivers/prism_play/README.md`
  and `README_github_prism_ci.md`.
