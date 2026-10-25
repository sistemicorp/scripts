/*  Sistemi Corporation, copyright, all rights reserved, 2021-2026
 *  Martin Guthrie
 *
 *  BOND (a4402) Teensy 4.1 simpleRPC server, schematic a4402-SCH_05.
 *
 *  Code organization:
 *  - teensy4_server.ino   setup(), loop() and the RPC table (this file)
 *  - bond_pins.h          Teensy pin assignments
 *  - bond_board.*         shared on-board I2C devices (INA226s, TMP1075, CYPD3176)
 *  - bond_teensy.*        Teensy functions: ids, status, GPIO, ADC, supply rail BIST
 *  - bond_max_iox.*       MAX11311 IO expander: LEDs, self test, VBAT enables
 *  - bond_max_hdr.*       MAX11311 on DUT headers 1-4
 *  - bond_vdut.*          VDUT supply (TPS55289)
 *  - battemu.*            battery emulator (VBAT)
 *  - bond_selftest.*      reset (DUT safe state) and the power up self test
 *  - rpc_helpers.*        RPC response document helpers
 *  - src/                 device libraries (MAX11311, OLED, TMP1075, CYPD3176)
 *
 *  Each module header lists its internal API and its RPC API. An RPC function must
 *  never call another RPC function, see rpc_helpers.h.
 *
 *  Adding an RPC: write it in the module (see rpc_helpers.h for the shape), declare
 *  it in the module header, and add it to interface() in loop().
 */
#include <Wire.h>
#include <simpleRPC.h>
#include "version.h"  // holds the "version" of this code, !update when code is changed!
#include "bond_pins.h"
#include "bond_board.h"
#include "bond_teensy.h"
#include "bond_max_iox.h"
#include "bond_max_hdr.h"
#include "bond_vdut.h"
#include "battemu.h"
#include "bond_selftest.h"
#include "src/oled/bond_oled.h"

// setup_fail_code bit numbers, see status()
#define SETUP_FAIL_INA226_VBAT  2
#define SETUP_FAIL_INA226_VDUT  3
#define SETUP_FAIL_MAX_IOX      4
#define SETUP_FAIL_VOLTAGE      6
#define SETUP_FAIL_VDUT         7
#define SETUP_FAIL_BATTEM       8
#define SETUP_FAIL_MAX_HDR      9
#define SETUP_FAIL_SELFTEST     10
#define SETUP_FAIL_CYPD3176     11

#define CYPD3176_DEVICE_ID      0x2011
#define BIST_VOLTAGE_TOL_MV     50
#define V6V_WAIT_TRIES          100
#define BIST_TRIES              10
#define BIST_GOOD_READINGS      2
#define BIST_ADC_SAMPLES        10
#define BIST_ADC_RATE_MS        2
#define BLINK_MS                100
#define STATUS_PERIOD_MS        2000

static unsigned int setup_blink_code = 0;
static bool setup_ok = false;

static bool _bist_in_tol(const bist_voltage_t &bv, unsigned int *mv_out) {
  unsigned int mv = bist_adc_to_mv(teensy_read_adc(bv.pin, BIST_ADC_SAMPLES, BIST_ADC_RATE_MS));
  *mv_out = mv;
  return (mv < (unsigned int)bv.mv + BIST_VOLTAGE_TOL_MV) && (mv + BIST_VOLTAGE_TOL_MV > bv.mv);
}

static bool _setup_fail(uint16_t code, const char *msg) {
  set_setup_fail_code(code);
  setup_blink_code = code;
  oled_print(OLED_LINE_STATUS, msg, true);
  return false;
}

/* _wait_for_v6v
 * - wait on V6V, indicating USB-PD is on
 * - can't use I2C while CYPD3176 is waiting for USB-PD
 * - when VIN is not present, there is back powering of CYPD3176 causing it NOT
 *   to negotiate USB-PD, toggling VSYS_EN_PIN (VSYS ~6V, powers the rest of BOND) fixes this
 */
static bool _wait_for_v6v(void) {
  unsigned int mv = 0;
  int good = BIST_GOOD_READINGS;
  for (int tries = V6V_WAIT_TRIES; tries > 0; tries--) {
    digitalWrite(VSYS_EN_PIN, HIGH);
    delay(100);
    if (_bist_in_tol(bist_voltages[0], &mv) && --good == 0) return true;
    digitalWrite(VSYS_EN_PIN, LOW);
    delay(20);
    digitalWrite(LED_BUILTIN, HIGH);
    delay(100);
    digitalWrite(LED_BUILTIN, LOW);
    delay(200);
  }
  return false;
}

