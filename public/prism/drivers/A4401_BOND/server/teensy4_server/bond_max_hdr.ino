/*  Sistemi Corporation, copyright, all rights reserved, 2023
 *  Martin Guthrie
 *  
*/
#include "bond_max_hdr.h"
#include "src/oled/bond_oled.h"

#define BIST_VREF_TOL_MV    20
#define BIST_VREF_MV        2500

// default IOX MAX11311 resisters, set on init
// this array is pulling from init code that auto generated from
// MAX11300/01/11/12 Configuration Software (Ver. 1.1.0.5) 16/10/2025 17:41
// The file a4402-MAX11300Design_hdr_01.mpix is the source file for the tool.
// Then generate the header file, and then pull out the programming sequence.
static _init_regs_t init_hdr_regs[] = {
  {.r = device_control, .d = 0x8000}, // reset
  {.r = device_control, .d = 0xc0 & 0x40b0},
  {.r = port_cfg_p11, .d = 0x7100},
  {.r = device_control, .d = 0xc0 & 0x40FF},
  {.r = device_control, .d = 0xc0},
  {.r = interrupt_mask, .d = 0xffff},
};


 MAX11300 *_get_max_from_hdr(int hdr) {
  switch (hdr) {
    case 1: return &max_hdr1;
    case 2: return &max_hdr2;
    case 3: return &max_hdr3;
    case 4: return &max_hdr4;
  }
  return NULL;
 }

 uint8_t _get_max_cs_from_hdr(int hdr) {
  switch (hdr) {
  case 1: return SPI_CS_HRD1_Pin; 
  case 2: return SPI_CS_HDR2_Pin; 
  case 3: return SPI_CS_HDR3_Pin; 
  case 4: return SPI_CS_HDR4_Pin;   
  }
  return 0;
 }

MAX11300RegAddress_t _reg_dac_data_port(int port) {
  switch (port) {
    case 0: return dac_data_port_p0;
    case 1: return dac_data_port_p1;
    case 2: return dac_data_port_p2;
    case 3: return dac_data_port_p3;
    case 4: return dac_data_port_p4;
    case 5: return dac_data_port_p5;
    case 6: return dac_data_port_p6;
    case 7: return dac_data_port_p7;
    case 8: return dac_data_port_p8;
    case 9: return dac_data_port_p9;
    case 10: return dac_data_port_p10;
    case 11: return dac_data_port_p11;
  }
  return dac_data_port_p0;  // squelch build warning
}

MAX11300RegAddress_t _reg_port_config_port(int port) {
  switch (port) {
    case 0: return port_cfg_p0;
    case 1: return port_cfg_p1;
    case 2: return port_cfg_p2;
    case 3: return port_cfg_p3;
    case 4: return port_cfg_p4;
    case 5: return port_cfg_p5;
    case 6: return port_cfg_p6;
    case 7: return port_cfg_p7;
    case 8: return port_cfg_p8;
    case 9: return port_cfg_p9;
    case 10: return port_cfg_p10;
    case 11: return port_cfg_p11;
  }  
  return port_cfg_p0;  // squelch build warning
}

MAX11300::MAX11300_Ports _get_port_from_int(int port) {
  switch (port) {
    case 0: return MAX11300::PIXI_PORT0;
    case 1: return MAX11300::PIXI_PORT1;
    case 2: return MAX11300::PIXI_PORT2;
    case 3: return MAX11300::PIXI_PORT3;
    case 4: return MAX11300::PIXI_PORT4;
    case 5: return MAX11300::PIXI_PORT5;
    case 6: return MAX11300::PIXI_PORT6;
    case 7: return MAX11300::PIXI_PORT7;
    case 8: return MAX11300::PIXI_PORT8;
    case 9: return MAX11300::PIXI_PORT9;
    case 10: return MAX11300::PIXI_PORT10;
    case 11: return MAX11300::PIXI_PORT11;
  }  
  return MAX11300::PIXI_PORT0;  // squelch build warning  
}

