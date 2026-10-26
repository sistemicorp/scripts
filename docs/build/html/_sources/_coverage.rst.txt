PCBA Test Coverage
##################

A test coverage analysis shows which assembly faults on a PCBA your production test can find,
and which it can't.  Do it for each board, ideally while the board is still being designed, so
that test points can be added where they find the most faults.

The Prism Assistant `analyze_coverage` prompt walks you through this analysis, see
:doc:`Prism Assistant <_assistant>`.

.. contents::
   :local:


Fault Model
***********

Look at each component on the board and ask, for each fault below, "would a test fail if this
part had this fault?"

* **Short** - an unintended connection.  Usually the connection is to GND or a supply rail, but
  it can be to another net, for example a solder bridge to the next pin.
* **Open** - the part is not connected.  Usually the part was not fitted by mistake, but it can
  also be a lifted pin or a dry joint.
* **Value** - the wrong part is fitted, for example 10k instead of 100k.  Value applies only to
  passive parts: resistors, capacitors, inductors, ferrites, crystals and LEDs.

ICs, and other parts with several pins (transistors, connectors, modules), are analysed pin by
pin.  Each pin is treated like a passive part and checked for Short and Open only.  A test that
reads an IC's device ID also proves that the right IC is fitted, so note it in the Notes column.

A test detects a fault only if the fault moves the measurement outside the test limits.  A missing
decoupling capacitor does not change a rail voltage, so the rail voltage test does not cover that
capacitor's Open fault, even though the test "uses" the rail.


Test Points
***********

BOND reaches the DUT through the Pogo board.  The Pogo board's spring pins land on test points on
the PCB, and are wired to the BOND headers, where each pin is a MAX11311 port, set as an ADC,
DAC, GPO or GPI, see :doc:`BOND <prism_bond>`.  A net with no test point can only be tested
through other parts, or by the DUT itself.

Plan the test points while the board is designed.  The coverage analysis tells you where they
are needed, and adding them before the first PCB order costs almost nothing.

Most PCBAs are programmed through JTAG or SWD at test.  The JTAG/SWD signals, reset, the target
supply and GND must be reachable by the jig, as test points or a programming connector footprint
(for example a Tag-Connect pad).  A board whose MCU can't be programmed in the jig usually needs a
respin.

The pins of a through hole connector can be used as test points, the spring pins land on the
solder side of the pins.  Check that the pins are not covered by a part or a label, and that the
connector is fitted when the board is tested.

Add a test point to,

* the programming and debug pins (JTAG/SWD, reset, boot mode pins), and a debug UART
* every supply rail, and GND (several, spread over the board)
* each enable, reset and power-good signal of a regulator or load switch
* each analog signal that is measured, and the input of each analog chain, so a test can drive it
* each signal that goes to a connector, if the connector is not fitted at test, or is hard to reach
* nets where a part would otherwise not be covered, for example a pull resistor on a net the
  MCU can't release

Programming test points are often added in a later board revision, after the first boards could
only be programmed through a debug connector.  A debug connector footprint (for example a
Tag-Connect pad, on the bottom side) suits development, test points suit the jig, and a board can
have both.  A test point on the boot mode pin gives a second way to program, for example
through USB, if the JTAG/SWD programming fails.

Circuits designed into the DUT can help the test too, for example on-board calibration loads that
the DUT switches on, or a spare MCU pin on a net that is otherwise hard to reach.

A board with few or no test points can still be tested, through,

* the connectors, the programming header and debug UART
* the DUT's own interface, for example USB, for the test to talk to the DUT
* test firmware on the DUT's MCU, using the MCU as an instrument: GPIO, its ADC, bus transactions
  to the other ICs, clock measurement, low power modes
* the supply current, measured by BOND's DUT supply or battery emulator

The coverage will be lower.  The analysis lists the parts that can't be covered, and the test
points that would cover them, so you can decide whether they justify a board respin.


BOND Resources
**************

These are what a test can use, list them before you start the analysis.

