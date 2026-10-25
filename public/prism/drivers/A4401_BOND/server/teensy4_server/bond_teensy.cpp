/*  Sistemi Corporation, copyright, all rights reserved, 2021-2026
 *  Martin Guthrie
 *
 *  Teensy "on board" functions, see bond_teensy.h
 */
#include "bond_teensy.h"
#include "bond_board.h"
#include "bond_pins.h"
#include "rpc_helpers.h"
#include "version.h"

#define MAC_STR_SIZE         18  // "xx:xx:xx:xx:xx:xx" + null
#define READ_ADC_SAMPLES_MAX 1000
#define BIST_ADC_SAMPLES     10
#define BIST_ADC_RATE_MS     2

extern uint32_t external_psram_size;

static uint16_t setup_fail_code = 0;

const bist_voltage_t bist_voltages[] = {
  // Note this voltage appears when USB-PD is present at 15V
  // setup() will wait on this voltage before continuing, assuming
  // that the voltage has not yet been applied
  {.pin = BIST_VOLTAGE_V6V_PIN,    .mv = 6000, .name = "V6V"},
  {.pin = BIST_VOLTAGE_V3V3A_PIN,  .mv = 3300, .name = "V3V3A"},
  {.pin = BIST_VOLTAGE_V3V3D_PIN,  .mv = 3300, .name = "V3V3D"},
  {.pin = BIST_VOLTAGE_V5V_PIN,    .mv = 5000, .name = "V5V"},
  // A_VNEG2V5 is a divider from V3V3D (R132 5.1k) to VNEG2V5A (R89 10k), Teensy4 sheet,
  //   A = 3.3 + (VNEG - 3.3) * 5.1 / 15.1, read with the same * 3 math as the other rails.
  //   -2.5V reads 4023, the boards read ~4079 (-2.44V), in tolerance.
  {.pin = BIST_VOLTAGE_NEG2V5_PIN, .mv = 4079, .name = "V2V5NEG"},
};
const unsigned int bist_voltages_num = sizeof(bist_voltages) / sizeof(bist_voltage_t);

void set_setup_fail_code(uint16_t code) {
  setup_fail_code |= (0x1 << code);
}

unsigned int teensy_read_adc(unsigned int pin, unsigned int sample_num, unsigned int sample_rate_ms) {
  uint32_t accumulator = 0;
  for (unsigned int i = 0; i < sample_num; i++) {
    if (i) delay(sample_rate_ms);
    accumulator += analogRead(pin);
  }
  return sample_num ? (unsigned int)(accumulator / sample_num) : 0;
}

unsigned int bist_adc_to_mv(unsigned int adc_raw) {
  return (adc_raw * 3300 * 3) / 1024;  // * 3 for resistor divider, 10k / (10k + 20k)
}

/* mem_info
 *  - from https://forum.pjrc.com/index.php?threads/how-to-display-free-ram.33443/#post-284796
 */
void mem_info(uint32_t *stack, uint32_t *heap, uint32_t *psram) {
  extern char _ebss[], _heap_end[], _extram_start[], _extram_end[], *__brkval;

  auto sp = (char*) __builtin_frame_address(0);
  auto _stack = sp - _ebss;
  auto _heap = _heap_end - __brkval;
  auto _psram = _extram_start + (external_psram_size << 20) - _extram_end;

  *stack = _stack >> 10;
  *heap = _heap >> 10;
  *psram = _psram >> 10;
}

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
 *  - DEPRECATED (mostly), Prism orders BONDs by USB path
 *  - returns the last 2 bytes of the MAC address
 */
String slot(void) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API
  doc["result"]["id"] = HW_OCOTP_MAC0 & 0xffff;
  return rpc_response(doc);  // always the last line of RPC API
}

String version(void) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API
  doc["result"]["version"] = VERSION;
  return rpc_response(doc);  // always the last line of RPC API
}

/* status
 *  - setup() fail code (bit per SETUP_FAIL_*), and free memory
 */
String status(void) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API

  uint32_t stack = 0, heap = 0, psram = 0;
  mem_info(&stack, &heap, &psram);

  doc["result"]["setup_fail_code"] = setup_fail_code;
  doc["result"]["stack_kb"] = stack;
  doc["result"]["heap_kb"] = heap;
  doc["result"]["psram_kb"] = psram;
  return rpc_response(doc);  // always the last line of RPC API
}

String temperature(void) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API
  doc["result"]["temp_degC"] = tmp1075.getTemperatureCelsius();
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

/* set_led
 *  - Teensy module LED on or off
 */
String set_led(bool on) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API
  digitalWrite(LED_BUILTIN, on ? HIGH : LOW);
  doc["result"]["state"] = on ? "on" : "off";
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
  doc["result"]["reading"] = teensy_read_adc(pin_number, sample_num, sample_rate);
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
  JsonDocument &doc = rpc_begin(__func__, false);  // polled for jig closed, keep off display
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

/* bist_voltage
 *  - built in self-test (bist) read voltage
 *  - name: one of bist_voltages[].name, see schematic
 */
String bist_voltage(String name) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API
  doc["result"]["name"] = name;

  const bist_voltage_t *bv = NULL;
  for (unsigned int i = 0; i < bist_voltages_num; i++) {
    if (name == bist_voltages[i].name) bv = &bist_voltages[i];
  }
  if (bv == NULL) return rpc_error(doc, "Unknown name");

  unsigned int mv = bist_adc_to_mv(teensy_read_adc(bv->pin, BIST_ADC_SAMPLES, BIST_ADC_RATE_MS));
  doc["result"]["mv"] = mv;
  doc["result"]["tol_mv"] = BIST_VOLTAGE_TOLERANCE_MV;
  doc["result"]["pass"] = (mv <= (unsigned int)bv->mv + BIST_VOLTAGE_TOLERANCE_MV) &&
                          (mv + BIST_VOLTAGE_TOLERANCE_MV >= bv->mv);
  return rpc_response(doc);  // always the last line of RPC API
}
