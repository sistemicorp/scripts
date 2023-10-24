/*  Sistemi Corporation, copyright, all rights reserved, 2021-2023
 *  Martin Guthrie
 *  
 *  Dedicated functions for the BOND design, a4401. 
 *
 *  Notes:
 *  1) functions begining with "_" are considered "private" and should not
 *     be called thru the RPC API.  These are "supporting" functions.
*/
#include <Wire.h>
#include <simpleRPC.h>
#include <ArduinoJson.h>
#include "version.h"  // holds the "version" of this code, !update when code is changed!
#include <INA219_WE.h>
#define INA220_VBAT_I2C_ADDRESS 0x40
#define INA220_VBUS_I2C_ADDRESS 0x41

#define VSYS_EN_PIN             41
#define VSYS_PG_PIN             40

#define BIST_VOLTAGE_V3V3A_PIN  23
#define BIST_VOLTAGE_V3V3D_PIN  22
#define BIST_VOLTAGE_V5V_PIN    25
#define BIST_VOLTAGE_V6V_PIN    24

INA219_WE ina219_vbat = INA219_WE(INA220_VBAT_I2C_ADDRESS);
INA219_WE ina219_vbus = INA219_WE(INA220_VBAT_I2C_ADDRESS);

//-------------------------------------------------------------------------------------------------------------
// Teensy "on board" RPC functions
// - use this area to create RPC API functions for APIs that directly use (onboard) the Teensy (module)

/* _teensyMAC
 * - return the Teensy's MAC address as a string
 * 
 * char *unique_id : ptr to string buffer (must be of length MAX_STR_SIZE)
 */
#define MAC_SIZE 6
#define MAX_STR_SIZE 18  // remember to leave space for null terminator
String _teensyMAC(char *unique_id){
    uint32_t m1 = HW_OCOTP_MAC1;
    uint32_t m2 = HW_OCOTP_MAC0;
    uint8_t mac[MAC_SIZE];
    mac[0] = m1 >> 8;
    mac[1] = m1 >> 0;
    mac[2] = m2 >> 24;
    mac[3] = m2 >> 16;
    mac[4] = m2 >> 8;
    mac[5] = m2 >> 0;
    snprintf(unique_id, MAX_STR_SIZE, "%02x:%02x:%02x:%02x:%02x:%02x", mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    return unique_id;
}
/* unique_id
 *  - return MAC address as the uniqie identifier
 */
String unique_id() {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  
  char unique_id[MAX_STR_SIZE];
  doc["result"]["unique_id"] = _teensyMAC(unique_id);
  
  return _response(doc);  // always the last line of RPC API
}

/* reboot_to_bootloader
 *  - software reset Teensy to jump to bootloader for reprogramming
 *  - this function does not really return because Teensy has been "reset",
 *    in the Python Teensy class, the return has been "faked".
 */
String reboot_to_bootloader() {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  // send reboot command ----- from https://forum.pjrc.com/threads/71624-teensy_loader_cli-with-multiple-Teensys-connected?p=316838#post316838
  _reboot_Teensyduino_();
  return _response(doc);  // this never happens because of reboot call
}

/* version
 *  - return the version of this code
 */
String version(){
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
 
  doc["result"]["version"] = VERSION;
  
  return _response(doc);  // always the last line of RPC API
}

/* slot
 *  - DEPRICATED (mostly)
 *  - return the "slot number" or channel number of the test jig so that Prism
 *    can assign it.
 *  - Teensy's discovery is based on the USB (physical) tree, so this is not used to discover
 *    attached Teensys and map the slot number
 *  - Prism sorts slot numbers, assinig the lowest to slot 0, and so on.  This
 *    function returned a partial of the MAC address, and Prism sorted slots
 *    based on that value.
 */
String slot() {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API

  // slot id will be based on MAC address last 2 bytes
  uint32_t m2 = HW_OCOTP_MAC0;
  uint32_t _id = m2 & 0xffff;
  doc["result"]["id"] = _id;
  
  return _response(doc);  // always the last line of RPC API
}

/* reset
 *  - reset this code
 *  - DOES NOT RESET TEENSY, meerly resets its "state"
 */
String reset(){
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API

  // ... add any required resetting code here ...
  
  return _response(doc);  // always the last line of RPC API
}


//-------------------------------------------------------------------------------------------------------------
//set-up/loop Functions

void setup(void) {
  bool all_good = true;
  unsigned int blink_delay_ms = 100;

  Serial.begin(115200);
  Wire.begin();
  pinMode(LED_BUILTIN, OUTPUT);

  // blink the LED to let people know we are good
  digitalWrite(LED_BUILTIN, HIGH);
  delay(blink_delay_ms);
  digitalWrite(LED_BUILTIN, LOW);
  delay(blink_delay_ms);
  digitalWrite(LED_BUILTIN, HIGH);
  delay(blink_delay_ms);
  digitalWrite(LED_BUILTIN, LOW);

  // set BOND pins
  pinMode(VSYS_EN_PIN, OUTPUT);
  pinMode(VSYS_PG_PIN, INPUT);

  // ADC
  pinMode(BIST_VOLTAGE_V3V3A_PIN, INPUT);  // analog input
  pinMode(BIST_VOLTAGE_V3V3D_PIN, INPUT);  // analog input
  pinMode(BIST_VOLTAGE_V5V_PIN, INPUT);    // analog input
  pinMode(BIST_VOLTAGE_V6V_PIN, INPUT);    // analog input

  // run tests here... blink LED if problem
  digitalWrite(VSYS_EN_PIN, HIGH);
  delay(100);
  // check VSYS_PG_PIN
  uint8_t vsys_pg_pin = digitalRead(VSYS_PG_PIN);
  if (vsys_pg_pin == 0) {
    all_good = false;
  }

  if (!ina219_vbat.init()) {
    all_good = false;
  }
  if (!ina219_vbus.init()) {
    all_good = false;
  }


  delay(blink_delay_ms);

  if (!all_good) {
    // long blinks if things are bad
    blink_delay_ms = 400;

    // shutdown for safety
    //digitalWrite(VSYS_EN_PIN, LOW);
  }
    
  // TODO: blink error code based on fault
  digitalWrite(LED_BUILTIN, HIGH);
  delay(blink_delay_ms);
  digitalWrite(LED_BUILTIN, LOW);
  delay(blink_delay_ms);
  digitalWrite(LED_BUILTIN, HIGH);
  delay(blink_delay_ms);
  digitalWrite(LED_BUILTIN, LOW);
  
}

void loop(void) {

  // interface() is non-blocking
  // NOTE: !! the function name and string begining must match !!
  interface(
    Serial,
    unique_id, "unique_id: Shows Teensy's unique id",
    slot, "slot: Shows the Teensy's slot to differentiate multiple Teensys",
    set_led, "set_led: Set LED (ON/OFF).",
    reboot_to_bootloader, "reboot_to_bootloader: Reboot Teensy to bootloader for FW update via teensy_loader_cli",
    version, "version: Shows current version.",
    read_adc, "read_adc: Reads analog pin.",
    init_gpio, "init_gpio: Initializes GPIO (INPUT, INPUT_PULLUP, OUTPUT).",
    read_gpio, "read_gpio: Reads GPIO (HIGH or LOW).",
    write_gpio, "write_gpio: Writes GPIO (HIGH or LOW).",
    reset, "reset: Resets Teensy.",

    bist_voltage, "bist_voltage: Reads internal voltage"
    );
}
