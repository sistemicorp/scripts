# Sistemi (a44) Bed of Nails Design (BOND) Developer Guide

NOTE: When working with Prism scripts, the Arduino IDE must be closed or else bad things may happen.

See the readme in `server` folder for developing on BOND's Teensy (with Arduino IDE or arduino-cli).

Reference documents in this folder:
- `a4402-SCH_05.pdf`, BOND schematic (project a44, board a4402)
- `a4402-SPC_ProductBrief_01.pdf`, product brief
- The MAX11311 datasheet is not redistributed, download it from Analog Devices.

1) Teensy RPC Development with the CLI

The CLI is a way of testing the BOND Prism API without having to run Prism.  Debugging outside of Prism is easier
and faster.  The downside is that for each API you add, you need to add it to the CLI.  But its worth it.
(Please maintain this CLI for debugging)

    - Using the A4401_BOND_cli.py program is how you will be testing/developing new APIs to the Teensy4 server.
    - The CLI uses `pogo_hdr_definition._json` in this folder for the header pin definitions.
    - The CLI inits BOND every time it is called, because between CLI runs it can't keep state.
      Use `-n` to skip sending the header definition to BOND (the file is still read for pin lookups).
    - The CLI exits with 0 on success and 1 on failure.
    - BOND calibrates the battery emulator at power up. `bond_batt_emu_cal` repeats it.

BOND CLI Examples,

    $ cd ~/git/scripts/public/prism/drivers/A4401_BOND
    $ python A4401_BOND_cli.py -p /dev/ttyACM0 status
           A4401_BOND.py   INFO   81 version 0.2.0
           A4401_BOND.py   INFO  108 installing BOND on port /dev/ttyACM0 using .../pogo_hdr_definition._json
           A4401_BOND.py   INFO  211 version
           A4401_BOND.py   INFO  395 {'success': True, 'method': 'version', 'result': {'version': '0.2.0'}}
           ...
           A4401_BOND.py   INFO  211 bond_max_hdr_init (1, [6, 11], 2, [], 0, [1, 7, 8], 3, [], 0, 3300, 1000)
           A4401_BOND.py   INFO  395 {'success': True, 'method': 'bond_max_hdr_init', 'result': {'hdr': 1}}
           ...
           A4401_BOND.py   INFO  176 Installed A4401BOND on port /dev/ttyACM0
       A4401_BOND_cli.py   INFO  502 status: Namespace(port='/dev/ttyACM0', _skip_init=False, verbose=0, _cmd='status')
           A4401_BOND.py   INFO  395 {'success': True, 'method': 'status', 'result': {'setup_fail_code': 0, 'stack_kb': 401, 'heap_kb': 496, 'psram_kb': 0}}
       A4401_BOND_cli.py   INFO  666 Success
           A4401_BOND.py   INFO  187 closing /dev/ttyACM0
    $ python A4401_BOND_cli.py -p /dev/ttyACM0 -n led --on
    $ python A4401_BOND_cli.py -p /dev/ttyACM0 -n bond_max_hdr_adc_cal --header 3
    $ python A4401_BOND_cli.py -p /dev/ttyACM0 -n bond_max_hdr_gpo --header 1 --pin 1 --enable
    $ python A4401_BOND_cli.py -p /dev/ttyACM0 -n bond_ldo_set --mv 3300


The BOND CLI has many commands, use `--help` to see all of them, and `<command> --help` for a command's
arguments.

      $ python A4401_BOND_cli.py --help
      usage: A4401_BOND_cli.py [-h] -p PORT [-n] [-v] {led,uid,version,...} ...

      options:
        -h, --help            show this help message and exit
        -p PORT, --port PORT  Active serial port
        -n, --no-init         Do not send the header definition to BOND (presumed previously initialized),
                              the file is still read for pin lookups
        -v, --verbose         Increase verbosity


