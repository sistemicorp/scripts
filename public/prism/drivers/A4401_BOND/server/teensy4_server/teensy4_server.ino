/*  Sistemi Corporation, copyright, all rights reserved, 2021-2025
 *  Martin Guthrie
 *  
 *  Dedicated functions for the BOND design, a4401. 
 *
 *  Notes:
 *  1) functions begining with "_" are considered "private" and should not
 *     be called thru the RPC API.  These are "supporting" functions.
 *  2) "Bond"
*/
#include <Wire.h>
#include <simpleRPC.h>
#include <ArduinoJson.h>
#include "version.h"  // holds the "version" of this code, !update when code is changed!
#include <INA219_WE.h>
#include "src/MAX11311/MAX11300.h"
#include "bond_max_iox.h"
#include "bond_max_hdr.h"
#include "bond_vdut.h"
#include "src/oled/bond_oled.h"

#define INA220_VBAT_I2C_ADDRESS 0x40
#define INA220_VDUT_I2C_ADDRESS 0x41
#define INA220_VBAT_SHUNT_OHMS  0.2f
#define INA220_VDUT_SHUNT_OHMS  0.2f

#define SELF_TEST_LOAD_RESISTOR 200.0f

#define BUTTON1_PIN             6   // Jig Closed Detection
#define BUTTON2_PIN             7   // User defined
#define MAX11311_CONVERT_Pin    8
#define VDUT_SMPS_EN_PIN        10  // schematic name VDUTSMPS_EN
#define VDUT_CONNECT_PIN        11  // schematic name VDUT_EN
#define BIST_VOLTAGE_V3V3D_PIN  22  // ADC input
#define BIST_VOLTAGE_V3V3A_PIN  23  // ADC input
#define BIST_VOLTAGE_V6V_PIN    24  // ADC input
#define BIST_VOLTAGE_V5V_PIN    25  // ADC input
#define SPI_MOSI_Pin            26
#define SPI_SCLK_Pin            27
#define VSYS_EN_PIN             31
#define SPI_CS_IOX_Pin          33
#define SPI_CS2_HDR4_Pin        34 
#define SPI_CS_HDR4_Pin         35  
#define SPI_CS_HDR3_Pin         36
#define SPI_CS_HDR2_Pin         37
#define SPI_CS_HRD1_Pin         38
#define SPI_MISO_Pin            39
#define VDUTSMPS_INT            40
#define BIST_VOLTAGE_NEG2V5_PIN 41  // ADC input

#define SETUP_FAIL_USEME        1
#define SETUP_FAIL_INA219_VBAT  2
#define SETUP_FAIL_INA219_VDUT  3
#define SETUP_FAIL_MAX_IOX      4
#define SETUP_FAIL_RESET        5
#define SETUP_FAIL_VOLTAGE      6
#define SETUP_FAIL_VDUT         7
#define SETUP_FAIL_BATTEM       8
#define SETUP_FAIL_MAX_HDR      9
#define SETUP_FAIL_SELFTEST     10

static uint16_t setup_fail_code = 0;

extern uint32_t external_psram_size;

typedef struct {
  uint8_t pin;
  uint16_t mv;
  char name[6];
} _bist_voltages;
static _bist_voltages bist_voltages[] = {
  {.pin = BIST_VOLTAGE_V6V_PIN,    .mv = 6000, .name = "V6V"},
  {.pin = BIST_VOLTAGE_V3V3A_PIN,  .mv = 3300, .name = "V3V3A"},
  {.pin = BIST_VOLTAGE_V3V3D_PIN,  .mv = 3300, .name = "V3V3D"},
  {.pin = BIST_VOLTAGE_V5V_PIN,    .mv = 5000, .name = "V5V"},

  // Note the resistor divider on BOND level shifts the -2.5V
  // to a positive value so that Teensy ADC can read it. The
  // correct mv value is obscured by usng the same voltage
  // divider math for al the other pins.  TODO: validate this with math
  {.pin = BIST_VOLTAGE_NEG2V5_PIN, .mv = 4079, .name = "V2V5N"},
};

