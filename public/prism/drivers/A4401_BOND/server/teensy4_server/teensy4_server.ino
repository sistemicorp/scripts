/*  Sistemi Corporation, copyright, all rights reserved, 2021-2023
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
#include "src/oled/bond_oled.h"

#define INA220_VBAT_I2C_ADDRESS 0x40
#define INA220_VBUS_I2C_ADDRESS 0x41
#define INA220_VBAT_SHUNT_OHMS  0.2f
#define INA220_VBUS_SHUNT_OHMS  0.2f

#define VSYS_EN_PIN             41
#define VSYS_PG_PIN             40

#define BIST_VOLTAGE_V3V3A_PIN  23
#define BIST_VOLTAGE_V3V3D_PIN  22
#define BIST_VOLTAGE_V5V_PIN    25
#define BIST_VOLTAGE_V6V_PIN    24
#define SPI_CS_IOX_Pin          33
#define SPI_CS_HRD1_Pin         38
#define SPI_CS_HDR2_Pin         37
#define SPI_CS_HDR3_Pin         36
#define SPI_CS_HDR4_Pin         35  
#define SPI_CS2_HDR4_Pin        34 
#define SPI_MOSI_Pin            26
#define SPI_MISO_Pin            39
#define SPI_SCLK_Pin            27
#define MAX11311_COPNVERT_Pin   8

#define SETUP_FAIL_VSYS_PG_PIN  0
#define SETUP_FAIL_INA219_VBAT  1
#define SETUP_FAIL_INA219_VBUS  2
#define SETUP_FAIL_MAX_IOX      3
static uint16_t setup_fail_code = 0;

extern uint32_t external_psram_size;

INA219_WE ina219_vbat = INA219_WE(INA220_VBAT_I2C_ADDRESS);
INA219_WE ina219_vbus = INA219_WE(INA220_VBUS_I2C_ADDRESS);

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
  doc["result"]["setup_fail_code"] = setup_fail_code;

  uint32_t stack = 0, heap = 0, psram = 0;
  mem_info(&stack, &heap, &psram);

  doc["result"]["stack_kb"] = stack;
  doc["result"]["heap_kb"] = heap;
  doc["result"]["psram_kb"] = psram;

  oled_print(OLED_LINE_RPC, __func__, false);
  return _response(doc);  // always the last line of RPC API
}

/* reset
 *  - reset this code
 *  - DOES NOT RESET TEENSY, meerly resets its "state"
 */
String reset(){
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  oled_print(OLED_LINE_RPC, __func__, false);

  // ... add any required resetting code here ...
  
  return _response(doc);  // always the last line of RPC API
}

//-------------------------------------------------------------------------------------------------------------
//set-up/loop Functions