2) BOND Header Pin Configuration

   - Review BOND schematic, specifically the `Header #` pages.
   - Each header is connected up to a MAX11311 whose ports can be configured as an ADC, DAC, GPO or GPI.
   - A json-like file is used to define the setup for each header.  Note the file allows single line
     comments (unlike a pure JSON file).
   - Each pin entry is `{"mode": <mode>, "port": <port>}`, mode is "ADC", "DAC", "GPO", "GPI" or null.
     A pin wired to two ports lists both, for example `{"mode": "ADC,GPO", "port": "6,9"}`.
   - Ports are 0-10, each port may be used once per header. The driver always configures,
     and the file must not list,
       - port 11 of every header, wired to the 2.5V reference for self test, see `bond_max_hdr_adc_cal`
       - HDR3 port 9, the relay that connects VBUS to the External USB-C, see `vbus_en`
   - `gpo_mv` is the GPO logic-high voltage (0-10000 mV) and `gpi_mv` the GPI threshold (0-2500 mV),
     for all GPOs/GPIs on that header.
   - HDR1 pin 1 is an LDO output: its GPO (port 1) enables it, `bond_ldo_set` sets its voltage
     (600-3900 mV), and pin 9 (ADC port 6) reads it back.
   - DAC outputs start at 0V, and `reset` (start and end of every test) sets DACs to 0V and GPOs to
     their idle level.
   - Ranges: ADC and DAC are 0-10000 mV.
   - The file is checked when BOND is installed, an invalid file fails the install.
   - For different Pogo boards, for different DUTs, a different header definition file can be used.
   - The header file is specified in the script, in the `drivers` section.


3) Walk thru of an API call

   - At the top level is the script test item (`public/prism/scripts/example/BOND_v0/bond_selftest_0.scr`),


      {"id": "P1100_ADC_check",      "enable": true, "hdr": 1 },


   - The corresponding code in the associated Python file (`bond_P00xx.py`),


    def P1100_ADC_check(self):
        """ ADC Check/Validate conversion
        - each MAX11311 on each header has an ADC input connected to Voltage Reference
          for self testing each chip
        - BOND's reference voltage is 2500mV

        {"id": "P1100_ADC_check",      "enable": true, "hdr": 1 },

        """
        ctx = self.item_start()  # always first line of test
        EXPECTED_MV = 2500
        TOLERANCE_MV = 15

        ...

        response = self.teensy.bond_max_hdr_adc_cal(ctx.item.hdr)    <--- CALLING HERE
        if not response['success']:
            self.logger.error(response)
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        success, _result, _bullet  = ctx.record.measurement(f"adc_cal_hdr_{ctx.item.hdr}",
                                                            response['result']['mV'],
                                                            unit=ResultAPI.UNIT_MILLIVOLTS,
                                                            min=EXPECTED_MV - TOLERANCE_MV,
                                                            max=EXPECTED_MV + TOLERANCE_MV)
        self.log_bullet(_bullet)

        self.item_end()  # always last line of test


   - The Python side BOND class method (`A4401_BOND.py`),


    def bond_max_hdr_adc_cal(self, hdr: int):
        """ MAX11311 Header <1-4> read ADC CAL (port 11) voltage
        - expected result is always 2500 +/- error

        :return: {'success': True, 'method': 'bond_max_hdr_adc_cal',
                  'result': {'mV': <int>}}
        """
        return self._call('bond_max_hdr_adc_cal', hdr)

   - `_call()` holds the driver lock, and turns a serial error into `{'success': False, ...}`.

   - The Teensy Arduino server side code (`server/teensy4_server/bond_max_hdr.cpp`),


      String bond_max_hdr_adc_cal(int hdr) {
        JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API

        _hdr_t *h = NULL;
        const char *err = _hdr_port(hdr, HDR_PORT_CAL, HDR_MODE_ADC, &h);
        if (err) return rpc_error(doc, err);

        doc["result"]["mV"] = _adc_read_mv(h, HDR_PORT_CAL);
        return rpc_response(doc);  // always the last line of RPC API
      }

   - Note the `response` is passed all the way back to the calling script Python function.