INA219_WE ina219_vbat = INA219_WE(INA220_VBAT_I2C_ADDRESS);
INA219_WE ina219_vdut = INA219_WE(INA220_VDUT_I2C_ADDRESS);

// Original Repo: https://github.com/sistemicorp/MAX11300/tree/master
// Clone the repo and documentation can be found in "extras"
MAX11300 max_iox = MAX11300();
MAX11300 max_hdr1 = MAX11300();
MAX11300 max_hdr2 = MAX11300();
MAX11300 max_hdr3 = MAX11300();
MAX11300 max_hdr4 = MAX11300();

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

  oled_print(OLED_LINE_RPC, __func__, false);
  return _response(doc);  // always the last line of RPC API
}

/* reboot_to_bootloader
 *  - software reset Teensy to jump to bootloader for reprogramming
 *  - this function does not really return because Teensy has been "reset",
 *    in the Python Teensy class, the return has been "faked".
 */
String reboot_to_bootloader() {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  oled_print(OLED_LINE_RPC, __func__, false);

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

  oled_print(OLED_LINE_RPC, __func__, false);
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
  
  oled_print(OLED_LINE_RPC, __func__, false);
  return _response(doc);  // always the last line of RPC API
}

/* mem_info
 *  - from https://forum.pjrc.com/index.php?threads/how-to-display-free-ram.33443/#post-284796
 */
void mem_info(uint32_t *stack, uint32_t *heap, uint32_t *psram) {
  extern char _ebss[], _heap_end[],_extram_start[],_extram_end[],*__brkval;

  auto sp = (char*) __builtin_frame_address(0);
  auto _stack = sp-_ebss;
  auto _heap = _heap_end-__brkval;
  auto _psram = _extram_start + (external_psram_size << 20) - _extram_end;

  *stack = _stack >> 10;
  *heap = _heap >> 10;
  *psram = _psram >> 10;
}

/* status
 *  - status flags and codes
 *  - memory stuff from https://forum.pjrc.com/index.php?threads/how-to-display-free-ram.33443/#post-284796
 */
String status() {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API

  // TODO: might optionally (re-)run BIST here

  doc["result"]["setup_fail_code"] = setup_fail_code;

  uint32_t stack = 0, heap = 0, psram = 0;
  mem_info(&stack, &heap, &psram);

  doc["result"]["stack_kb"] = stack;
  doc["result"]["heap_kb"] = heap;
  doc["result"]["psram_kb"] = psram;

  oled_print(OLED_LINE_RPC, __func__, false);
  return _response(doc);  // always the last line of RPC API
}

/* vdut_con
 *  - set VDUT_EN pin, which is active (asserted) HIGH
 *  - connects VDUT to the DUT
 */
String vdut_con(bool assert) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API

  digitalWrite(VDUT_CONNECT_PIN, assert ? HIGH : LOW);

  doc["result"]["assert"] = assert;
  doc["result"]["level"] = assert;

  oled_print(OLED_LINE_RPC, __func__, false);
  return _response(doc);  // always the last line of RPC API
}

/* vdut_en
 *  - set VDUTSMPS_EN pin, which is active (asserted) HIGH
 *  - enables TPS55289
 */
String vdut_en(bool assert) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API

  digitalWrite(VDUT_SMPS_EN_PIN, assert ? HIGH : LOW);

  doc["result"]["assert"] = assert;
  doc["result"]["level"] = assert;

  oled_print(OLED_LINE_RPC, __func__, false);
  return _response(doc);  // always the last line of RPC API
}

