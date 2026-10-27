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
* Pogo board template: `a5800-BONDPogo <https://github.com/sistemicorp/a5800-BONDPogo>`_,
  see `Designing the Pogo Board`_

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


Designing the Pogo Board
************************

Start your Pogo board from Sistemi's template, the Altium Designer project
`a5800-BONDPogo <https://github.com/sistemicorp/a5800-BONDPogo>`_.  It has the four BOND
headers already placed where they mate with BOND, a spring pin part, the BOND schematic and a 3D
model of BOND.  You add the spring pins for your DUT's test points, and wire each one to a header
pin.  The template's `README.md` lists its files.

The stack up, from the top,

* the DUT, with its test points facing down,
* the spring pins, on the Pogo board,
* the Pogo board, with the four headers TH1-TH4 (Molex 90151-2120) on its bottom side,
* BOND, with its headers facing the Pogo board, and its components facing away from it.

Plan the test points and their header pins first, see :doc:`PCBA Test Coverage <_coverage>`,
sections Pin Budget, Test Point Location and From the Pin Map to the Pogo Board.


Start a Pogo Board Project
==========================

Your Pogo board is usually private, and a GitHub fork of a public repo can't be private.  Clone
the template, and push it to a new, empty private repo,

::

    git clone https://github.com/sistemicorp/a5800-BONDPogo.git myproduct-Pogo
    cd myproduct-Pogo
    git remote rename origin sistemi
    git remote add origin git@github.com:<your org>/myproduct-Pogo.git
    git push -u origin master

The `sistemi` remote lets you fetch later changes to the template.  In Altium, rename the project
and the title blocks to your own part number.


Schematic
=========

* In `Top.SchDoc`, copy the spring pin `TP1` once for each DUT test point.  Name each after the
  test point and its net, for example `TP1-VDD`, `TP2-IN5`, the same as the Pin Map.
* Use several GND spring pins, `TPG1`, `TPG2`..., spread over the DUT.
* Connect each test point to a net of the header sheets `TH1`-`TH4`.  Each sheet gives the BOND
  function and range of its pins, for example `VDUT` (1-20V, 1A), `VBAT` (2-5V, 0.8A),
  the open drain outputs, UART, I2C, JTAG/SWD and USB, and the general purpose `PORT` pins
  (ADC, DAC, GPO or GPI, set in the `Header Definition File`_).
* Circuits that BOND controls, such as switched loads, dividers or relays, go on the Pogo board
  too, see :ref:`_coverage:Pogo Board Circuits`.

BOND has some flexibility: some header pins depend on how the BOND is populated, for example
header 3 pin 2 to the BNC connector, or the divider on header 1 pin 8.  Check your BOND against
the BOND schematic `public/prism/drivers/A4401_BOND/a4402-SCH_05.pdf`, and change the template
to match it.


Layout
======

* Do not move the headers TH1-TH4, or change their footprints.  They must line up with the BOND
  headers.
* Place the spring pins under the DUT test points, from the DUT's layout.  Keep the trace from
  each spring pin to its header pin short, see :ref:`_coverage:Test Point Location`.
* The template board is 2 mm thick, which keeps the spring pins straight and the board flat
  under the force of the pins.
* Parts on the top of the Pogo board must clear the DUT and the parts on its bottom side.  The
  bottom of the Pogo board sits over BOND, keep it clear apart from the headers.


Stack Up STEP Model
===================

The template layout has a 3D model of BOND (`a4402-CAD_PCB1_01.step`) mated to the Pogo board,
and the template's `a5800-CAD_3DwBOND_01.step` is the two boards together.  Add the 3D model of
your DUT on its spring pins, and export a STEP of the whole stack up, BOND, Pogo board and DUT.
The jig's mechanical design (the base, the DUT nest, the lid and its hold downs) starts from that
model.


Mechanical
==========

These are typical values, check them against the spring pin's datasheet and your jig.

* Spring pins: the template uses `S13-503-SISTEMI`.  When the jig is closed, compress each pin
  to about two thirds of its travel, so every pin has force even when the DUT is not flat.
* DUT test pads: about 1 mm across, at least 2.54 mm (100 mil) apart centre to centre where you
  can, 1.27 mm at the least.  Keep pads a few mm from tall parts, and on one side of the DUT.
* Alignment: two non-plated tooling holes on the DUT, at opposite corners, with guide pins in the
  nest or on the Pogo board.  Pin to pad accuracy comes from the tooling holes, not the board
  edge.
* Hold down: push the DUT down with hold down fingers in the lid, placed over the spring pins,
  so the DUT does not bend.  Many spring pins add up to a large force.
* Through hole connector pins and the programming header can be probed too, see
  :doc:`PCBA Test Coverage <_coverage>`.

Before ordering the Pogo board, check its schematic against the Pin Map and the header
definition file, pin by pin.


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