void setup(void) {
  unsigned int blink_delay_ms = 100;

  Serial.begin(115200);
  Wire.begin();
  Wire.setClock(400000);
  pinMode(LED_BUILTIN, OUTPUT);

  // blink the LED to let people know we are good
  digitalWrite(LED_BUILTIN, HIGH);
  delay(blink_delay_ms);
  digitalWrite(LED_BUILTIN, LOW);
  delay(blink_delay_ms);
  digitalWrite(LED_BUILTIN, HIGH);
  delay(blink_delay_ms);
  digitalWrite(LED_BUILTIN, LOW);

  oled_init();
  oled_print(OLED_LINE_STATUS, "SETUP:BOOTING...", false);

  // set SPI interface pin modes
  // TODO: probably don't need this as MAX11300 inits pins
  digitalWrite(SPI_CS_IOX_Pin, HIGH); // SPI CS inactive high
  pinMode (SPI_CS_IOX_Pin, OUTPUT);   // ensure SPI CS is driven output
  digitalWrite(SPI_CS_HRD1_Pin, HIGH); 
  pinMode (SPI_CS_HRD1_Pin, OUTPUT); 
  digitalWrite(SPI_CS_HDR2_Pin, HIGH); 
  pinMode (SPI_CS_HDR2_Pin, OUTPUT); 
  digitalWrite(SPI_CS_HDR3_Pin, HIGH); 
  pinMode (SPI_CS_HDR3_Pin, OUTPUT); 
  digitalWrite(SPI_CS_HDR4_Pin, HIGH); 
  pinMode (SPI_CS_HDR4_Pin, OUTPUT); 
  digitalWrite(SPI_CS2_HDR4_Pin, HIGH); 
  pinMode (SPI_CS2_HDR4_Pin, OUTPUT);          
  digitalWrite(SPI_MOSI_Pin, LOW);
  pinMode (SPI_MOSI_Pin, OUTPUT);
  pinMode (SPI_MISO_Pin, INPUT);
  digitalWrite(SPI_SCLK_Pin, LOW);
  pinMode (SPI_SCLK_Pin, OUTPUT);

  // set BOND pins
  pinMode(VSYS_EN_PIN, OUTPUT);
  pinMode(VSYS_PG_PIN, INPUT);

  // ADC
  pinMode(BIST_VOLTAGE_V3V3A_PIN, INPUT);  // analog input
  pinMode(BIST_VOLTAGE_V3V3D_PIN, INPUT);  // analog input
  pinMode(BIST_VOLTAGE_V5V_PIN, INPUT);    // analog input
  pinMode(BIST_VOLTAGE_V6V_PIN, INPUT);    // analog input

  // turn on VSYS (~6V) - powers rest of system
  digitalWrite(VSYS_EN_PIN, HIGH);
  delay(100);
  // check VSYS_PG_PIN
  uint8_t vsys_pg_pin = digitalRead(VSYS_PG_PIN);
  if (vsys_pg_pin == 0) {
    setup_fail_code |= (0x1 << SETUP_FAIL_VSYS_PG_PIN);
    oled_print(OLED_LINE_STATUS, "SETUP:VSYS_PG_PIN", true);
    goto fail;
  }

  {  // fixes build error on goto
    int success = init_max_iox();
    if (success != 0) {
      setup_fail_code |= (0x1 << SETUP_FAIL_MAX_IOX);
      oled_print(OLED_LINE_STATUS, "SETUP:INA219_VBUS", true);
      goto fail;
    }
  }
  // configure INA220s
  if (!ina219_vbat.init()) {
    setup_fail_code |= (0x1 << SETUP_FAIL_INA219_VBAT);
    oled_print(OLED_LINE_STATUS, "SETUP:INA219_VBAT", true);
    goto fail;
  }

  ina219_vbat.setShuntSizeInOhms(INA220_VBAT_SHUNT_OHMS);
  ina219_vbat.setBusRange(BRNG_16);
  ina219_vbat.setMeasureMode(TRIGGERED);

  if (!ina219_vbus.init()) {
    setup_fail_code |= (0x1 << SETUP_FAIL_INA219_VBUS);
    oled_print(OLED_LINE_STATUS, "SETUP:INA219_VBUS", true);
    goto fail;
  }

  ina219_vbus.setShuntSizeInOhms(INA220_VBUS_SHUNT_OHMS);
  ina219_vbus.setBusRange(BRNG_16);
  ina219_vbus.setMeasureMode(TRIGGERED);

fail:
  delay(blink_delay_ms);
  if (setup_fail_code) {
    // long blinks if things are bad
    blink_delay_ms = 500;

    // shutdown for safety
    //digitalWrite(VSYS_EN_PIN, LOW);
  } else {
    oled_print(OLED_LINE_STATUS, "SETUP: COMPLETE", false);
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
    status, "status: status flags",
    bist_voltage, "bist_voltage: Reads internal voltage",

    // A44BOND APIs
    bond_max_hdr_init, "bond_max_hdr_init: init max11311 on header #",
    bond_max_hdr_adc_cal, "bond_max_hdr_adc_cal: read port 11 cal voltage on header",
    bond_max_hdr_adc, "bond_max_hdr_adc: read ADC voltage on header port",
    bond_max_hdr_dac, "bond_max_hdr_dac: write DAC voltage on header port",

    vbus_read, "vbus_read: Read VBUS current and voltage",
    vbat_read, "vbat_read: Read VBAT current and voltage",
    iox_reset, "iox_reset: IOX reset (USB Hub) pin",
    iox_led_green, "iox_led_green: green led",
    iox_led_yellow, "iox_led_yellow: yellow led",
    iox_led_red, "iox_led_red: red led",
    iox_led_blue, "iox_led_blue: blue led",
    iox_vbus_en, "iox_vbus_en: VBUS Enable",
    iox_vbat_en, "iox_vbat_en: VBAT Enable",
    iox_vbat_con, "iox_vbat_con: VBAT Connect"
  );
}