int _reset(void) {
  // called on setup() and by API reset()
  // ... add any required resetting code here ...

  max_iox.gpio_write(MAX11300::PIXI_PORT2, 0); // vbat disconnect
  max_iox.gpio_write(MAX11300::PIXI_PORT7, 0); // self test disable
  digitalWrite(VDUT_CONNECT_PIN, LOW);
  iox_vbat_con(false);

  // flash all LEDs
  iox_led_yellow(true);
  iox_led_red(true);
  iox_led_green(true);
  iox_led_blue(true);
  delay(200);
  iox_led_yellow(false);
  iox_led_red(false);
  iox_led_green(false);
  iox_led_blue(false);

  return 0;
}

/* reset
 *  - this reset is called when Prism "finishes" the DUT test
 *  - DOES NOT RESET TEENSY, meerly resets its "state"
 */
String reset(){
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  oled_print(OLED_LINE_RPC, __func__, false);

  if (_reset()) {
    doc["success"] = false;
    doc["result"]["error"] = "reset failed";
  }

  return _response(doc);  // always the last line of RPC API
}

/* _self_test
 *  - asserts the SELF_TEST signal on BOND
 *  - measures the VDUT and VBUS voltage and current to confirm operation
*/
int _self_test(void) {
  char buf[LINE_MAX_LENGTH];

  // check VDUT
  #define VDUT_SELF_TEST_MV_TOL        0.05f
  #define VDUT_SELF_TEST_MA_TOL        0.5f
  #define VDUT_SELF_TEST_MA_NOLOAD_MAX 0.5f

  uint16_t voltages[] = {2000, 4000};
  float ma_max_no_load = 0.25f;
  for(int i = 0; i < sizeof(voltages) / sizeof(uint16_t); i++) {
    vdut_set(voltages[i]);
    ina219_vdut.startSingleMeasurement();  
    delay(1);      
    float v = ina219_vdut.getBusVoltage_V();
    float ma = ina219_vdut.getCurrent_mA();
    float vf = voltages[i] / 1000.0f;
    snprintf(buf, LINE_MAX_LENGTH, "vdut1 %.2f %.2f %0.2f", vf, v, ma);
    if (v > (vf + VDUT_SELF_TEST_MV_TOL) || v < (vf - VDUT_SELF_TEST_MV_TOL)) {
      oled_print(OLED_LINE_DEBUG, buf, true);
      delay(500);  // use for debug on display
      return -1;
    }
    if (ma > VDUT_SELF_TEST_MA_NOLOAD_MAX) {
      oled_print(OLED_LINE_DEBUG, buf, true);
      delay(500);  // use for debug on display
      return -1;
    }    
    oled_print(OLED_LINE_DEBUG, buf, false);
    delay(100);  // use for debug on display

    // set SELF_TEST and check current
    iox_selftest(true);
    vdut_con(true);
    ina219_vdut.startSingleMeasurement();      
    delay(1);
    v = ina219_vdut.getBusVoltage_V();
    ma = ina219_vdut.getCurrent_mA();
    vf = voltages[i] / 1000.0f;
    float ma_expected = (vf / SELF_TEST_LOAD_RESISTOR) * 1000.0;  // 200 ohm load resistor
    snprintf(buf, LINE_MAX_LENGTH, "vdut2 %.2f %.2f %0.2f", v, ma, ma_expected);
    if (v > (vf + VDUT_SELF_TEST_MV_TOL) || v < (vf - VDUT_SELF_TEST_MV_TOL)) {
      oled_print(OLED_LINE_DEBUG, buf, true);
      delay(500);  // use for debug on display
      return -1;
    }
    if (ma > (ma_expected + VDUT_SELF_TEST_MA_TOL) || ma < (ma_expected - VDUT_SELF_TEST_MA_TOL)) {
      oled_print(OLED_LINE_DEBUG, buf, true);
      delay(500);  // use for debug on display
      return -1;
    }    
    oled_print(OLED_LINE_DEBUG, buf, false);
    iox_selftest(false);
    vdut_con(false);
    delay(100);  // use for debug on display
  }

  return 0;
}

