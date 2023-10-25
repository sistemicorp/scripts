/*  Sistemi Corporation, copyright, all rights reserved, 2023
 *  Martin Guthrie
 *  
 *  MAX11311 IOX (IO Expander)
 *  See: https://github.com/MaximIntegratedRefDesTeam/MAX11300
 *  Clone and view docs in "extras", although missing examples
*/


/* vbus_read
 *  - return INA bus voltage and current
 */
String iox_read() {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  
  doc["result"]["id"] = max_iox.read_register(dev_id);

  return _response(doc);  // always the last line of RPC API
}


