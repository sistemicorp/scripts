Barcode Count Example
#####################

This example counts items with a USB barcode scanner.  Each item carries a 2D barcode, and every
scan becomes one test result, so Lente counts the items, by product and lot.

The example is in `public/prism/scripts/example/barcode_count_v0`,

* `count_0.scr` - the script
* `tst00xx.py` - the test program
* `make_barcodes.py` - makes a PDF sheet of QR codes to print
* `barcodes_P001.pdf` - a sample sheet

The driver is `public/prism/drivers/scanners`.


Barcode Format
==============

The barcode holds `P###-S#####`, where `P###` is the product model number and `#####` is the
product serial number, for example `P001-S00123`.

The test checks each scan against the regex in the script, `TST000_Scan` `args` `regex`,
`^(?P<product>P\d{3})-S(?P<sn>\d{5})$`.  The regex groups `product` and `sn` pick the fields
from the barcode, so a different barcode format only needs a new regex,

* `product` is saved as the result `info` `product`, `P001`
* `sn` is saved as `key0`, `sn:00123`
* the whole barcode is saved as the measurement `TST000_Scan.barcode`

A scan that does not match the format is recorded as a FAIL.

Scanning the same barcode twice makes two results.  To count each item once, select
`Unique units, last result` in the Lente Throughput & Yield chart, which counts each `product` and
`key0` once, see :doc:`Lente screenshots <lente_screenshots>`.

Make a sheet of barcodes to print with,

::

    cd public/prism/scripts/example/barcode_count_v0
    python make_barcodes.py --product P001 --start 123 --count 24

This writes `barcodes_P001.pdf`, 12 codes per Letter page.


Lot
===

The `Lot` is entered when the script is loaded, in the format `YYYYMMDD-##`, a date and a two
digit number, for example `20261025-01` for the first lot of the day.  It is saved as the result
`info` `lot`, and Lente can show yield and counts by lot.


Scanner
=======

The scanner must be in USB keyboard mode (HID), the usual factory setting.  The scanner "types" the
barcode followed by Enter, into the Prism text box.

* The Prism Test Portal page must have the keyboard focus when scanning
* The driver finds the scanner by its USB manufacturer, see `SCANNER_MANUFACTURERS` in
  `hwdrv_scanners.py`.  Datalogic is supported, add your scanner's manufacturer as required.
  `python public/prism/drivers/scanners/hwdrv_scanners.py` lists the scanners found.
* If no scanner is found, the script does not load
* A scanner in keyboard mode cannot be told apart from another scanner, or from the keyboard, so
  there is only one channel, even with more scanners attached.


Running
=======

After the script is loaded and started, the operator just keeps scanning.  The scanner driver
restarts the script after each scan, there is no button to press.

A scan made before Prism shows the next text box is lost, so Prism beeps when it is ready for the next
scan.  The driver checks every 0.2 seconds (`play_poll_sec`, see :doc:`Drivers <prism_drivers>`), so the
next text box is ready about a second after a scan.

* The beep plays on the Prism computer, using `aplay`.  Set `AUDIO_DEVICE` in `Scanners.py` if the
  default sound output is not the right one, `aplay -L` lists them.
* Set `"ready_beep": false` in the `TST000_Scan` `args` to turn the beep off.

The scan item has a 5 minute timeout (`"timeout": 300` in the script).  If nothing is scanned in
that time, the item is recorded as `TIMEOUT` and the script stops restarting, so an idle station
sends one `TIMEOUT` result, not one every 5 minutes.  To resume, press the channel number (Start)
button on the Test Portal, and the next good scan turns the automatic restarts back on.

Change the `timeout` to suit, see :ref:`Timeouts and Aborts <prism_programs:Timeouts and Aborts>`.


Command Line Testing
====================

The script runs with `prism_dev.py` (see :doc:`Development <_development>`), the barcode is scanned
into the terminal prompt,

::

    python prism_dev.py --script public/prism/scripts/example/barcode_count_v0/count_0.scr

`prism_dev.py` runs the script once, and the result file is written to the current folder.


Script
======

.. literalinclude:: ../../public/prism/scripts/example/barcode_count_v0/count_0.scr


Program
=======

.. literalinclude:: ../../public/prism/scripts/example/barcode_count_v0/tst00xx.py
   :language: python
