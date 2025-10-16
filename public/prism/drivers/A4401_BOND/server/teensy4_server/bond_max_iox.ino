/*  Sistemi Corporation, copyright, all rights reserved, 2023
 *  Martin Guthrie
 *  
 *  MAX11311 IOX (IO Expander)
 *  See: https://github.com/MaximIntegratedRefDesTeam/MAX11300
 *  Clone and view docs in "extras", although missing examples
*/
#include "bond_max_hdr.h"
#include "src/oled/bond_oled.h"

// default IOX MAX11311 resisters, set on init
// this array is pulling from init code that auto generated from
// MAX11300/01/11/12 Configuration Software (Ver. 1.1.0.5) 16/10/2025 17:41
// The file a4402-MAX11300Design_iox_01.mpix is the source file for the tool.
// Then generate the header file, and then pull out the programming sequence.
static _init_regs_t init_regs[] = {
  {.r = device_control, .d = 0x8000}, // reset
  {.r = device_control, .d = 0xc0 & 0x40b0},
  {.r = device_control, .d = 0xc0 & 0x40fc},
  {.r = dac_data_port_p2, .d = 0x0547}, // GPO VBAT_CON
  {.r = dac_data_port_p3, .d = 0x0547}, // GPO VBAT_EN
  {.r = dac_data_port_p7, .d = 0x0547}, // GPO SELFTEST
  {.r = dac_data_port_p8, .d = 0x0547}, // GPO LED GREEN
  {.r = dac_data_port_p9, .d = 0x0547}, // GPO LED YELLOW
  {.r = dac_data_port_p10,.d = 0x0547}, // GPO LED RED
  {.r = dac_data_port_p11,.d = 0x0547}, // GPO LED BLUE
  {.r = dac_data_port_p4, .d = 0x019a}, // DAC VBAT_ADJ
  {.r = dac_data_port_p5, .d = 0x019a}, // DAC HDR1 LDO ADJ
  {.r = dac_preset_data_1, .d = 0x0}, 
  {.r = dac_preset_data_2, .d = 0x0},
  {.r = gpo_data_P10P6_P5P0, .d = 0x0},
  {.r = gpo_data_P11, .d = 0x0},
  {.r = port_cfg_p2, .d = 0x3000},
  {.r = port_cfg_p3, .d = 0x3000},
  {.r = port_cfg_p7, .d = 0x3000},
  {.r = port_cfg_p8, .d = 0x3000},
  {.r = port_cfg_p9, .d = 0x3000},
  {.r = port_cfg_p10, .d = 0x3000},
  {.r = port_cfg_p11, .d = 0x3000},
  {.r = port_cfg_p4, .d = 0x5100},
  {.r = port_cfg_p5, .d = 0x5100},
  {.r = gpi_irqmode_P5_P0, .d = 0x0},
  {.r = gpi_irqmode_P10_P6, .d = 0x0},
  {.r = gpi_irqmode_P11, .d = 0x0},
  {.r = device_control, .d = 0xc0},
  {.r = interrupt_mask, .d = 0xffff},
};

int init_max_iox(void) {
  /* MAX11311 init register values comes from the MAX11300 Configuration
     Tool (ver 1.1.0.5).
     The Datasheet (DS) has specific flowchat as to how the registers
     are programmed, and the time delay between writes.
     The Configuration tool generates code to program the registers,
     values, sequence, and delay.  That is used here as a template.
  */
  unsigned int i = 0;
  char buf[LINE_MAX_LENGTH];

  max_iox.begin(SPI_MOSI_Pin, SPI_MISO_Pin, SPI_SCLK_Pin, SPI_CS_IOX_Pin, MAX11311_CONVERT_Pin);

  // read device_control to see if writing worked, else return error
  uint16_t _dev_id = max_iox.read_register(dev_id);
  if (_dev_id != 0x424) {  // see datasheet for expected result value
    snprintf(buf, LINE_MAX_LENGTH, "init_max_iox:id %x", _dev_id);
    oled_print(OLED_LINE_RPC, buf, true);
    return -1;
  }

  for (i = 0; i < sizeof(init_regs) / sizeof(_init_regs_t); i++) {
    max_iox.write_register(init_regs[i].r, init_regs[i].d);
    delay(1);
    snprintf(buf, LINE_MAX_LENGTH, "init_max_iox:%02x %04x", init_regs[i].r, init_regs[i].d);
    oled_print(OLED_LINE_RPC, buf, false);
  }

  oled_print(OLED_LINE_RPC, __func__, false);
  return 0;
}

