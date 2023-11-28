/*  Sistemi Corporation, copyright, all rights reserved, 2023
 *  Martin Guthrie
 *  
 *  MAX11311 IOX (IO Expander)
 *  See: https://github.com/MaximIntegratedRefDesTeam/MAX11300
 *  Clone and view docs in "extras", although missing examples
*/
#include "bond_max_hdr.h"
#include "src/oled/bond_oled.h"

static _init_regs_t init_regs[] = {
  {.r = device_control, .d = 0x8000}, // reset
  {.r = device_control, .d = 0xc0 & 0x40b0},
  {.r = device_control, .d = 0xc0 & 0x40fc},
  {.r = dac_data_port_01, .d = 0x0666}, // VBUS_FAULT input, threshold 1V
  {.r = dac_data_port_05, .d = 0x0666}, // VBUS_PG input, threshold 1V
  {.r = dac_data_port_00, .d = 0x0547}, // VBUS_SWEN output, 3.3V
  {.r = dac_data_port_02, .d = 0x0547}, // VBAT_CON output, 3.3V
  {.r = dac_data_port_03, .d = 0x0547}, // VBAT_EN output, 3.3V
  {.r = dac_data_port_04, .d = 0x0547}, // VBUS_EN output, 3.3V
  {.r = dac_data_port_06, .d = 0x0547}, // RESETb (active LOW) output, 3.3V
  {.r = dac_data_port_07, .d = 0x0547}, // SELFTEST output, 3.3V
  {.r = dac_data_port_08, .d = 0x0547}, // GREEN output, 3.3V
  {.r = dac_data_port_09, .d = 0x0547}, // YELLOW output, 3.3V
  {.r = dac_data_port_10, .d = 0x0547}, // RED output, 3.3V
  {.r = dac_data_port_11, .d = 0x0547}, // BLUE output, 3.3V
  {.r = dac_preset_data_1, .d = 0x0}, 
  {.r = dac_preset_data_2, .d = 0x0}, 
  {.r = port_cfg_01, .d = (MAX11300::MODE_1 << 12)}, 
  {.r = port_cfg_05, .d = (MAX11300::MODE_1 << 12)}, 
  {.r = gpo_data_10_to_0, .d = 0x0}, 
  {.r = gpo_data_11, .d = 0x0}, 
  {.r = port_cfg_00, .d = (MAX11300::MODE_3 << 12)}, 
  {.r = port_cfg_02, .d = (MAX11300::MODE_3 << 12)}, 
  {.r = port_cfg_03, .d = (MAX11300::MODE_3 << 12)}, 
  {.r = port_cfg_04, .d = (MAX11300::MODE_3 << 12)}, 
  {.r = port_cfg_06, .d = (MAX11300::MODE_3 << 12)}, 
  {.r = port_cfg_07, .d = (MAX11300::MODE_3 << 12)}, 
  {.r = port_cfg_08, .d = (MAX11300::MODE_3 << 12)}, 
  {.r = port_cfg_09, .d = (MAX11300::MODE_3 << 12)}, 
  {.r = port_cfg_10, .d = (MAX11300::MODE_3 << 12)}, 
  {.r = port_cfg_11, .d = (MAX11300::MODE_3 << 12)}, 
  {.r = gpi_irqmode_5_to_0, .d = 0x0}, 
  {.r = gpi_irqmode_10_to_6, .d = 0x0}, 
  {.r = gpi_irqmode_11, .d = 0x0},   
  {.r = device_control, .d = 0xc0},  // data val used to confirm in init 
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

  max_iox.begin(SPI_MOSI_Pin, SPI_MISO_Pin, SPI_SCLK_Pin, SPI_CS_IOX_Pin, MAX11311_COPNVERT_Pin); 

  for (i = 0; i < sizeof(init_regs) / sizeof(_init_regs_t); i++) {
    max_iox.write_register(init_regs[i].r, init_regs[i].d);
    delay(1);
  }
  // read device_control to see if writing worked, else return error
  uint16_t _device_control = max_iox.read_register(device_control);
  if (_device_control != 0xc0) {
    return -1;
  }

  // toggle RESETb to USB
  max_iox.gpio_write(MAX11300::PIXI_PORT6, 0);
  delay(5);
  max_iox.gpio_write(MAX11300::PIXI_PORT6, 1);

  // flash all LEDs
  max_iox.gpio_write(MAX11300::PIXI_PORT8, 1);
  max_iox.gpio_write(MAX11300::PIXI_PORT9, 1);
  max_iox.gpio_write(MAX11300::PIXI_PORT10, 1);
  max_iox.gpio_write(MAX11300::PIXI_PORT11, 1);
  delay(100);
  max_iox.gpio_write(MAX11300::PIXI_PORT8, 0);
  max_iox.gpio_write(MAX11300::PIXI_PORT9, 0);
  max_iox.gpio_write(MAX11300::PIXI_PORT10, 0);
  max_iox.gpio_write(MAX11300::PIXI_PORT11, 0);

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

/* iox_vbus_en
 *  - set VBUS_EN pin, which is active (asserted) HIGH
 */
String iox_vbus_en(bool assert) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  max_iox.gpio_write(MAX11300::PIXI_PORT4, (assert ? 1 : 0));
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