String bond_max_hdr_init(int hdr,  // 1-4
                         int *adcs, int adc_len,
                         int *dacs, int dac_len,
                         int *gpos, int gpo_len,
                         int *gpis, int gpi_len,
                         int gpo_mv, int gpi_mv) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  
  MAX11300 *max = _get_max_from_hdr(hdr);
  if (max == NULL) {
    doc["result"]["error"] = "1 <= hdr <= 4, invalid parameter";
    doc["success"] = false;
    return _response(doc);
  }

  #define MAX_INIT_SETTINGS  40
  _init_regs_t init_regs[MAX_INIT_SETTINGS];

  unsigned int i = 0;
  init_regs[i].r = device_control; init_regs[i].d = 0x8000; i++; // reset
  init_regs[i].r = device_control; init_regs[i].d = 0xc1 & 0x40b0; i++;
  init_regs[i].r = device_control; init_regs[i].d = 0xc1 & 0x40fc; i++;
  // Set reg DAC_DATA_port registers -----------------------------------------
  // GPIs
  uint16_t d = 0x0666;  // TODO: this comes from gpi_mv
  for (int j = 0; j < gpi_len; j++) {
    init_regs[i].r = _reg_dac_data_port(gpis[j]); init_regs[i].d = d; i++;
  }
  // GPOs
  d = 0x0666;  // TODO: this comes from gpo_mv?
  for (int j = 0; j < gpo_len; j++) {
    init_regs[i].r = _reg_dac_data_port(gpos[j]); init_regs[i].d = d; i++;
  }
  // DACs
  d = 0x0666;  // TODO: this comes from ??
  for (int j = 0; j < dac_len; j++) {
    init_regs[i].r = _reg_dac_data_port(dacs[j]); init_regs[i].d = d; i++;
  }  
  init_regs[i].r = dac_preset_data_1; init_regs[i].d = 0x0; i++;
  init_regs[i].r = dac_preset_data_2; init_regs[i].d = 0x0; i++;
  // Set reg PORT_CONFIG -----------------------------------------------------
  // GPIs
  d = 0x1000;  // TODO: this comes from ??
  for (int j = 0; j < gpi_len; j++) {
    init_regs[i].r = _reg_port_config_port(gpis[j]); init_regs[i].d = d; i++;
  }
  // delay 200us * num pins in mode 1 -> just delay 2ms!
  init_regs[i].r = reserved_6A; init_regs[i].d = 0x0; i++;  // !! DELAY 1 ms !!
  init_regs[i].r = reserved_6A; init_regs[i].d = 0x0; i++;  // !! DELAY 1 ms !!
  // GPODAT for ports in mode 3
  init_regs[i].r = gpo_data_P10P6_P5P0; init_regs[i].d = 0x0; i++;
  init_regs[i].r = gpo_data_P11; init_regs[i].d = 0x0; i++;
  // GPOs
  d = 0x3000;
  for (int j = 0; j < gpo_len; j++) {
    init_regs[i].r = _reg_port_config_port(gpos[j]); init_regs[i].d = d; i++;
  }
  // DACs
  d = 0x5100;  // TODO: where this come from?
  for (int j = 0; j < dac_len; j++) {
    init_regs[i].r = _reg_port_config_port(dacs[j]); init_regs[i].d = d; i++;
  }  
  // IRQ modes
  init_regs[i].r = gpi_irqmode_P5_P0; init_regs[i].d = 0x0; i++;
  init_regs[i].r = gpi_irqmode_P10_P6; init_regs[i].d = 0x0; i++;
  init_regs[i].r = gpi_irqmode_P11; init_regs[i].d = 0x0; i++;
  // ADCs
  d = 0x7100;  // TODO: where this come from?
  for (int j = 0; j < adc_len; j++) {
    init_regs[i].r = _reg_port_config_port(adcs[j]); init_regs[i].d = d; i++;
  }    
  init_regs[i].r = device_control; init_regs[i].d = 0xc1 & 0x40ff; i++;
  init_regs[i].r = device_control; init_regs[i].d = 0xc1; i++;
  init_regs[i].r = interrupt_mask; init_regs[i].d = 0xffff; i++;

  if (0) {  // DEBUG CODE
    doc["result"]["len_adc"] = adc_len;
    doc["result"]["len_dac"] = dac_len;
    doc["result"]["len_gpo"] = gpo_len;
    doc["result"]["len_gpi"] = gpi_len;
    doc["result"]["gpo_mv"] = gpo_mv;
    doc["result"]["gpi_mv"] = gpi_mv;
    doc["result"]["i"] = i;  //  !! check i < MAX_INIT_SETTINGS !! 
    return _response(doc);
  }

  uint8_t cs_pin = _get_max_cs_from_hdr(hdr);
  max->begin(SPI_MOSI_Pin, SPI_MISO_Pin, SPI_SCLK_Pin, cs_pin, MAX11311_CONVERT_Pin);
  for(unsigned int k = 0; k < i; k++) {
    if (init_regs[k].r != reserved_6A) {  // reserved_6a is flag for just delay
      max->write_register(init_regs[k].r, init_regs[k].d);
    }
    delay(1);
  }

  doc["result"]["regs_seq_len"] = i;

  oled_print(OLED_LINE_RPC, __func__, !doc["success"]);
  return _response(doc);  // always the last line of RPC API
}