/* iox_reset
 *  - set reset pin, which is active (asserted) LOW
 *  - RESETb only affects USB, so this should probably never get called
 */
String iox_reset(bool assert) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  max_iox.gpio_write(MAX11300::PIXI_PORT6, (!assert ? 1 : 0));
  doc["result"]["assert"] = assert;
  doc["result"]["level"] = !assert;    

  oled_print(OLED_LINE_RPC, __func__, false);
  return _response(doc);  // always the last line of RPC API
}

/* iox_vbat_con
 *  - set VBAT_CON pin, which is active (asserted) HIGH
 */
String iox_vbat_con(bool assert) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  max_iox.gpio_write(MAX11300::PIXI_PORT2, (assert ? 1 : 0));
  doc["result"]["assert"] = assert;
  doc["result"]["level"] = assert;  

  oled_print(OLED_LINE_RPC, __func__, false);
  return _response(doc);  // always the last line of RPC API
}

/* iox_vbat_en
 *  - set VBAT_EN pin, which is active (asserted) HIGH
 */
String iox_vbat_en(bool assert) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  max_iox.gpio_write(MAX11300::PIXI_PORT3, (assert ? 1 : 0));
  doc["result"]["assert"] = assert;
  doc["result"]["level"] = assert;  

  oled_print(OLED_LINE_RPC, __func__, false);
  return _response(doc);  // always the last line of RPC API
}

/* iox_selftest
 *  - set SELFTEST pin, which is active (asserted) HIGH
 */
String iox_selftest(bool assert) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  max_iox.gpio_write(MAX11300::PIXI_PORT7, (assert ? 1 : 0));
  doc["result"]["assert"] = assert;
  doc["result"]["level"] = assert;

  oled_print(OLED_LINE_RPC, __func__, false);
  return _response(doc);  // always the last line of RPC API
}

/* iox_led_green
 *  - set green LED high/low
 */
String iox_led_green(bool assert) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  max_iox.gpio_write(MAX11300::PIXI_PORT8, (assert ? 1 : 0));
  doc["result"]["assert"] = assert;
  doc["result"]["level"] = assert;

  oled_print(OLED_LINE_RPC, __func__, false);
  return _response(doc);  // always the last line of RPC API
}

/* iox_led_yellow
 *  - set yellow LED high/low
 */
String iox_led_yellow(bool assert) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  max_iox.gpio_write(MAX11300::PIXI_PORT9, (assert ? 1 : 0));
  doc["result"]["assert"] = assert;
  doc["result"]["level"] = assert;

  oled_print(OLED_LINE_RPC, __func__, false);
  return _response(doc);  // always the last line of RPC API
}

/* iox_led_red
 *  - set red LED high/low
 */
String iox_led_red(bool assert) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  max_iox.gpio_write(MAX11300::PIXI_PORT10, (assert ? 1 : 0));
  doc["result"]["assert"] = assert;
  doc["result"]["level"] = assert;

  oled_print(OLED_LINE_RPC, __func__, false);
  return _response(doc);  // always the last line of RPC API
}

/* iox_led_blue
 *  - set blue LED high/low
 */
String iox_led_blue(bool assert) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  max_iox.gpio_write(MAX11300::PIXI_PORT11, (assert ? 1 : 0));
  doc["result"]["assert"] = assert;
  doc["result"]["level"] = assert;

  oled_print(OLED_LINE_RPC, __func__, false);
  return _response(doc);  // always the last line of RPC API
}