* About 30 general purpose header pins, each a MAX11311 port set as an ADC input, a DAC output, a
  GPO or a GPI (0-10V), see `Pin Budget`_.  Check the MAX11311 datasheet for the ADC input
  impedance and DAC output current, they matter for high impedance nets and loads.
* DUT supply (VDUT), 1-12V, with current measurement.
* Battery emulator (VBAT), 1.5-5V, sources and sinks current, with current measurement.
* An adjustable LDO, 600-3900 mV, on header 1 pin 1.
* SWD/JTAG programmer (header 3), UART (header 1) and I2C (header 2) to the DUT, USB to the DUT.
* Two open drain outputs on header 1 (pins 2 and 4).
* Any other test equipment in the jig, see :ref:`prism_drivers:Adding Test Equipment`.

Power the DUT from VDUT or the battery emulator when you can.  Their current measurement finds
shorts on every rail, see `Techniques`_.  A DUT powered another way, for example from USB, loses
that test, and its short coverage drops.


Pin Budget
==========

Each BOND header has a MAX11311.  The general purpose pins in the example header definition file
`public/prism/drivers/A4401_BOND/pogo_hdr_definition._json` are,

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Header
     - Pins
     - Also on the header
   * - 1 (J5)
     - 7
     - UART, LDO output, two open drain outputs, VDUT, VBAT, GND
   * - 2 (J9)
     - 10
     - I2C, VDUT, VBAT, GND
   * - 3 (J11)
     - 9
     - JTAG/SWD, USB, VBUS, GND
   * - 4 (J16)
     - 5
     - mezzanine pass through, GND

Count the pins the test needs before you add test points, so the design does not ask for more
than BOND has.

* Each test point that a test drives or measures uses one header pin.  A test point wired to two
  ports, for example `ADC,GPO`, still uses one pin, but both ports.
* GND, VDUT and VBAT test points go to the header's fixed GND, VDUT and VBAT pins, and the
  JTAG/SWD, UART and I2C test points to their fixed pins.  They don't use general purpose pins.
* Each Pogo board circuit that BOND controls uses pins too, for example a GPO per switched
  resistor, see `Pogo Board Circuits`_.
* A test point only needed by one test can share a pin with another through an analog switch or
  relay on the Pogo board, at the cost of one more GPO.

When the count is over the budget, drop the test points that detect the fewest faults (the
coverage worksheet shows this), test a block through the DUT's MCU instead, or share pins.


Test Point Location
===================

The Pogo board wires each spring pin to a header pin.  Keep those wires short: assign each test
point to the nearest header that has a pin of the right kind.  Long traces pick up noise, add
capacitance (which slows the pull resistor decay and RC tests), and make the Pogo board harder to
route.

* Note the location of each test point on the PCB, from the layout (x, y) or as a board area.
* Look at where the headers are under the DUT, see the Stack Up in the BOND product brief
  `public/prism/drivers/A4401_BOND/a4402-SPC_ProductBrief_01.pdf`.  The DUT can be placed
  and rotated in the nest so that its programming pins are near header 3 (JTAG/SWD) and its
  debug UART near header 1.
* Put DAC and ADC pins for sensitive analog nets close to their header, and away from switching
  nodes on the DUT.
* When a header runs out of pins, move the test points that can tolerate a longer trace (GPIO,
  slow signals) to another header.

While the board is being designed, ask for test points in the areas near the headers where you
can.


Pogo Board Circuits
===================

If a test needs an electrical function that BOND doesn't have, add it to the Pogo board, and let
BOND control it through the header pins.  For example,

* switched precision resistors, for resistance and pull resistor tests, for example a 0.1% 10k
  from a test point to GND, switched by a GPO and a FET
* loads, for load switches, regulators and the DUT's outputs
* a reference clock, for crystal frequency tests
* relays or analog switches, to connect an instrument to a test point only when needed, or to
  share one header pin between test points
