/*  Sistemi Corporation, copyright, all rights reserved, 2021-2026
 *  Owen Li, Martin Guthrie
 *
 *  Teensy 4.1 simpleRPC server, a starting point for a test jig controller.
 *
 *  Adding an RPC: write it here (see rpc_helpers.h for the shape), and add it to
 *  interface() in loop(). An RPC function must never call another RPC function.
 */
#include <simpleRPC.h>
#include "version.h"  // holds the "version" of this code, !update when code is changed!
#include "rpc_helpers.h"

#define MAC_STR_SIZE          18    // "xx:xx:xx:xx:xx:xx" + null
#define GPIO_NUMBER_MAX       41
#define READ_ADC_SAMPLES_MAX  1000

//-------------------------------------------------------------------------------------------------------------
// Teensy "on board" RPC functions
// - use this area to create RPC API functions for APIs that directly use (onboard) the Teensy (module)

/* unique_id
 *  - return the Teensy's MAC address as the unique identifier
 */
String unique_id(void) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API

  uint32_t m1 = HW_OCOTP_MAC1;
  uint32_t m2 = HW_OCOTP_MAC0;
  char mac[MAC_STR_SIZE];
  snprintf(mac, sizeof(mac), "%02lx:%02lx:%02lx:%02lx:%02lx:%02lx",
           (m1 >> 8) & 0xff, m1 & 0xff, (m2 >> 24) & 0xff, (m2 >> 16) & 0xff,
           (m2 >> 8) & 0xff, m2 & 0xff);
  doc["result"]["unique_id"] = mac;
  return rpc_response(doc);  // always the last line of RPC API
}

/* slot
 *  - DEPRECATED (mostly), Prism orders Teensys by USB path
 *  - returns the last 2 bytes of the MAC address
 */
String slot(void) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API
  doc["result"]["id"] = HW_OCOTP_MAC0 & 0xffff;
  return rpc_response(doc);  // always the last line of RPC API
}

/* set_led
 *  - Teensy module LED on or off
 */
String set_led(bool on) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API
  digitalWrite(LED_BUILTIN, on ? HIGH : LOW);
  doc["result"]["state"] = on ? "on" : "off";
  return rpc_response(doc);  // always the last line of RPC API
}

/* reboot_to_bootloader
 *  - jump to the bootloader for reprogramming with teensy_loader_cli
 *  - does not return, the Python side fakes the response
 *    see https://forum.pjrc.com/threads/71624-teensy_loader_cli-with-multiple-Teensys-connected?p=316838#post316838
 */
String reboot_to_bootloader(void) {
  _reboot_Teensyduino_();
}

String version(void) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API
  doc["result"]["version"] = VERSION;
  return rpc_response(doc);  // always the last line of RPC API
}

/* read_adc
 *  - average of sample_num ADC readings on a Teensy pin, sample_rate ms apart
 */
String read_adc(unsigned int pin_number, unsigned int sample_num, unsigned int sample_rate) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API

  if (pin_number > GPIO_NUMBER_MAX) return rpc_error(doc, "0 <= pin <= 41, invalid parameter");
  if (sample_num < 1 || sample_num > READ_ADC_SAMPLES_MAX) {
    return rpc_error(doc, "1 <= sample_num <= 1000, invalid parameter");
  }

  uint32_t accumulator = 0;
  for (unsigned int i = 0; i < sample_num; i++) {
    if (i) delay(sample_rate);
    accumulator += analogRead(pin_number);
  }
  doc["result"]["reading"] = accumulator / sample_num;
  return rpc_response(doc);  // always the last line of RPC API
}

/* init_gpio
 *  - mode: <"INPUT"|"OUTPUT"|"INPUT_PULLUP">
 */
String init_gpio(int pin_number, String &mode) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API

  if (pin_number < 0 || pin_number > GPIO_NUMBER_MAX) {
    return rpc_error(doc, "0 <= pin <= 41, invalid parameter");
  }
  if (mode == "INPUT") pinMode(pin_number, INPUT);
  else if (mode == "OUTPUT") pinMode(pin_number, OUTPUT);
  else if (mode == "INPUT_PULLUP") pinMode(pin_number, INPUT_PULLUP);
  else return rpc_error(doc, "invalid mode");

  doc["result"]["mode"] = mode;
  return rpc_response(doc);  // always the last line of RPC API
}

String read_gpio(int pin_number) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API
  if (pin_number < 0 || pin_number > GPIO_NUMBER_MAX) {
    return rpc_error(doc, "0 <= pin <= 41, invalid parameter");
  }
  doc["result"]["state"] = digitalRead(pin_number);
  return rpc_response(doc);  // always the last line of RPC API
}

String write_gpio(int pin_number, bool state) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API
  if (pin_number < 0 || pin_number > GPIO_NUMBER_MAX) {
    return rpc_error(doc, "0 <= pin <= 41, invalid parameter");
  }
  digitalWrite(pin_number, state);
  doc["result"]["state"] = state;
  return rpc_response(doc);  // always the last line of RPC API
}

/* reset
 *  - set the jig to a known state, called at the start and end of each test
 *  - DOES NOT RESET TEENSY
 */
String reset(void) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API

  // ... add any required resetting code here ...

  return rpc_response(doc);  // always the last line of RPC API
}

//-------------------------------------------------------------------------------------------------------------
//set-up/loop Functions

void setup(void) {
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);

  // add hardware specific setup here
}

void loop(void) {
  // interface() is non-blocking
  // NOTE: !! the function name and description string beginning must match !!
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
    reset, "reset: Set the jig to a known state (not a Teensy reset).");
}
