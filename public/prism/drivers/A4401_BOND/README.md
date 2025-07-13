# Sistemi (a44) Bed of Nails Design (BOND) Developer Guide


See the readme in `server` folder for developing on BOND's Teensy (with Arduino IDE).

1) Teensy RPC Development with the CLI

The CLI is a way of testing the BOND Prism API without having to run Prism.  Debugging outside of Prism is easier
and faster.  The downside is that for each API you add, you need to add it to the CLI.  But its worth it.
(Please maintain this CLI for debugging)

    - Using the A4401_BOND_cli.py program is how you will be testing/developing new APIs to the Teensy4 server.
    - Note the `-n` flag which will skip BOND initialization.  The first time BOND is used it requires
      initialization so that flag should not be used the first time.  There is no harm in not using the flag
      at all, but CLI would be slower because of the init work that is done.

BOND CLI Examples,


    (venv) martin@martin-ThinkPad-L13:~/git/scripts/public/prism/drivers/A4401_BOND$ python A4401_BOND_cli.py -p /dev/ttyACM0 version
           A4401_BOND.py   INFO   74 version 0.1.0
           A4401_BOND.py   INFO   85 attempting to install BOND on port /dev/ttyACM0
           A4401_BOND.py   INFO  312 version
           A4401_BOND.py   INFO  257 {'success': True, 'method': 'version', 'result': {'version': '0.1.0'}}
           A4401_BOND.py   INFO  321 status
           A4401_BOND.py   INFO  257 {'success': True, 'method': 'status', 'result': {'setup_fail_code': 0, 'stack_kb': 402, 'heap_kb': 492, 'psram_kb': 1572864}}
           A4401_BOND.py   INFO  171 HDR 1 pin 1 init {'mode': 'DAC,GPO', 'port': '10,1'}
           A4401_BOND.py   INFO  171 HDR 1 pin 2 init {'mode': 'GPO', 'port': '7'}
           A4401_BOND.py   INFO  171 HDR 1 pin 3 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 1 pin 4 init {'mode': 'GPO', 'port': '8'}
           A4401_BOND.py   INFO  171 HDR 1 pin 5 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 1 pin 6 init {'mode': 'DAC', 'port': '9'}
           A4401_BOND.py   INFO  171 HDR 1 pin 7 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 1 pin 8 init {'mode': 'DAC', 'port': '5'}
           A4401_BOND.py   INFO  171 HDR 1 pin 9 init {'mode': 'ADC', 'port': '6'}
           A4401_BOND.py   INFO  171 HDR 1 pin 10 init {'mode': 'GPO', 'port': '4'}
           A4401_BOND.py   INFO  171 HDR 1 pin 11 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 1 pin 12 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 1 pin 13 init {'mode': 'GPI', 'port': '0'}
           A4401_BOND.py   INFO  171 HDR 1 pin 14 init {'mode': 'ADC', 'port': '3'}
           A4401_BOND.py   INFO  171 HDR 1 pin 15 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 1 pin 16 init {'mode': 'ADC', 'port': '2'}
           A4401_BOND.py   INFO  171 HDR 1 pin 17 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 1 pin 18 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 1 pin 19 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 1 pin 20 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  196 ports_dac [5, 9, 10]
           A4401_BOND.py   INFO  197 ports_adc [2, 3, 6, 11]
           A4401_BOND.py   INFO  198 ports_gpo [1, 4, 7, 8]
           A4401_BOND.py   INFO  199 ports_gpi [0]
           A4401_BOND.py   INFO  257 {'success': True, 'method': 'bond_max_hdr_init', 'result': {'regs_seq_len': 35}}
           A4401_BOND.py   INFO  171 HDR 2 pin 1 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 2 pin 2 init {'mode': 'DAC', 'port': '8'}
           A4401_BOND.py   INFO  171 HDR 2 pin 3 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 2 pin 4 init {'mode': 'DAC', 'port': '7'}
           A4401_BOND.py   INFO  171 HDR 2 pin 5 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 2 pin 6 init {'mode': 'DAC', 'port': '9'}
           A4401_BOND.py   INFO  171 HDR 2 pin 7 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 2 pin 8 init {'mode': 'DAC', 'port': '5'}
           A4401_BOND.py   INFO  171 HDR 2 pin 9 init {'mode': 'DAC', 'port': '6'}
           A4401_BOND.py   INFO  171 HDR 2 pin 10 init {'mode': 'GPO', 'port': '4'}
           A4401_BOND.py   INFO  171 HDR 2 pin 11 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 2 pin 12 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 2 pin 13 init {'mode': 'GPI', 'port': '0'}
           A4401_BOND.py   INFO  171 HDR 2 pin 14 init {'mode': 'ADC', 'port': '3'}
           A4401_BOND.py   INFO  171 HDR 2 pin 15 init {'mode': 'ADC', 'port': '1'}
           A4401_BOND.py   INFO  171 HDR 2 pin 16 init {'mode': 'ADC', 'port': '2'}
           A4401_BOND.py   INFO  171 HDR 2 pin 17 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 2 pin 18 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 2 pin 19 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 2 pin 20 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  196 ports_dac [5, 6, 7, 8, 9]
           A4401_BOND.py   INFO  197 ports_adc [1, 2, 3, 11]
           A4401_BOND.py   INFO  198 ports_gpo [4]
           A4401_BOND.py   INFO  199 ports_gpi [0]
           A4401_BOND.py   INFO  257 {'success': True, 'method': 'bond_max_hdr_init', 'result': {'regs_seq_len': 33}}
           A4401_BOND.py   INFO  171 HDR 3 pin 1 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 3 pin 2 init {'mode': 'DAC', 'port': '8'}
           A4401_BOND.py   INFO  171 HDR 3 pin 3 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 3 pin 4 init {'mode': 'DAC', 'port': '7'}
           A4401_BOND.py   INFO  171 HDR 3 pin 5 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 3 pin 6 init {'mode': 'DAC', 'port': '1'}
           A4401_BOND.py   INFO  171 HDR 3 pin 7 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 3 pin 8 init {'mode': 'ADC', 'port': '2'}
           A4401_BOND.py   INFO  171 HDR 3 pin 9 init {'mode': 'DAC', 'port': '6'}
           A4401_BOND.py   INFO  171 HDR 3 pin 10 init {'mode': 'ADC', 'port': '3'}
           A4401_BOND.py   INFO  171 HDR 3 pin 11 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 3 pin 12 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 3 pin 13 init {'mode': 'GPI', 'port': '0'}
           A4401_BOND.py   INFO  171 HDR 3 pin 14 init {'mode': 'GPO', 'port': '4'}
           A4401_BOND.py   INFO  171 HDR 3 pin 15 init {'mode': 'ADC', 'port': '5'}
           A4401_BOND.py   INFO  171 HDR 3 pin 16 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 3 pin 17 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 3 pin 18 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 3 pin 19 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 3 pin 20 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  196 ports_dac [1, 6, 7, 8]
           A4401_BOND.py   INFO  197 ports_adc [2, 3, 5, 11]
           A4401_BOND.py   INFO  198 ports_gpo [4]
           A4401_BOND.py   INFO  199 ports_gpi [0]
           A4401_BOND.py   INFO  257 {'success': True, 'method': 'bond_max_hdr_init', 'result': {'regs_seq_len': 31}}
           A4401_BOND.py   INFO  171 HDR 4 pin 1 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 4 pin 2 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 4 pin 3 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 4 pin 4 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 4 pin 5 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 4 pin 6 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 4 pin 7 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 4 pin 8 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 4 pin 9 init {'mode': 'DAC', 'port': '6'}
           A4401_BOND.py   INFO  171 HDR 4 pin 10 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 4 pin 11 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 4 pin 12 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 4 pin 13 init {'mode': 'GPI', 'port': '0'}
           A4401_BOND.py   INFO  171 HDR 4 pin 14 init {'mode': 'GPO', 'port': '3'}
           A4401_BOND.py   INFO  171 HDR 4 pin 15 init {'mode': 'ADC', 'port': '1'}
           A4401_BOND.py   INFO  171 HDR 4 pin 16 init {'mode': 'ADC', 'port': '2'}
           A4401_BOND.py   INFO  171 HDR 4 pin 17 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 4 pin 18 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 4 pin 19 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  171 HDR 4 pin 20 init {'mode': None, 'port': None}
           A4401_BOND.py   INFO  196 ports_dac [6]
           A4401_BOND.py   INFO  197 ports_adc [1, 2, 11]
           A4401_BOND.py   INFO  198 ports_gpo [3]
           A4401_BOND.py   INFO  199 ports_gpi [0]
           A4401_BOND.py   INFO  257 {'success': True, 'method': 'bond_max_hdr_init', 'result': {'regs_seq_len': 24}}
           A4401_BOND.py   INFO  130 Installed A4401BOND on port /dev/ttyACM0
       A4401_BOND_cli.py   INFO  263 version: Namespace(port='/dev/ttyACM0', _skip_init=False, verbose=0, _cmd='version')
           A4401_BOND.py   INFO  312 version
           A4401_BOND.py   INFO  257 {'success': True, 'method': 'version', 'result': {'version': '0.1.0'}}
       A4401_BOND_cli.py   INFO  266 {'success': True, 'method': 'version', 'result': {'version': '0.1.0'}}
       A4401_BOND_cli.py   INFO  502 Success
           A4401_BOND.py   INFO  141 closing /dev/ttyACM0
    (venv) martin@martin-ThinkPad-L13:~/git/scripts/public/prism/drivers/A4401_BOND$ python A4401_BOND_cli.py -p -n /dev/ttyACM0 led --on
    ...
    (venv) martin@martin-ThinkPad-L13:~/git/scripts/public/prism/drivers/A4401_BOND$ python A4401_BOND_cli.py -p -n /dev/ttyACM0 led --off
    ...
    (venv) martin@martin-ThinkPad-L13:~/git/scripts/public/prism/drivers/A4401_BOND$ python A4401_BOND_cli.py -p /dev/ttyACM0 -n bond_max_hdr_adc_cal --header 3
           A4401_BOND.py   INFO   74 version 0.1.0
           A4401_BOND.py   INFO   85 attempting to install BOND on port /dev/ttyACM0
           A4401_BOND.py   INFO  312 version
           A4401_BOND.py   INFO  257 {'success': True, 'method': 'version', 'result': {'version': '0.1.0'}}
           A4401_BOND.py   INFO  321 status
           A4401_BOND.py   INFO  257 {'success': True, 'method': 'status', 'result': {'setup_fail_code': 0, 'stack_kb': 402, 'heap_kb': 492, 'psram_kb': 1835008}}
           A4401_BOND.py   INFO  130 Installed A4401BOND on port /dev/ttyACM0
       A4401_BOND_cli.py   INFO  401 bond_max_hdr_adc_cal: Namespace(port='/dev/ttyACM0', _skip_init=True, verbose=0, _cmd='bond_max_hdr_adc_cal', _hdr=3)
           A4401_BOND.py   INFO  565 bond_max_hdr_adc_cal 3
           A4401_BOND.py   INFO  257 {'success': True, 'method': 'bond_max_hdr_adc_cal', 'result': {'mV': 2562}}
       A4401_BOND_cli.py   INFO  404 {'success': True, 'method': 'bond_max_hdr_adc_cal', 'result': {'mV': 2562}}
       A4401_BOND_cli.py   INFO  502 Success
           A4401_BOND.py   INFO  141 closing /dev/ttyACM0


