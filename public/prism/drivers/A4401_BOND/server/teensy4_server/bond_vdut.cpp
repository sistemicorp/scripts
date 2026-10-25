/*  Sistemi Corporation, copyright, all rights reserved, 2023-2026
 *  Martin Guthrie
 *
 *  VDUT supply, see bond_vdut.h
 *
 *  TPS55289 Settings
 *    REG_VOUT_FS
 *       FB set to Internal (Default Value)
 *       INTFB (internal feedback ratio) 0.0564 (0x11) (Default Value)
 *
 *  TODO: Enable interrupt fault handler
 */
#include <Wire.h>
#include "bond_vdut.h"
#include "bond_board.h"
#include "bond_pins.h"
#include "rpc_helpers.h"
#include "src/oled/bond_oled.h"

#define I2C_ADDR                  0x75
#define RESET_HOLD_MS             5

#define REG_VREF                  0x0
#define REG_IOUT_LIMIT            0x2
#define REG_VOUT_SR               0x3  // slew rate
#define REG_VOUT_FS               0x4  // feedback selection
#define REG_CDC                   0x5  // cable compensation
#define REG_MODE                  0x6
#define REG_STATUS                0x7

#define REG_STATUS_DEFAULT        0x1
#define REG_MODE_DEFAULT          0x32 // output disabled, freq unchanged, hiccup
                                       // discharge, FPWM
#define REG_MODE_OE               0x80

#define REG_STATUS_SCP            0x80  // short circuit protection
#define REG_STATUS_OCP            0x40  // over current protection
#define REG_STATUS_OVP            0x20  // over voltage protection
#define REG_STATUS_MODE_MASK      0x03
#define REG_STATUS_BOOST          0x00  // operating boost
#define REG_STATUS_BUCK           0x01  // operating buck
#define REG_STATUS_BUCKBOOST      0x02  // operating buckbost

#define VDUT_TOL_MV               25
#define VDUT_SETTLE_MS            10

static char buf[LINE_MAX_LENGTH];

static int _i2c_write(const uint8_t *data, uint8_t len) {
  Wire.beginTransmission(I2C_ADDR);
  Wire.write(data, len);
  return Wire.endTransmission();
}

static int _read_reg(uint8_t reg, uint8_t *value) {
  int rc = _i2c_write(&reg, 1);
  if (rc) return rc;
  if (Wire.requestFrom(I2C_ADDR, 1) != 1 || !Wire.available()) return -1;
  *value = Wire.read();
  return 0;
}

static int _write_reg(uint8_t reg, uint8_t value) {
  uint8_t data[] = {reg, value};
  return _i2c_write(data, sizeof(data));
}

static int _vdut_oe(bool en) {
  return _write_reg(REG_MODE, REG_MODE_DEFAULT | (en ? REG_MODE_OE : 0));
}

static void _vdut_hw_reset(void) {
  // toggle EN pin to reset
  digitalWrite(VDUT_SMPS_EN_PIN, LOW);
  delay(RESET_HOLD_MS);
  digitalWrite(VDUT_SMPS_EN_PIN, HIGH);
  delay(RESET_HOLD_MS);
}

/* vdut_set_mv
 * - don't operate near the buck/boost switching point, ~15V for BOND, max is 9V so ok
 * - From TPS55289 DS
 *     VOUT = VREF / INTERNAL_FEEDBACK, INTERNAL_FEEDBACK = 0.0564
 *     VREF_SETTING = ((VOUT * INTFB) - VREF_MIN) / VREF_STEP_SIZE = (VOUT * 0.0564 - 0.045) / 0.000564
 *     in mV, rounded: (mV - 798 + 5) / 10
 * - mv must already be in range VDUT_MIN_MV..VDUT_MAX_MV
 */
int vdut_set_mv(uint16_t mv) {
  uint16_t vref = (mv - 798 + 5) / 10;
  uint8_t data[] = {REG_VREF, (uint8_t)(vref & 0xFF), (uint8_t)((vref >> 8) & 0x7)};
  int rc = _i2c_write(data, sizeof(data));
  if (rc) {
    snprintf(buf, LINE_MAX_LENGTH, "vdut i2c %d", rc);
    oled_print(OLED_LINE_DEBUG, buf, true);
    return -1;
  }
  return 0;
}

void vdut_connect(bool assert) {
  digitalWrite(VDUT_CONNECT_PIN, assert ? HIGH : LOW);
}