* dividers, for nets above the 0-10V ADC range, for example a 15V input through a 3:1 divider.
  Use resistors low enough that the ADC input impedance does not change the ratio, and keep the
  ratio with the pin in the Pin Map.
* a level shift for a negative rail, a resistor from the test point to a positive supply and
  another to the negative rail, so the ADC reads a positive voltage.  The reading depends on the
  positive supply too, so measure it as well, or set the limits for its tolerance.
* level shifting, for nets that need another logic level than the header's GPO and GPI levels
* a connector for an instrument, for example a BNC for a scope on an analog output, as well as
  a divider to an ADC pin for the automatic test
* a solenoid plunger, to press the DUT's buttons

Each circuit uses header pins (usually GPOs, the header 1 open drain outputs suit relays), so
count them in the `Pin Budget`_.  Note each one in the analysis, they become the Pogo board
requirements.


From the Pin Map to the Pogo Board
==================================

The Pin Map becomes the Pogo board schematic, the header definition file, and the test code.

* Name each Pogo board spring pin after the DUT test point it lands on, and its net, for example
  `TP2-VMAIN`, and the GND pins `TPG1`, `TPG2`...  Then the DUT, the Pogo board and the Pin Map
  can be checked against each other one to one.
* Put a spring pin on every DUT test point, and wire it to a header pin, even if no test uses it
  yet.  A test added later then only needs the header definition file and the test code, not a
  new Pogo board.  The header definition file sets only the pins the tests use.
* Use several GND spring pins, spread over the board, near the test points of sensitive
  measurements.
* The programmer's target voltage reference (`JTAG_VCC` on header 3) comes from the DUT's MCU
  supply test point.

* Keep the pin map in one place in the test code, a table from the net name to its header, pin
  and divider ratio, so each test item looks up its pin by name,

  ::

      VOLTAGE_MAP = {
          "V3V3": {"hdr": 2, "pin": 10, "rdivf": 1.0},
          "VIN":  {"hdr": 2, "pin": 15, "rdivf": 3.0},   # 3:1 divider on the Pogo board
      }

* Before ordering the Pogo board, check its schematic against the Pin Map and the header
  definition file, pin by pin.  A wrong pin disables a test until the Pogo board is fixed.
* Bring up the Pogo board one pin at a time with `A4401_BOND_cli.py`, with a known good DUT,
  before writing the tests, see :ref:`prism_bond:Command Line`.


The Worksheet
*************

Keep the analysis in a spreadsheet with four lists, one set per board.

**Components**, one row per passive part, and one row per pin of each IC, transistor and connector,

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Column
     - Content
   * - Ref, Pin
     - reference designator, and the pin for a multi-pin part (blank for a two pin passive)
   * - Net
     - the net, or nets, the pin or part connects to
   * - Part
     - value or part number
   * - Short, Open, Value
     - `Y` detected, `P` partly detected, `N` not detected, `-` does not apply (Value of an IC pin)
   * - Tests
     - the test ids that detect the faults
   * - Notes
     - why a fault is partly or not detected, and the fault a limit is set to catch

Mark a fault `P` when the test only finds a gross fault, for example a capacitor shorted but not
missing, a value a decade off but not one step off, or a short to GND but not to the next pin.

Summarize each part as **Full** (every fault that applies is `Y`), **Partial** or **None**, and
count them per board.

**Tests**, one row per test, in the order they run,

* Test id, for example `T1-03b`: board number, test group, and a letter per test in the group
* Test name, Setup or preconditions, Stimulus, Measured, Nominal, Min, Max, Unit
* Verifies (full), Verifies (partly): the parts, as reference designators
* Notes: how the nominal value was calculated, and which faults the limits catch

A part on another board (two boards tested together) is written `<board>:<ref>`.

**Pin Map**, one row per test point and per Pogo board circuit: the test point (or circuit), its
net, its location on the PCB, the BOND header and pin, the mode (ADC, DAC, GPO, GPI, or a fixed
pin such as GND or SWD), and the tests that use it.  Total the general purpose pins per header
against the `Pin Budget`_.

