/*  Sistemi Corporation, copyright, all rights reserved, 2023
 *  Martin Guthrie
 *  
 *  INA220 for VBUS and VBAT
*/


/* vbus_read
 *  - return INA bus voltage and current
 */
String vbus_read() {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  
  doc["result"]["v"] = ina219_vbus.getBusVoltage_V();
  doc["result"]["ima"] = ina219_vbus.getCurrent_mA();

  return _response(doc);  // always the last line of RPC API
}

/* vbat_read
 *  - return INA bus voltage and current
 */
String vbat_read() {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  
  doc["result"]["v"] = ina219_vbat.getBusVoltage_V();
  doc["result"]["ima"] = ina219_vbat.getCurrent_mA();

  return _response(doc);  // always the last line of RPC API
}
