/*  Sistemi Corporation, copyright, all rights reserved, 2023
 *  Martin Guthrie
 *  
 *  MAX11311 IOX (IO Expander)
 *  See: https://github.com/MaximIntegratedRefDesTeam/MAX11300
 *  Clone and view docs in "extras", although missing examples
*/


/* iox_reset
 *  - set reset pin, which is active (asserted) LOW
 */
String iox_reset(bool assert) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  max_iox.gpio_write(MAX11300::PIXI_PORT6, (!assert ? 1 : 0));
  return _response(doc);  // always the last line of RPC API
}

/* iox_vbat_con
 *  - set VBAT_CON pin, which is active (asserted) HIGH
 */
String iox_vbat_con(bool assert) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  max_iox.gpio_write(MAX11300::PIXI_PORT2, (assert ? 1 : 0));
  return _response(doc);  // always the last line of RPC API
}

/* iox_vbat_en
 *  - set VBAT_EN pin, which is active (asserted) HIGH
 */
String iox_vbat_en(bool assert) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  max_iox.gpio_write(MAX11300::PIXI_PORT3, (assert ? 1 : 0));
  return _response(doc);  // always the last line of RPC API
}

/* iox_vbus_en
 *  - set VBUS_EN pin, which is active (asserted) HIGH
 */
String iox_vbus_en(bool assert) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  max_iox.gpio_write(MAX11300::PIXI_PORT4, (assert ? 1 : 0));
  return _response(doc);  // always the last line of RPC API
}

/* iox_selftest
 *  - set SELFTEST pin, which is active (asserted) HIGH
 */
String iox_selftest(bool assert) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  max_iox.gpio_write(MAX11300::PIXI_PORT7, (assert ? 1 : 0));
  return _response(doc);  // always the last line of RPC API
}

/* iox_led_green
 *  - set green LED high/low
 */
String iox_led_green(bool assert) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  int success = max_iox.gpio_write(MAX11300::PIXI_PORT8, (assert ? 1 : 0));
  //doc["success"] = success;
  doc["result"]["set"] = (assert ? true : false);
  doc["result"]["port"] = MAX11300::PIXI_PORT8;

  //max_iox.write_register(gpo_data_10_to_0, 0x1 << 13);
  //max_iox.write_register(gpo_data_10_to_0, 0xf8fc);

  //max_iox.write_register(dac_preset_data_1, 0x123);
  uint16_t test = max_iox.read_register(port_cfg_08);
  doc["result"]["port_cfg_08"] = test;
  test = max_iox.read_register(gpo_data_10_to_0);
  doc["result"]["gpo_data_10_to_0"] = test;
  test = max_iox.read_register(dac_data_port_08);
  doc["result"]["dac_data_port_08"] = test;


  return _response(doc);  // always the last line of RPC API
}