**Gaps**, one row per group of parts that is not fully covered: the parts, what they are, why
they can't be fully covered, and a possible mitigation (a test point, a Pogo board circuit, test
firmware, optical inspection, or accept the risk).

Each test item in the Prism script can then use the same test id, so a failing item points to
the parts to check, see :doc:`Scripts <prism_scripts>`.


Doing the Analysis
******************

#. Collect the schematic, the BOM, the list of nets with test points (or the PCB layout), and the
   connectors and programming header the jig can reach.  Find out whether the DUT's MCU can run
   test firmware.
#. List the BOND resources and Pogo board circuits you can use, see `BOND Resources`_.
#. List the test points with their location on the PCB, and start the Pin Map.
#. Fill in the Components list from the BOM: one row per passive, one row per IC pin.  Start from
   the `Common Gaps`_, which give the usual answer for many parts.
#. Work through the schematic block by block (power, MCU, each peripheral, each analog chain).
   For each block, choose the tests from `Techniques`_ that cover its parts, and calculate the
   nominal values from the schematic.
#. For each part and pin, mark Short, Open and Value with the test that detects the fault.  Be
   strict: a fault is only detected if the measurement leaves the limits.
#. Review every `N` and `P`.  Add a test point, a Pogo board circuit or a test firmware command
   where it is cheap, otherwise list it in the Gaps.
#. Assign each test point and Pogo board circuit to a header pin, nearest header first, and
   check the total against the `Pin Budget`_.
#. Put the tests in the `Test Order`_ and set the initial limits, see `Limits`_.


Test Order
**********

#. **Unpowered** - resistance between rails and GND, 0 ohm links, termination and RC networks.
   A short found here can't damage the board.
#. **Power up, current limited, MCU held in reset** - input current, rail voltages, and default
   states (for example a rail held off by a pull-down on its enable).
#. **Program** - connect to the MCU, read its id, program test firmware and verify it.
#. **Pull resistors** - before any functional test changes the pin states.
#. **Clocks** - crystal start up, then frequency.
#. **Rails and references** switched on by the firmware.
#. **Functional blocks** - analog chains, bus peripherals, LEDs and displays, chargers, interfaces.
#. **Run and sleep current** - last, with everything in a known state.

Put the tests with the most likely and cheapest faults first, see
:ref:`_prodplan:Planning Your Test Stages`.


Techniques
**********

Each technique, how to do it with BOND, and the faults it usually detects.