/* Calibrate Battery Emulator
 */
String bond_batt_emu_cal(void) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API

  int rc = battemu_init();
  if (rc) {
    doc["success"] = false;
    doc["result"]["error"] = "battemu_init";
  }

  oled_print(OLED_LINE_RPC, __func__, !doc["success"]);
  return _response(doc);  // always the last line of RPC API
}  

/* Read Header <1-4> ADC Port 11 cal voltage
 * - all MAX11311's Port 11 is connected to 2500mV voltage reference
 */
String bond_max_hdr_adc_cal(int hdr) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API

  MAX11300 *max = _get_max_from_hdr(hdr);
  if (max == NULL) {
    doc["result"]["error"] = "1 <= hdr <= 4, invalid parameter";
    doc["success"] = false;
    return _response(doc);
  }  
  
  uint16_t data = 0;
  MAX11300::CmdResult result = max->single_ended_adc_read(MAX11300::PIXI_PORT11, &data);
  if (result != MAX11300::Success) {
    doc["result"]["error"] = "single_ended_adc_read error";
    doc["success"] = false;
    return _response(doc);    
  }

  doc["result"]["mV"] = (data * 10000 + 2048) / 4096  ;  // raw * 10000mV / 4096

  oled_print(OLED_LINE_RPC, __func__, !doc["success"]);
  return _response(doc);  // always the last line of RPC API
}

/* Read Header <1-4> ADC Port <#> cal voltage
 * - its assume the port mode was checked by the Python side code
 */
String bond_max_hdr_adc(int hdr, int port) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API

  MAX11300 *max = _get_max_from_hdr(hdr);
  if (max == NULL) {
    doc["result"]["error"] = "1 <= hdr <= 4, invalid parameter";
    doc["success"] = false;
    return _response(doc);
  }  

  uint16_t data = 0;
  MAX11300::CmdResult result = max->single_ended_adc_read(_get_port_from_int(port), &data);
  if (result != MAX11300::Success) {
    doc["result"]["error"] = "single_ended_adc_read error";
    doc["success"] = false;
    return _response(doc);    
  }

  doc["result"]["mV"] = ((uint32_t)data * 10000 + 2048) / 4096;  // raw * 10000mV / 4096

  oled_print(OLED_LINE_RPC, __func__, !doc["success"]);
  return _response(doc);  // always the last line of RPC API
}

/* Write Header <1-4> DAC Port <#> cal voltage
 * - its assume the port mode was checked by the Python side code
 */
