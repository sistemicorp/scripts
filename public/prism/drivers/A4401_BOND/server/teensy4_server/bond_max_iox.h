/*  Sistemi Corporation, copyright, all rights reserved, 2023
 *  Martin Guthrie
 *  
 *  MAX11311 IOX (IO Expander)
 *  See: https://github.com/MaximIntegratedRefDesTeam/MAX11300
 *  Clone and view docs in "extras", although missing examples
*/

int init_max_iox(void);
String iox_led_blue(bool assert);
String iox_led_red(bool assert);
String iox_led_yellow(bool assert);
String iox_led_green(bool assert);
String iox_selftest(bool assert);
String iox_vbat_en(bool assert);
String iox_vbat_con(bool assert);