/* _check_rails
 * - every BIST rail must read in tolerance BIST_GOOD_READINGS times within BIST_TRIES
 */
static bool _check_rails(void) {
  char buf[LINE_MAX_LENGTH];
  for (unsigned int i = 0; i < bist_voltages_num; i++) {
    unsigned int mv = 0;
    int good = BIST_GOOD_READINGS;
    int tries = BIST_TRIES;
    while (tries-- > 0) {
      if (_bist_in_tol(bist_voltages[i], &mv) && --good == 0) break;
      delay(20);
    }
    snprintf(buf, LINE_MAX_LENGTH, "voltage %s %u", bist_voltages[i].name, mv);
    oled_print(OLED_LINE_DEBUG, buf, good != 0);
    if (good != 0) return false;
  }
  return true;
}

static void _pins_init(void) {
  pinMode(VSYS_EN_PIN, OUTPUT);
  digitalWrite(VSYS_EN_PIN, LOW);  // disable VSYS on boot
  pinMode(VDUT_CONNECT_PIN, OUTPUT);
  digitalWrite(VDUT_CONNECT_PIN, LOW);
  pinMode(VDUT_SMPS_EN_PIN, OUTPUT);
  digitalWrite(VDUT_SMPS_EN_PIN, LOW);
  pinMode(MAX11311_CONVERT_Pin, OUTPUT);
  pinMode(VDUTSMPS_INT, INPUT);
  pinMode(BUTTON1_PIN, INPUT);
  pinMode(BUTTON2_PIN, INPUT);
  pinMode(LED_BUILTIN, OUTPUT);

  for (unsigned int i = 0; i < bist_voltages_num; i++) {
    pinMode(bist_voltages[i].pin, INPUT);  // analog input
  }

  // SPI, chip selects inactive high
  const uint8_t cs_pins[] = {SPI_CS_IOX_Pin, SPI_CS_HDR1_Pin, SPI_CS_HDR2_Pin, SPI_CS_HDR3_Pin,
                             SPI_CS_HDR4_Pin, SPI_CS2_HDR4_Pin};
  for (uint8_t pin : cs_pins) {
    pinMode(pin, OUTPUT);
    digitalWrite(pin, HIGH);
  }
  pinMode(SPI_MOSI_Pin, OUTPUT);
  digitalWrite(SPI_MOSI_Pin, LOW);
  pinMode(SPI_SCLK_Pin, OUTPUT);
  digitalWrite(SPI_SCLK_Pin, LOW);
  pinMode(SPI_MISO_Pin, INPUT);
}

static void _ina226_init(INA226_WE &ina, float shunt_ohms) {
  ina.setResistorRange(shunt_ohms, INA226_CURRENT_RANGE_A);
  ina.setMeasureMode(INA226_TRIGGERED);
}

/* _setup
 * - bring up BOND, return false on the first failure (setup_blink_code is set)
 */
static bool _setup(void) {
  char buf[LINE_MAX_LENGTH];

  if (!_wait_for_v6v()) {
    set_setup_fail_code(SETUP_FAIL_VOLTAGE);
    setup_blink_code = SETUP_FAIL_VOLTAGE;
    return false;  // no display yet, I2C can't be used
  }

  Serial.begin(115200);
  Wire.begin();
  Wire.setClock(400000);
  oled_init();

  snprintf(buf, LINE_MAX_LENGTH, "version %s", VERSION);
  oled_print(OLED_LINE_MEM, buf, false);

  oled_print(OLED_LINE_STATUS, "SETUP:SUPPLY CHECK", false);
  if (!_check_rails()) return _setup_fail(SETUP_FAIL_VOLTAGE, "SETUP:voltage");

  oled_print(OLED_LINE_STATUS, "SETUP:CONFIGURE", false);
  if (init_max_iox()) return _setup_fail(SETUP_FAIL_MAX_IOX, "SETUP:init_max_iox");

  // flash all LEDs, then YELLOW while setup is running
  iox_leds(true, true, true, true);
  delay(200);
  iox_leds(false, true, false, false);

  uint16_t cypd3176_id = cypd3176.getDeviceId();
  snprintf(buf, LINE_MAX_LENGTH, "cypd3176 id 0x%x", cypd3176_id);
  oled_print(OLED_LINE_DEBUG, buf, cypd3176_id != CYPD3176_DEVICE_ID);
  if (cypd3176_id != CYPD3176_DEVICE_ID) return _setup_fail(SETUP_FAIL_CYPD3176, "SETUP:CYPD3176");
  // FIXME: cypd3176.getBusVoltageMV() is not working, when it is, gate setup() until VIN is 15V

  bond_reset();

  oled_print(OLED_LINE_STATUS, "SETUP:BIST", false);
  if (!ina226_vbat.init()) return _setup_fail(SETUP_FAIL_INA226_VBAT, "SETUP:INA226_VBAT");
  _ina226_init(ina226_vbat, INA226_VBAT_SHUNT_OHMS);
  if (!ina226_vdut.init()) return _setup_fail(SETUP_FAIL_INA226_VDUT, "SETUP:INA226_VDUT");
  _ina226_init(ina226_vdut, INA226_VDUT_SHUNT_OHMS);

  tmp1075.begin();
  tmp1075.setConversionTime(TMP1075::ConversionTime220ms);
  snprintf(buf, LINE_MAX_LENGTH, "TMP1075 %.2f degC", tmp1075.getTemperatureCelsius());
  oled_print(OLED_LINE_DEBUG, buf, false);

  if (vdut_init()) return _setup_fail(SETUP_FAIL_VDUT, "SETUP:vdut");
  if (init_max_hdr_bist()) return _setup_fail(SETUP_FAIL_MAX_HDR, "SETUP:max_hdr_bist");

  oled_print(OLED_LINE_STATUS, "SETUP:BATTEM CAL", false);
  if (battemu_init()) return _setup_fail(SETUP_FAIL_BATTEM, "SETUP:battemu_init");

  oled_print(OLED_LINE_STATUS, "SETUP:SELF TEST", false);
  if (bond_self_test()) return _setup_fail(SETUP_FAIL_SELFTEST, "SETUP:self_test");

  oled_print(OLED_LINE_STATUS, "SETUP:COMPLETE", false);
  return true;
}