.. list-table::
   :header-rows: 1
   :widths: 22 48 30

   * - Technique
     - How
     - Detects
   * - Resistance
     - Unpowered.  DAC through a known resistor on the Pogo board into the test point, ADC reads
       the test point, R = R_known * V / (V_dac - V).  For continuity to GND, expect near 0V.
     - Short to GND, Open of 0 ohm links and connector GND pins, resistor Value
   * - Divider with a known load
     - The DUT pulls a test point up to a rail; the Pogo board switches a known resistor to GND;
       ADC reads the ratio to the rail.
     - Pull resistor Open and Value
   * - RC step
     - DAC steps through a known resistor, ADC samples the rise.  Only for time constants slow
       enough for the ADC sample rate.
     - Capacitor Open and Value, resistor Value
   * - Supply current
     - VDUT or VBAT with a low current limit, MCU held in reset.  Limit from known good boards.
     - Shorts on any rail (capacitors, diodes, ICs), reversed parts.  Partial for most parts.
   * - Rail voltage
     - ADC on the rail test point, or the programmer's target voltage, or the MCU reading its
       internal reference.
     - Regulator, feedback divider Value, inductor Open
   * - Default state
     - Rails and outputs while the MCU is held in reset.
     - Pull-down or pull-up Open on enables and resets
   * - Program and id
     - SWD connect, read the MCU id, program and verify.  The MCU booting from flash proves the
       boot pin pull resistor.
     - MCU pins for SWD, reset, boot, supply.  Series resistors on SWD lines.
   * - UART echo
     - Test firmware echoes frames over the debug UART, count errors.
     - Series resistors and UART pins Open
   * - Pull resistor decay
     - Test firmware drives the pin opposite to its pull, switches it to input with no internal
       pull, and reads it after a delay, sweeping the delay (about 0.25-200 us).  A 100k pull
       flips in a few us; with no resistor the pin holds its level for much longer.
     - Pull resistor Open, and Value to within a decade.  Not for a line that another device
       drives, or that has a bus-hold input.
   * - Crystal
     - Start up time, then frequency against a reference clock from the Pogo board or test
       equipment, in ppm.
     - Crystal Open and Short, load capacitor Open and Value (with tight limits)
   * - Bus peripheral
     - Test firmware reads the device id, writes and reads back registers, or writes and reads
       back a flash block.
     - The IC fitted (right part), its bus, select, reset and supply pins.  Bus pull-ups partly.
   * - Analog chain
     - DAC drives the input at two or three levels (gain and offset), then a sine at a few
       frequencies around each filter corner, read by the chain's ADC.
     - Gain resistor Value, chain Open, filter capacitors partly
   * - Voltage monitor
     - Known supply voltage, the MCU reads the monitor divider.
     - Divider resistor Value, monitor switch Open
   * - Load switch
     - Switch on with a load on the Pogo board, then off.
     - Switch IC, enable resistors
   * - LEDs and segments
     - Light one at a time, measure the increase in supply current; repeat at two supply
       voltages to get the slope.
     - LED Open, Short and reversed, series resistor Value
   * - Protection and charger
     - Sweep the battery emulator or DUT supply, find the threshold (UVLO, cut-off, float voltage).
     - Threshold divider Value, protection IC


Common Gaps
***********

These parts are usually only partly covered, whatever the test.

* **Decoupling and bulk capacitors** - Short is found by the supply current or rail voltage.
  Open and Value are not detected.
* **TVS, ESD and clamp diodes** - only a Short is detected.
* **Filter capacitors** on reset lines, ADC inputs and data lines - the circuit works without them,
  only a Short is detected.
* **Regulator compensation, soft start and frequency setting parts** - only gross faults change
  the output, mark Value `P` at best.
* **Pull resistors on a line that another device drives, or that is not on an MCU pin** - the
  decay test can't be used.  Add a test point, or accept.
* **Parts in parallel with a driven net**, for example a button in parallel with a GPIO that the
  test drives - only a Short is detected.
* **Switches and buttons** that are never pressed - only a Short is detected.  A solenoid plunger
  or a manual press step covers them.
* **Parts that are electrically the same when rotated**, for example some displays and
  connectors - orientation is not detected.  A camera or phototransistor covers it.
* **Thermal pads** - not detected electrically, use X-ray.
* **Protection features that are not exercised**, for example an over-charge cut-off or reverse
  blocking - list them, and test them if a fault would be unsafe.
* **RF parts, antenna ports and connectors not used by the jig** - excluded from the test, list them.
* **Unused connector pins** - Open is not detected.
* **A wrong value within the test limits** - for example a 1% resistor tested with 10% limits,
  mark Value `P`.

Optical inspection (AOI) or X-ray at assembly covers many of these.  List them in the Gaps so the
assembler knows what the test does not find.


Limits
******

* Calculate the nominal value from the schematic, and write the calculation in the Notes.
* Start with wide initial limits from the part tolerances.
* Tighten the limits on at least 5 known good boards: mean +/- max(5 sigma, stated tolerance).
* Some tests have no calculated limit, for example supply current, noise and frequency response.
  Leave the limits blank in the worksheet and set them from the known good boards, for example
  mean +/- 20% for a run current.
* Check that the fault a test is meant to find falls outside the limits, for example a resistor
  one E-series step off, or a capacitor missing, and note it.  If it doesn't, mark the fault `P`.

Put the limits in the script `args`, so they can be tightened without changing code, see
:ref:`_prodplan:Planning Your Test Stages`.
