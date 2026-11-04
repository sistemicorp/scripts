# Example BOND

BOND (Bed of Nails Design) is Sistemi's open source Board Level Tester (BLT), built around a
Teensy 4.1.  This folder is the example Prism test program for BOND.  Copy it to start your own product.

## Repositories

* [sistemicorp/a44-BOND](https://github.com/sistemicorp/a44-BOND): the BOND hardware, an Altium
  Designer project (schematics, PCB, output jobs).  The released schematic is
  `public/prism/drivers/A4401_BOND/a4402-SCH_05.pdf` (board a4402, rev 02).
* [sistemicorp/a5800-BONDPogo](https://github.com/sistemicorp/a5800-BONDPogo): the Pogo board
  template, an Altium Designer project.  It has the four BOND headers already placed, a spring
  pin part and a 3D model of BOND.  Start your product's Pogo board from it, see the
  BOND page of the Prism docs (`docs/source/prism_bond.rst`).
* This repo (`scripts`): the BOND firmware, the Python driver and this example.

## Files

| File | What it is |
|------|------------|
| `bond_P00xx.py` | Test code for all the scripts in this folder |
| `bond_selftest_0.scr` | BOND self test, no Pogo board or DUT connected |
| `bond_update_0.scr` | Update the firmware of BONDs that are already programmed, any version |
| `bond_progfresh_0.scr` | Program a new (never programmed) BOND, one BOND on USB |
| `assets/teensy4_server.ino.hex` (`.elf`) | The BOND firmware that the update/program scripts load |
| `assets/pogo_hdr_definition._json` | Pogo board pin to BOND header port mapping |

The driver and firmware are in `public/prism/drivers/A4401_BOND`,

| Path | What it is |
|------|------------|
| `A4401_BOND.py` | Python driver class, one method per firmware RPC |
| `hwdrv_A4401_BOND.py` | Prism HW driver for test scripts, checks the firmware version |
| `hwdrv_A4401_BOND_update.py` | Prism HW driver for `bond_update_0.scr`, accepts any firmware version |
| `hwdrv_A4401_BOND_prog.py` | Prism HW driver for `bond_progfresh_0.scr` |
| `A4401_BOND_cli.py` | Command line tool, calls each RPC without Prism |
| `README.md` | CLI usage, header definition rules, walk through of an API call |
| `server/README.md` | Arduino IDE / arduino-cli setup, building and flashing the firmware |
| `server/teensy4_server/` | The firmware (Arduino sketch) |

Unit tests for the driver, CLI and HW drivers are in `tests/test_a4401_bond.py`, run them with
`python -m pytest tests` from the `scripts` folder.  No BOND is needed.

## Init or Update your BOND board

* A new BOND: program it with the Arduino IDE, see
  `public/prism/drivers/A4401_BOND/server/README.md`, or use `bond_progfresh_0.scr`.
* A BOND that is already programmed: update it with `bond_update_0.scr`.  The Arduino IDE must be
  closed.  No Pogo board or jig is needed.

      ~/git/scripts$ python prism_dev.py --script public/prism/scripts/example/BOND_v0/bond_update_0.scr

  The update passes when `UPD020_verify` reads the new firmware version.  The test scripts refuse a
  BOND that runs a different firmware version than the Python driver, so update every BOND
  after a firmware change.

## How to use this Example

### Create your own product folder

For your own use of BOND, copy this folder to a new location, and modify the files as needed.
For example, create your product folder,

    ~/git/scripts/public/prism/scripts$ mkdir myproduct
    ~/git/scripts/public/prism/scripts$ cp -R example/BOND_v0/ myproduct/blt

Then, in the copy,

* change `"module"` in each `.scr` file to the new folder, for example
  `public.prism.scripts.myproduct.blt.bond_P00xx`,
* change the header definition path in `"drivers"` to the new `assets` folder,
* change `BOND_ASSETS_PATH` at the top of `bond_P00xx.py` to the new `assets` folder,
* rename the `BOND` test items to your stage, for example `BLT100_voltage`, and delete the
  example items you don't need.

### Create Pogo Board to BOND Header Mapping

In your new product folder, edit the file `public/prism/scripts/myproduct/blt/assets/pogo_hdr_definition._json`.
The rules for this file are in `public/prism/drivers/A4401_BOND/README.md`, section BOND
Header Pin Configuration.

## Developing BOND Functionality

You only need this section to add or change what BOND can do (a new RPC, a new on-board device,
different behaviour).  To write tests for your product, use the existing driver methods.

A BOND function goes through four layers.  A new function usually touches all of them,

    test item (bond_P00xx.py)   self.expect(self.teensy.vdut_set(3000))
      -> Python driver          A4401_BOND.vdut_set() -> self._call('vdut_set', mv)
        -> simpleRPC over USB serial
          -> firmware RPC       String vdut_set(uint16_t mv) in bond_vdut.cpp

### Firmware (Arduino) code patterns

The firmware is in `public/prism/drivers/A4401_BOND/server/teensy4_server`.  Follow the patterns
that are already there.

**Module layout**

* `teensy4_server.ino` only has `setup()`, `loop()` and the RPC table (`interface()`).  Keep it
  small, and put new code in a module.
* Each module is a `.h`/`.cpp` pair for one part of the board, for example `bond_vdut.*` for
  the VDUT supply and `battemu.*` for the battery emulator.  Add a new pair for a new
  device or block, and add it to the module list at the top of `teensy4_server.ino`.
* The module header begins with a comment naming the part and its schematic sheet.  It holds
  the hardware constants (`#define`), then two sections,

      // internal API, use these from other modules, never the RPC functions
      int vdut_set_mv(uint16_t mv);

      // RPC API
      String vdut_set(uint16_t mv);

* Helpers used only inside a `.cpp` are `static`, with names starting with `_`
  (`_read_reg()`, `_vdut_oe()`).
* Teensy pin numbers go in `bond_pins.h` only, with the schematic net name in a comment.
* On-board I2C devices used by more than one module (INA226s, TMP1075, CYPD3176) are defined
  once in `bond_board.*`.
* Device libraries go in `src/<device>/`, not in the Arduino libraries folder, so the sketch
  builds from the repo.  The only external libraries are simpleRPC, ArduinoJson and INA226_WE,
  at the versions pinned in `server/README.md`.

**RPC functions**

Every RPC has the same shape (see `rpc_helpers.h`),

    String vdut_set(uint16_t mv) {
      JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API

      if (mv > VDUT_MAX_MV) return rpc_error(doc, "invalid arg exceeds maximum");
      if (vdut_set_mv(mv)) return rpc_error(doc, "TPS55289 i2c write");

      doc["result"]["mv"] = mv;
      return rpc_response(doc);  // always the last line of RPC API
    }

* The RPC returns a JSON string, `{"success": <bool>, "method": <name>, "result": {...}}`.
  On error, `rpc_error()` sets `success` false and `result.error` to a short message.
* **An RPC must never call another RPC.**  There is one response document, so the inner call
  would overwrite the outer response.  Call the module's internal function instead.  This is why
  every module has an internal API, for example `reset()` calls `bond_reset()`, and `bond_reset()`
  calls `vdut_connect()`, not `vdut_con()`.
* Check every argument in the RPC (range, header, port, mode) and return `rpc_error()`.  Never
  trust the caller.
* Keep RPCs fast (about 1 ms), and use no long `delay()`.  A short settle time is fine, for
  example `VDUT_SETTLE_MS`.  The display is not written by the RPC: `rpc_response()` writes into a
  RAM frame, and `loop()` sends it to the panel.
* An RPC that is polled (like `read_gpio` for jig closed) uses `rpc_begin(__func__, false)` so it
  stays off the display.  Errors are always shown.
* Responses are limited to `RPC_RESPONSE_MAX` characters, and a longer response becomes an
  error.  Return values, not large tables.
* Internal functions return `0` on success and non-zero on failure.  Write a short message to
  the display with `oled_print(OLED_LINE_DEBUG, buf, true)`, using a `LINE_MAX_LENGTH` (21 char)
  buffer and `snprintf()`.

**Adding an RPC**

1. Write the RPC in its module `.cpp`, declare it under `// RPC API` in the module header.
2. Add it to `interface()` in `loop()` (`teensy4_server.ino`).  The description string must begin
   with the function name, `vdut_set, "vdut_set: Set VDUT voltage mV",`.
3. simpleRPC argument types: use `int`, `uint16_t`, `bool`, `String` / `String &`, and
   `int *` with a length for lists (see `bond_max_hdr_init`).  The Python side passes the same order.
4. Bump `version.h`.  The Python driver reads this same file, and refuses a BOND that runs a
   different version.  This is how a station knows its BOND firmware matches its scripts.

**DUT safety and setup**

* `bond_reset()` (the `reset` RPC, called at the start and end of every test) puts BOND in the
  DUT safe state: VDUT and VBAT disconnected, self test load off, header DACs 0 V, GPOs idle.
  A new output that can drive the DUT must be turned off there.
* A new device that must work for BOND to be usable is checked in `_setup()` in
  `teensy4_server.ino`.  Add a `SETUP_FAIL_*` bit for it.  The Python driver's `init()` refuses a
  BOND whose `status` shows a non-zero `setup_fail_code`.
* The firmware's ranges (`VDUT_MAX_MV`, `HDR_DAC_MV_MAX`, ...) and the Python driver's ranges
  must agree.

### Python driver patterns

In `public/prism/drivers/A4401_BOND`,

* Add one method to `A4401_BOND.py` per RPC, named like the RPC, with a docstring that gives the
  argument range and an example return,

      def vdut_set(self, mv: int):
          """ Set VDUT Voltage in mV, 1000-9000

          :return: {'success': True, 'method': 'vdut_set',
                    'result': {'mv': 3000, 'measured_mv': 3001}}
          """
          return self._call('vdut_set', mv)

* Always go through `_call()`.  It holds the driver lock (one RPC at a time on the serial port),
  logs the call, and turns a serial error into `{'success': False, ...}`.  Never raise to the test
  code.
* Argument checks that Python can do (ranges, header pin lookups) return `self._error(...)`
  before the RPC is called, see `bond_ldo_set()`.
* `success` means the call ran, not that a measurement passed.  Test code passes the response to
  `self.expect()`, and checks values with `ctx.record.measurement()`.
* Add a subcommand to `A4401_BOND_cli.py` for every new RPC, and try the RPC from the CLI before
  using it in Prism, see `public/prism/drivers/A4401_BOND/README.md`.
* Add a unit test to `tests/test_a4401_bond.py`.  `FakeRPC` stands in for the serial link.
* If the change affects how BOND is used, update `docs/source/prism_bond.rst` and
  `docs/source/prism_drivers.rst`.

### Build, flash and check

1. Build with the Arduino IDE or with arduino-cli, see `server/README.md`.
2. Copy the new `teensy4_server.ino.hex` and `.elf` to `assets/` of this folder (and of your
   product folders that update BOND).
3. Close the Arduino IDE and run `bond_update_0.scr` with `prism_dev.py` (above).
4. Check with the CLI, then run `bond_selftest_0.scr` with no Pogo board connected.  The self
   test waits for the jig to be closed (BOND GPIO 6 reads 1).
5. Commit the firmware source, `version.h`, the Python driver and the `assets` files together.