//-------------------------------------------------------------------------------------------------------------
//set-up/loop Functions

void setup(void) {
  unsigned int blink_delay_ms = 100;
  unsigned int blink_error_count = 0;
  char buf[LINE_MAX_LENGTH];

  // set Teensy BOND pins, disable where application
  pinMode(VSYS_EN_PIN, OUTPUT);
  pinMode(VDUT_CONNECT_PIN, OUTPUT);
  pinMode(VDUT_SMPS_EN_PIN, OUTPUT);
  digitalWrite(VDUT_SMPS_EN_PIN, LOW); 
  pinMode(MAX11311_CONVERT_Pin, OUTPUT); 
  pinMode(VDUTSMPS_INT, INPUT); 
  pinMode(BUTTON1_PIN, INPUT);
  pinMode(BUTTON2_PIN, INPUT);

  // toggle (power reset) VSYS (~6V) - powers rest of system
  digitalWrite(VSYS_EN_PIN, LOW);
  delay(10);
  digitalWrite(VSYS_EN_PIN, HIGH);
  delay(100);

  // set SPI interface pin modes
  pinMode (SPI_CS_IOX_Pin, OUTPUT);   // ensure SPI CS is driven output
  digitalWrite(SPI_CS_IOX_Pin, HIGH); // SPI CS inactive high
  pinMode (SPI_CS_HRD1_Pin, OUTPUT); 
  digitalWrite(SPI_CS_HRD1_Pin, HIGH); 
  pinMode (SPI_CS_HDR2_Pin, OUTPUT); 
  digitalWrite(SPI_CS_HDR2_Pin, HIGH); 
  pinMode (SPI_CS_HDR3_Pin, OUTPUT); 
  digitalWrite(SPI_CS_HDR3_Pin, HIGH); 
  pinMode (SPI_CS_HDR4_Pin, OUTPUT); 
  digitalWrite(SPI_CS_HDR4_Pin, HIGH); 
  pinMode (SPI_CS2_HDR4_Pin, OUTPUT);          
  digitalWrite(SPI_CS2_HDR4_Pin, HIGH); 
  pinMode (SPI_MOSI_Pin, OUTPUT);
  digitalWrite(SPI_MOSI_Pin, LOW);
  pinMode (SPI_SCLK_Pin, OUTPUT);
  digitalWrite(SPI_SCLK_Pin, LOW);
  pinMode (SPI_MISO_Pin, INPUT);

  Serial.begin(115200);
  Wire.begin();
  Wire.setClock(400000);
  pinMode(LED_BUILTIN, OUTPUT);

  oled_init();
  oled_print(OLED_LINE_STATUS, "SETUP:BOOTING...", false);

  int success = init_max_iox();
  if (success != 0) {
    setup_fail_code |= (0x1 << SETUP_FAIL_MAX_IOX);
    oled_print(OLED_LINE_STATUS, "SETUP:init_max_iox", true);
    blink_error_count = SETUP_FAIL_MAX_IOX;
    goto fail;
  }
  snprintf(buf, LINE_MAX_LENGTH, "max_iox");
  oled_print(OLED_LINE_DEBUG, buf, false);

  // reset 
  if (_reset()) {
    setup_fail_code |= (0x1 << SETUP_FAIL_RESET);
    oled_print(OLED_LINE_STATUS, "SETUP:reset", true);
    blink_error_count = SETUP_FAIL_RESET;
    goto fail;
  }
  // turn on YELLOW while setup is running
  iox_led_yellow(true);

  // ADC
  pinMode(BIST_VOLTAGE_V3V3A_PIN, INPUT);  // analog input
  pinMode(BIST_VOLTAGE_V3V3D_PIN, INPUT);  // analog input
  pinMode(BIST_VOLTAGE_V5V_PIN, INPUT);    // analog input
  pinMode(BIST_VOLTAGE_V6V_PIN, INPUT);    // analog input
  pinMode(BIST_VOLTAGE_NEG2V5_PIN, INPUT); // analog input

  // Check all BIST voltages...
  // note this code has delay on reading, allowing for voltages
  // to reach steady state... TODO: is delay really needed?
  {
    for(uint8_t i=0; i < sizeof(bist_voltages) / sizeof(_bist_voltages); i++) {
      #define BIST_VOLTAGE_TOL_MV  50
      unsigned int mv = 0;
      int count_down = 10;
      int count_good_measures = 2;
      while (count_down > 0) {
        unsigned int adc_raw = _read_adc(bist_voltages[i].pin, 10, 2);
        mv = (adc_raw * 3300 * 3) / 1024;  // * 3 for resistor divider, 10k / (10k + 20k)
        if ((mv < (bist_voltages[i].mv + BIST_VOLTAGE_TOL_MV)) && (mv > (bist_voltages[i].mv - BIST_VOLTAGE_TOL_MV))) {
          // the voltage is in range
          count_good_measures--;
          if (count_good_measures == 0) break;
        }
        count_down--;
        delay(20);
      }
      // there must be count_good_measures before count_down expires to pass this test
      if (count_down == 0) {
        setup_fail_code |= (0x1 << SETUP_FAIL_VOLTAGE);
        snprintf(buf, LINE_MAX_LENGTH, "voltage %s %u", bist_voltages[i].name, mv);
        oled_print(OLED_LINE_DEBUG, buf, true);
        blink_error_count = SETUP_FAIL_VOLTAGE;
        goto fail;
      }
      snprintf(buf, LINE_MAX_LENGTH, "voltage %s %u", bist_voltages[i].name, mv);
      oled_print(OLED_LINE_DEBUG, buf, false);
    }
  }

  // configure INA220s
  if (!ina219_vbat.init()) {
    setup_fail_code |= (0x1 << SETUP_FAIL_INA219_VBAT);
    oled_print(OLED_LINE_STATUS, "SETUP:INA219_VBAT", true);
    blink_error_count = SETUP_FAIL_INA219_VBAT;
    goto fail;
  }
  oled_print(OLED_LINE_DEBUG, "ina219_vbat.init", false);

  ina219_vbat.setShuntSizeInOhms(INA220_VBAT_SHUNT_OHMS);
  ina219_vbat.setBusRange(INA219_BRNG_16);
  ina219_vbat.setADCMode(INA219_SAMPLE_MODE_16);
  ina219_vbat.setMeasureMode(INA219_TRIGGERED);

  if (!ina219_vdut.init()) {
    setup_fail_code |= (0x1 << SETUP_FAIL_INA219_VDUT);
    oled_print(OLED_LINE_STATUS, "SETUP:INA219_VDUT", true);
    blink_error_count = SETUP_FAIL_INA219_VDUT;
    goto fail;
  }
  oled_print(OLED_LINE_DEBUG, "ina219_vdut.init", false);

  ina219_vdut.setShuntSizeInOhms(INA220_VDUT_SHUNT_OHMS);
  ina219_vdut.setBusRange(INA219_BRNG_16);
  ina219_vdut.setADCMode(INA219_SAMPLE_MODE_16);
  ina219_vdut.setMeasureMode(INA219_TRIGGERED);

  if (vdut_init()) {
    setup_fail_code |= (0x1 << SETUP_FAIL_VDUT);
    oled_print(OLED_LINE_STATUS, "SETUP:vdut", true);
    blink_error_count = SETUP_FAIL_VDUT;
    goto fail;    
  }
  oled_print(OLED_LINE_DEBUG, "vdut_init", false);

  if (init_max_hdr_bist()) {
    setup_fail_code |= (0x1 << SETUP_FAIL_MAX_HDR);
    oled_print(OLED_LINE_STATUS, "SETUP:._max_hdr_bist", true);
    blink_error_count = SETUP_FAIL_MAX_HDR;
    goto fail;     
  }

  if (battemu_init()) {
    setup_fail_code |= (0x1 << SETUP_FAIL_BATTEM);
    oled_print(OLED_LINE_STATUS, "SETUP:battemu_init", true);
    blink_error_count = SETUP_FAIL_BATTEM;
    goto fail;      
  }

  if (_self_test()) {
    setup_fail_code |= (0x1 << SETUP_FAIL_SELFTEST);
    oled_print(OLED_LINE_STATUS, "SETUP:self_test", true);
    blink_error_count = SETUP_FAIL_SELFTEST;
    goto fail;      
  }  

  // Add more startup checks here...

  oled_print(OLED_LINE_STATUS, "SETUP: COMPLETE", false);
  spinner_update();

  // blink the TEENSY LED to let people know we started, 2 fast blinks
  digitalWrite(LED_BUILTIN, HIGH);
  delay(blink_delay_ms);
  digitalWrite(LED_BUILTIN, LOW);
  delay(blink_delay_ms);
  digitalWrite(LED_BUILTIN, HIGH);
  delay(blink_delay_ms);
  digitalWrite(LED_BUILTIN, LOW);

  // turn off YELLOW setup is done
  iox_led_yellow(false);

  return;

fail:
  // On error, LED blinks 3x (slower), then count the error code
  blink_delay_ms *= 2;
  digitalWrite(LED_BUILTIN, LOW);
  delay(blink_delay_ms);
  for (int i=0; i < blink_error_count; i++) {
    digitalWrite(LED_BUILTIN, HIGH);
    delay(blink_delay_ms * 2);
    digitalWrite(LED_BUILTIN, LOW);
    delay(blink_delay_ms * 2);
  }
}