static void _blink(unsigned int count, unsigned int ms) {
  for (unsigned int i = 0; i < count; i++) {
    digitalWrite(LED_BUILTIN, HIGH);
    delay(ms);
    digitalWrite(LED_BUILTIN, LOW);
    delay(ms);
  }
}

void setup(void) {
  _pins_init();

  setup_ok = _setup();
  if (setup_ok) {
    _blink(2, BLINK_MS);  // let people know we started, 2 fast blinks
    iox_set(IOX_PORT_LED_YELLOW, false);
  } else {
    // On error, the RED LED is on and the Teensy LED blinks the fail code (slower)
    iox_set(IOX_PORT_LED_RED, true);
    delay(1500);  // allow error string to be shown for long time
    _blink(setup_blink_code, BLINK_MS * 4);
  }

  spinner_update();
  oled_set_deferred(true);  // from now on the display is written by loop()
}

static unsigned long last_status_ms = 0;

void loop(void) {
  if (millis() - last_status_ms > STATUS_PERIOD_MS) {
    last_status_ms = millis();
    if (!setup_ok) {
      char buf[LINE_MAX_LENGTH];
      snprintf(buf, LINE_MAX_LENGTH, "setup fail code %u", setup_blink_code);
      oled_print(OLED_LINE_DEBUG, buf, true);
    }
    spinner_update();
  }
  oled_service(Serial.available() > 0);

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
    reset, "reset: Set BOND to the DUT safe state (not a Teensy reset).",
    status, "status: status flags",
    temperature, "temperature: Get temperature degC",
    bist_voltage, "bist_voltage: Reads internal voltage",

    // A44BOND APIs
    bond_max_hdr_init, "bond_max_hdr_init: init max11311 on header #",
    bond_max_hdr_adc_cal, "bond_max_hdr_adc_cal: read port 11 cal voltage on header",
    bond_max_hdr_adc, "bond_max_hdr_adc: read ADC voltage on header port",
    bond_max_hdr_dac, "bond_max_hdr_dac: write DAC voltage on header port",
    bond_max_hdr_gpo, "bond_max_hdr_gpo: write GPO state on header port",
    bond_max_hdr_gpi, "bond_max_hdr_gpi: read GPI state on header port",
    bond_batt_emu_cal, "bond_batt_emu_cal: calibrate battery emulator",

    vdut_read, "vdut_read: Read VDUT current and voltage",
    vbat_read, "vbat_read: Read VBAT current and voltage",
    vbat_set, "vbat_set: Set VBAT voltage mV",
    vdut_set, "vdut_set: Set VDUT voltage mV",
    vdut_get_fault, "vdut_get_fault: Get faults reported by TPS55289",
    vdut_reset, "vdut_reset: reset TPS55289",
    vdut_con, "vdut_con: Connect VDUT to target",
    vdut_en, "vdut_en: Enable VDUT TPS55289",
    vbus_en, "vbus_en: Enable VBUS on the External USB-C (HDR3 port 9)",
    bond_ldo_set, "bond_ldo_set: Set Header 1 LDO voltage mV",

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