String bond_max_hdr_dac(int hdr, int port, int mv) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API

  MAX11300 *max = _get_max_from_hdr(hdr);
  if (max == NULL) {
    doc["result"]["error"] = "1 <= hdr <= 4, invalid parameter";
    doc["success"] = false;
    return _response(doc);
  }  
  if (mv < 0 || mv > 10000) {
    doc["result"]["error"] = "0 <= mv <= 10000, invalid parameter";
    doc["success"] = false;
    return _response(doc);    
  }

  float _data = mv * 4096 / 10000;
  uint16_t data = (uint16_t)_data & 0xFFFF;  // 10000mV range over 4096
  max->write_register(_reg_dac_data_port(port), data);

  doc["result"]["dac_raw"] = data;
  doc["result"]["mV"] = mv;

  oled_print(OLED_LINE_RPC, __func__, !doc["success"]);
  return _response(doc);  // always the last line of RPC API
}

int init_max_hdr_bist(void) {
  /* Each MAX11311 on a header has port 11 mapped as an ADC which is
     Connected to BOND's Vref (2.5V).  On power up, setup() will init
     all headers with PORT 11 mapped as ADC and this voltage is checked.
  */
  unsigned int hdr = 0;

  char buf[LINE_MAX_LENGTH];

  // configure all the MAX11311s
  for(hdr = 1; hdr < 5; hdr++) {
      MAX11300 *max = _get_max_from_hdr(hdr);
      uint8_t cs_pin = _get_max_cs_from_hdr(hdr);

      max->begin(SPI_MOSI_Pin, SPI_MISO_Pin, SPI_SCLK_Pin, cs_pin, MAX11311_CONVERT_Pin);

      // read device_control to see if writing worked, else return error
      uint16_t _dev_id = max->read_register(dev_id);
      if (_dev_id != 0x424) {  // see datasheet for expected result value
        snprintf(buf, LINE_MAX_LENGTH, "init_max_hdr %u:id %x", hdr, _dev_id);
        oled_print(OLED_LINE_DEBUG, buf, true);
        return -1;
      }

      // NOTE: Tried to use the output of the MAX11311 config tool to set MAX11311
      //       but it did NOT WORK.  Switched to this method, using bond_max_hdr_init()
      //       and this did work.
      int adcs[] = {11}; int adc_len = 1;
      int dacs[] = {0}; int dac_len = 0;
      int gpos[] = {0}; int gpo_len = 0;
      int gpis[] = {0}; int gpi_len = 0;
      int gpo_mv = 3300;
      int gpi_mv = 0;

      bond_max_hdr_init(hdr, adcs, adc_len, dacs, dac_len, gpos, gpo_len, gpis, gpi_len, gpo_mv, gpi_mv);
      snprintf(buf, LINE_MAX_LENGTH, "hdr %u", hdr);
      oled_print(OLED_LINE_DEBUG, buf, false);
  }

  // measure PORT11 voltage on all MAX11311a
  for(hdr = 1; hdr < 5; hdr++) {
      MAX11300 *max = _get_max_from_hdr(hdr);
      uint16_t data = 0;
      MAX11300::CmdResult result = max->single_ended_adc_read(MAX11300::PIXI_PORT11, &data);
      if (result != MAX11300::Success) {
        snprintf(buf, LINE_MAX_LENGTH, "init_max_hdr:adc %u", data);
        oled_print(OLED_LINE_DEBUG, buf, true);
        return -1;
      }

      uint32_t mv = ((uint32_t)data * 10000 + 2048) / 4096;  // raw * 10000mV / 4096
      snprintf(buf, LINE_MAX_LENGTH, "hdr %u %u %u mV", hdr, data, mv);

      if (mv > (BIST_VREF_MV + BIST_VREF_TOL_MV) || mv < (BIST_VREF_MV - BIST_VREF_TOL_MV)) {
        oled_print(OLED_LINE_DEBUG, buf, true);
        return -1;
      }
      oled_print(OLED_LINE_DEBUG, buf, false);
      delay(100); // just to see display
  }

  oled_print(OLED_LINE_RPC, __func__, false);
  return 0;
}