static unsigned long lastTime = 0;
void loop(void) {
 
  // Display status
  if (millis() - lastTime > 2000) {
    lastTime = millis();
    if (setup_fail_code) {
      // error - show code
      char _buf[LINE_MAX_LENGTH];
      snprintf(_buf, LINE_MAX_LENGTH, "setupfailcode %d", setup_fail_code);
      oled_print(OLED_LINE_DEBUG, _buf, true);
    }
    spinner_update();
  }

  // interface() is non-blocking
  // NOTE: !! the function name and string beginning must match !!
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
    status, "status: status flags",
    bist_voltage, "bist_voltage: Reads internal voltage",

    // A44BOND APIs
    bond_max_hdr_init, "bond_max_hdr_init: init max11311 on header #",
    bond_max_hdr_adc_cal, "bond_max_hdr_adc_cal: read port 11 cal voltage on header",
    bond_max_hdr_adc, "bond_max_hdr_adc: read ADC voltage on header port",
    bond_max_hdr_dac, "bond_max_hdr_dac: write DAC voltage on header port",
    bond_batt_emu_cal, "bond_batt_emu_cal: calibrate battery emulator",

    vdut_read, "vbus_read: Read VDUT current and voltage",
    vbat_read, "vbat_read: Read VBAT current and voltage",
    vbat_set, "vbat_set: Set VBAT voltage mV",
    vdut_set, "vdut_set: Set VDUT voltage mV",
    vdut_get_fault, "vdut_get_fault: Get faults reported by TPS55289",
    vdut_reset, "vdut_reset: reset TPS55289",
    vdut_con, "vdut_con: Connect VDUT to target",
    vdut_en, "vdut_en: Enable VDUT TPS55289",
    iox_led_green, "iox_led_green: green led",
    iox_led_yellow, "iox_led_yellow: yellow led",
    iox_led_red, "iox_led_red: red led",
    iox_led_blue, "iox_led_blue: blue led",
    iox_vbat_en, "iox_vbat_en: VBAT Enable",
    iox_vbat_con, "iox_vbat_con: VBAT Connect",
    iox_selftest, "iox_selftest: Self test Enable",

    // for debugging
    debug_batt_emu, "debug_batt_emu: debug battery lut"

  );
}
