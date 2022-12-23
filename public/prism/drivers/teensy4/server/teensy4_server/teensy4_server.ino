/*  Sistemi Corporation, copyright, all rights reserved, 2021-2022
 *  Owen Li, Martin Guthrie
 *  
 *  Notes:
 *  1) functions begining with "_" are considered "private" and should not
 *     be called thru the RPC API.  These are "supporting" functions.
*/

#include <simpleRPC.h>
#include <ArduinoJson.h>
#include "version.h"


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

String unique_id() {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  
  char unique_id[MAX_STR_SIZE];
  doc["result"]["unique_id"] = _teensyMAC(unique_id);
  
  return _response(doc);  // always the last line of RPC API
}

String slot() {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API

  // slot id will be based on MAC address last 2 bytes
  uint32_t m2 = HW_OCOTP_MAC0;
  uint32_t _id = m2 & 0xffff;
  doc["result"]["id"] = _id;
  
  return _response(doc);  // always the last line of RPC API
}

String set_led(bool on) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  
  if (on){
    doc["result"]["state"] = "on";
    if (digitalRead(LED_BUILTIN) == LOW){
      digitalWrite(LED_BUILTIN, HIGH);
    }
  }
  else{
    doc["result"]["state"] = "off";
    if (digitalRead(LED_BUILTIN) == HIGH){
      digitalWrite(LED_BUILTIN, LOW);
    }
  }
  
  return _response(doc);  // always the last line of RPC API
}

String reboot_to_bootloader() {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  // send reboot command ----- from https://forum.pjrc.com/threads/71624-teensy_loader_cli-with-multiple-Teensys-connected?p=316838#post316838
  _reboot_Teensyduino_();
  return _response(doc);  // this never happens because of reboot call
}

String version(){
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
 
  doc["result"]["version"] = VERSION;
  
  return _response(doc);  // always the last line of RPC API
}

String read_adc(int pin_number, int sample_num, unsigned int sample_rate){
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API

  unsigned long currentMillis = millis();
  unsigned long previousMillis = 0;
  double reading = 0;

  for(int count = 0; count <= sample_num; count++){
    if((currentMillis - previousMillis) >= sample_rate){
      reading += analogRead(pin_number);
      previousMillis = currentMillis;
    }
  }

  reading = reading/sample_num;
  doc["result"]["reading"] = reading;

  return _response(doc);  // always the last line of RPC API
}

String init_gpio(int pin_number, String& mode){
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  
  if(mode == "INPUT"){
    pinMode(pin_number, INPUT);
  }
  else if(mode == "OUTPUT"){
    pinMode(pin_number, OUTPUT);
  }
  else if(mode == "INPUT_PULLUP"){
    pinMode(pin_number, INPUT_PULLUP);
  }
  doc["result"]["mode"] = mode;
 
  return _response(doc);  // always the last line of RPC API
}

String read_gpio(int pin_number){
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API

  doc["result"]["state"] = digitalRead(pin_number);

  return _response(doc);  // always the last line of RPC API
}

String write_gpio(int pin_number, bool state){
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API

  digitalWrite(pin_number, state);

  doc["result"]["state"] = state;

  return _response(doc);  // always the last line of RPC API
}

String reset(){
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API

  // ... add any required resetting code here ...
  
  return _response(doc);  // always the last line of RPC API
}


//-------------------------------------------------------------------------------------------------------------
//set-up/loop Functions

void setup(void) {
  Serial.begin(9600);
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop(void) {

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
    reset, "reset: Resets Teensy.");
}