/* vdut_init
 * - reset the TPS55289, confirm it answers, lowest slew rate, enable the output
 */
int vdut_init(void) {
  uint8_t status = 0;
  _vdut_hw_reset();

  if (_read_reg(REG_STATUS, &status)) {
    oled_print(OLED_LINE_DEBUG, "vdut status read", true);
    return -1;
  }
  if (status != REG_STATUS_DEFAULT) {
    snprintf(buf, LINE_MAX_LENGTH, "vdut status %x", status);
    oled_print(OLED_LINE_DEBUG, buf, true);
    return -1;
  }
  // lowest slew rate, there is a large cap to charge and we don't want excessive current
  if (_write_reg(REG_VOUT_SR, 0) || _write_reg(REG_MODE, REG_MODE_DEFAULT) || _vdut_oe(true)) {
    oled_print(OLED_LINE_DEBUG, "vdut init write", true);
    return -1;
  }
  return 0;
}

String vdut_set(uint16_t mv) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API

  if (mv > VDUT_MAX_MV) return rpc_error(doc, "invalid arg exceeds maximum");
  if (mv < VDUT_MIN_MV) return rpc_error(doc, "invalid arg below minimum");
  if (vdut_set_mv(mv)) return rpc_error(doc, "TPS55289 i2c write");

  delay(VDUT_SETTLE_MS);
  uint16_t measured_mv = ina226_read_mv(ina226_vdut);
  doc["result"]["mv"] = mv;
  doc["result"]["measured_mv"] = measured_mv;

  snprintf(buf, LINE_MAX_LENGTH, "vdut %u %u mV", mv, measured_mv);
  if (measured_mv > mv + VDUT_TOL_MV || measured_mv < mv - VDUT_TOL_MV) {
    oled_print(OLED_LINE_DEBUG, buf, true);
    return rpc_error(doc, "set vdut beyond tolerance limit");
  }
  oled_print(OLED_LINE_DEBUG, buf, false);
  return rpc_response(doc);  // always the last line of RPC API
}

/* vdut_read
 *  - VDUT INA226 bus voltage (V) and current (mA)
 */
String vdut_read(void) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API

  ina226_vdut.startSingleMeasurement();
  doc["result"]["v"] = ina226_vdut.getBusVoltage_V();
  doc["result"]["ima"] = ina226_vdut.getCurrent_mA();
  return rpc_response(doc);  // always the last line of RPC API
}

/* vdut_con
 *  - set VDUT_EN pin, active (asserted) HIGH, connects VDUT to the DUT
 */
String vdut_con(bool assert) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API
  vdut_connect(assert);
  doc["result"]["assert"] = assert;
  doc["result"]["level"] = assert;
  return rpc_response(doc);  // always the last line of RPC API
}

/* vdut_en
 *  - set VDUTSMPS_EN pin, active (asserted) HIGH, enables TPS55289
 */
String vdut_en(bool assert) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API
  digitalWrite(VDUT_SMPS_EN_PIN, assert ? HIGH : LOW);
  doc["result"]["assert"] = assert;
  doc["result"]["level"] = assert;
  return rpc_response(doc);  // always the last line of RPC API
}

/* vdut_get_fault
 *  - TPS55289 status register faults and operating mode
 */
String vdut_get_fault(void) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API

  uint8_t status = 0;
  if (_read_reg(REG_STATUS, &status)) return rpc_error(doc, "TPS55289 i2c read");

  doc["result"]["short_protection"] = (status & REG_STATUS_SCP) != 0;
  doc["result"]["over_current_protection"] = (status & REG_STATUS_OCP) != 0;
  doc["result"]["over_voltage_protection"] = (status & REG_STATUS_OVP) != 0;
  switch (status & REG_STATUS_MODE_MASK) {
    case REG_STATUS_BOOST:     doc["result"]["mode"] = "boost"; break;
    case REG_STATUS_BUCK:      doc["result"]["mode"] = "buck"; break;
    case REG_STATUS_BUCKBOOST: doc["result"]["mode"] = "buck_boost"; break;
    default:                   doc["result"]["mode"] = "unknown"; break;
  }
  return rpc_response(doc);  // always the last line of RPC API
}

String vdut_reset(void) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API
  if (vdut_init()) return rpc_error(doc, "vdut_init failed");
  return rpc_response(doc);  // always the last line of RPC API
}
