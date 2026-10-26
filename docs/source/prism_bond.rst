BOND
####

BOND (Bed of Nails Design) is Sistemi's open source PCBA tester.  It is a Teensy 4.1 based jig
controller with four headers of configurable analog and digital pins, a DUT power supply, a
battery emulator, and pass/fail LEDs.  You design a Pogo board, with the spring probes for
your DUT, that plugs into the BOND headers.

* Product brief: `public/prism/drivers/A4401_BOND/a4402-SPC_ProductBrief_01.pdf`
* Schematic: `public/prism/drivers/A4401_BOND/a4402-SCH_05.pdf`
* Driver developer guide: `public/prism/drivers/A4401_BOND/README.md`
* Example scripts and test code: `public/prism/scripts/example/BOND_v0`

.. contents::
   :local:


Getting Started
***************

#. Program the BOND firmware into a new BOND, with the example script `bond_progfresh_0.scr`,
   or with the Arduino IDE, see `public/prism/drivers/A4401_BOND/server/README.md`.
   Only one BOND may be plugged in while programming.
#. With no Pogo board or DUT connected, run the self test script `bond_selftest_0.scr`.
   It checks the BOND supplies, the header ADCs against the 2.5V reference, the battery
   emulator and the DUT supply.
#. Copy the example folder to your product, for example
   `public/prism/scripts/myproduct/BLT`, and change the scripts and test code, see the example's
   `README.md`.  The `P1000`-`P1999` test items are examples, add your own tests after them.

`bond_update_0.scr` updates the firmware of a BOND that is already programmed.  Run it only
once per Prism start, as the BOND's USB port can change after the update.  The Arduino IDE must be
closed while Prism uses BOND.


Header Definition File
**********************

Each Pogo board has a header definition file, which sets how each header pin is used: `ADC`,
`DAC`, `GPO`, `GPI` or not used.  The file is given with the driver in the script `config`,

::

  "config": {
    "fail_fast": true,
    "drivers": [["public.prism.drivers.A4401_BOND.hwdrv_A4401_BOND",
                 "public/prism/scripts/myproduct/BLT/assets/pogo_hdr_definition._json"]]
  },

* Start from the example `assets/pogo_hdr_definition._json`, and use the BOND schematic
  `Header #` pages to map your Pogo board's signals to header pins.
* Each pin is `{"mode": <mode>, "port": <port>}`.  A pin wired to two ports lists both, for
  example `{"mode": "ADC,GPO", "port": "6,9"}`.
* ADC and DAC ranges are 0-10000 mV.  Each header has one GPO high level (`gpo_mv`) and one GPI
  threshold (`gpi_mv`).
* HDR1 pin 1 is an adjustable LDO output (600-3900 mV), set with `bond_ldo_set`.
* The file is checked when the driver loads, an invalid file fails the script `Validate`.
* Different DUTs use different Pogo boards, each with its own file.

The full rules are in the driver `README.md`, section `BOND Header Pin Configuration`.

To plan which DUT test points go to which header pins, and the Pogo board circuits, see
:ref:`_coverage:Pin Budget` in :doc:`PCBA Test Coverage <_coverage>`.


Test Code
*********

The setup item gets the BOND for its channel from the drivers, and records BOND's id for
traceability, see :doc:`Traceability <_traceability>`,

::

    drivers = self.shared_state.get_drivers(self.chan, type=DRIVER_TYPE)
    driver = drivers[0]
    _, _, _bullet = ctx.record.measurement("teensy4_id", driver["obj"]["unique_id"],
                                           ResultAPI.UNIT_STRING)
    self.teensy = driver["obj"]["hwdrv"]

Each BOND method returns a dict, `{'success': True, 'method': ..., 'result': {...}}`.  Check
`success` before using `result`,

::

    response = self.teensy.bond_max_hdr_adc(hdr=1, pin=9)
    if not response['success']:
        self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
        return
    success, _result, _bullet = ctx.record.measurement("v3v3", response['result']['mV'],
                                                       ResultAPI.UNIT_MILLIVOLTS,
                                                       ctx.item.args.min, ctx.item.args.max)

The main methods, see `A4401_BOND.py` for all of them and their arguments,

* header pins: `bond_max_hdr_adc`, `bond_max_hdr_dac`, `bond_max_hdr_gpo`, `bond_max_hdr_gpi`
* DUT supply: `vdut_set`, `vdut_en`, `vdut_con`, `vdut_read`, `vdut_get_fault`
* battery emulator: `vbat_set`, `vbat_read`, `iox_vbat_en`, `iox_vbat_con`
* other: `bond_ldo_set`, `vbus_en`, `led`, `version`, `unique_id`, `temperature`, `reset`

BOND is reset at the start and end of every test, which sets the DACs to 0V and the GPOs to
their idle level.  The BOND driver also gives Prism the jig closed detect (`play`) and the
pass/fail LEDs (`show_pass_fail`), see :doc:`Drivers <prism_drivers>`.


Command Line
************

`A4401_BOND_cli.py` runs BOND methods without Prism, for bringing up a Pogo board and debugging,

::

    cd ~/git/scripts/public/prism/drivers/A4401_BOND
    python A4401_BOND_cli.py -p /dev/ttyACM0 status
    python A4401_BOND_cli.py -p /dev/ttyACM0 -n bond_max_hdr_adc_cal --header 3
    python A4401_BOND_cli.py --help

Stop Prism, or close the script in Prism, before using the CLI, only one program can use the
BOND serial port at a time.
