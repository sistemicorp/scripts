# Sistemi Prism Demo Example Scripts

## prod_v0
* Three examples
  * prod_0
    * all APIs in use
  * prod_1
    * how "subs" work in replacing values in a script
  * prod_2
    * how multiple tests work
* These examples use the "fake" HWDRV, which sets the number of channels
  * As an experiment, edit the driver (./public/prism/drivers/fake/fake.py) and change NUM_CHANNELS up to 4

## dso_v0
* example connecting to an Agilent DSO7104B using the VISA modules, on USB or Ethernet
  * one scope shared by all channels (`{"only_one": true}`), or one scope per channel
  * without the DSO, the system will fail to run the script
* As an experiment, if you have a similiar Agilent DSO, you should be able to modify the driver and use your scope
  * see ./public/prism/drivers/agilent_dso_usb_1

## teensy4_v0
* Various Teensy4 scripts and examples.
* Teensy4 information can be found here: https://www.pjrc.com/store/teensy41.html

## BOND
* Example Bed of Nails Design, a Sistemi open source Board Level Tester (BLT)
* BOND is based on the Teensy4

## brother_v0
* Example

## nRF52833-DK
* Example how to discover and program NRF.

## barcode_count_v0
* Count items with a USB barcode scanner, each scan of P###-S##### is one result
* Uses the scanners HWDRV, which finds the scanner and restarts the script after each scan
* Make QR code sheets with `make_barcodes.py`, see sample `barcodes_P001.pdf`