The BOND CLI has many commands, use `--help` to see all of them.


      $ python A4401_BOND_cli.py --help
      usage: A4401_BOND_cli.py [-h] -p PORT [-n] [-v] {led,uid,version,write_gpio,read_gpio,read_adc,bist_voltage,vbat_read,vbat_set,vbus_read,iox_led_green,iox_led_yellow,iox_led_red,iox_led_blue,iox_vbus_en,iox_vbat_en,iox_vbat_con,bond_max_hdr_adc_cal,bond_max_hdr_adc,bond_max_hdr_dac} ...
      
      A4401_BOND_cli
      
      positional arguments:
        {led,uid,version,write_gpio,read_gpio,read_adc,bist_voltage,vbat_read,vbat_set,vbus_read,iox_led_green,iox_led_yellow,iox_led_red,iox_led_blue,iox_vbus_en,iox_vbat_en,iox_vbat_con,bond_max_hdr_adc_cal,bond_max_hdr_adc,bond_max_hdr_dac}
                              commands
      
      options:
        -h, --help            show this help message and exit
        -p PORT, --port PORT  Active serial port
        -n, --no-init         Do not init (its presumed BOND has been previously initialized)
        -v, --verbose         Increase verbosity


2) BOND Header Pin Configuration

   - Review BOND schematic, specifically the `Header #` pages.
   - Each header is connected up to a MAX11311 pin which can be configured as an ADC, DAC, GPO or GPI.
   - A json-like file is used to define the setup for each header.  Note the file allows single line
     comments (unlike a pure JSON file.
   - All pins on the header must be listed in the file.
   - For different Pogo boards, for different DUTs, a different header definition file can be used.
   - The header file is specified in the script, in the `drivers` section.


3) Walk thru of an API call

   - At the top level is the script test item (`public/prism/scripts/example/BOND_v0/bond_test_0.scr`),


      {"id": "P1100_ADC_check",      "enable": true, "hdr": 1 },


   - The corresponding code in the associated Python file (`bond_P00xx.py`),


    def P1100_SETUP(self):
        """ ADC Check/Validate conversion
        - each MAX11311 on each header has an ADC input connected to Voltage Reference
          for self testing each chip
        - BOND's reference voltage is 2500mV

        {"id": "P1100_ADC_check",      "enable": true, "hdr": 1 },

        """
        ctx = self.item_start()  # always first line of test
        EXPECTED_MV = 2500
        TOLERANCE_MV = 100

        if not (1 <= ctx.item.hdr <= 4):
            self.logger.error(f"invalid header index, 1 <= {ctx.item.hdr} <= 4")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        response = self.teensy.bond_max_hdr_adc_cal(ctx.item.hdr)    <--- CALLING HERE
        if not response['success']:
            self.logger.error(response)
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        success, _result, _bullet  = ctx.record.measurement(f"adc_cal_hdr_{ctx.item.hdr}",
                                                            response['result']['mV'],
                                                            min=EXPECTED_MV - TOLERANCE_MV,
                                                            max=EXPECTED_MV + TOLERANCE_MV)
        self.log_bullet(_bullet)

        self.item_end()  # always last line of test


   - The Python side BOND class method (`A4401_BOND.py`),


    def bond_max_hdr_adc_cal(self, hdr: int):
        """ MAX11311 Header <1-4> read ADC CAL (port 11) voltage
        - expected result is always 2500 +/- error

        :return: {'success': True, 'method': 'bond_max_hdr_adc_cal',
                  'result': {'mV': <int> }
        """
        with self._lock:
            self.logger.info(f"bond_max_hdr_adc_cal {hdr}")
            answer = self.rpc.call_method('bond_max_hdr_adc_cal', hdr)
            return self._rpc_validate(answer)

   - The Teensy Arduino server side code (`public/prism/drivers/A4401_BOND/server/teensy4_server/bond_max_hdr.ino`),


      /* Read Header <1-4> ADC Port 11 cal voltage
       * - all MAX11311's Port 11 is connected to 3300mV voltage
       */
      String bond_max_hdr_adc_cal(int hdr) {
        DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
      
        MAX11300 *max = _get_max_from_hdr(hdr);
        if (max == NULL) {
          doc["result"]["error"] = "1 <= hdr <= 4, invalid parameter";
          doc["success"] = false;
          return _response(doc);
        }  
        
        digitalWrite(MAX11311_COPNVERT_Pin, LOW);
        delayMicroseconds(2);
        digitalWrite(MAX11311_COPNVERT_Pin, HIGH);
        delayMicroseconds(100);
      
        uint16_t data = 0;
        MAX11300::CmdResult result = max->single_ended_adc_read(MAX11300::PIXI_PORT11, &data);
        if (result != MAX11300::Success) {
          doc["result"]["error"] = "single_ended_adc_read error";
          doc["success"] = false;
          return _response(doc);    
        }
      
        doc["result"]["mV"] = (data << 1) + (data >> 1);  // raw * 2.5 = mV
      
        oled_print(OLED_LINE_RPC, __func__, !doc["success"]);
        return _response(doc);  // always the last line of RPC API
      }

