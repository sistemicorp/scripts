/*  Sistemi Corporation, copyright, all rights reserved, 2021-2026
 *  Martin Guthrie
 *
 *  BOND reset (DUT safe state) and power up self test, see bond_selftest.h
 */
#include "bond_selftest.h"
#include "battemu.h"
#include "bond_board.h"
#include "bond_max_hdr.h"
#include "bond_max_iox.h"
#include "bond_vdut.h"
#include "rpc_helpers.h"
#include "src/oled/bond_oled.h"

#define SELF_TEST_LOAD_OHMS      200.0f
#define SELF_TEST_V_TOL          0.05f
#define SELF_TEST_MA_TOL         1.0f
#define SELF_TEST_MA_NOLOAD_MAX  0.5f
#define SELF_TEST_SETTLE_MS      100

/* bond_reset
 * - DUT safe state, called on setup() and by the reset RPC (start and end of each test)
 * - VDUT and VBAT disconnected, self test load off, header DACs 0V, header GPOs idle
 * - VDUT and VBAT voltages are not changed, they are disconnected from the DUT
 */
void bond_reset(void) {
  vdut_connect(false);
  iox_set(IOX_PORT_VBAT_CON, false);
  iox_set(IOX_PORT_SELFTEST, false);
  max_hdr_reset_outputs();
}

/* reset
 *  - DOES NOT RESET TEENSY, sets BOND to the DUT safe state, see bond_reset()
 */
String reset(void) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API
  bond_reset();
  return rpc_response(doc);  // always the last line of RPC API
}

static bool _in_tol(float value, float expected, float tol) {
  return value <= expected + tol && value >= expected - tol;
}

/* _check_supply
 * - measure an INA226 with no load, then with the self test load connected
 * - connect: connects the supply to the self test node
 */
static int _check_supply(INA226_WE &ina, const char *name, uint16_t mv, void (*connect)(bool)) {
  char buf[LINE_MAX_LENGTH];
  float vf = mv / 1000.0f;

  ina.startSingleMeasurement();
  float v = ina.getBusVoltage_V();
  float ma = ina.getCurrent_mA();
  snprintf(buf, LINE_MAX_LENGTH, "%s1 %.2f %.2f %.2f", name, vf, v, ma);
  if (!_in_tol(v, vf, SELF_TEST_V_TOL) || ma > SELF_TEST_MA_NOLOAD_MAX) {
    oled_print(OLED_LINE_DEBUG, buf, true);
    return -1;
  }
  oled_print(OLED_LINE_DEBUG, buf, false);

  iox_set(IOX_PORT_SELFTEST, true);
  connect(true);
  ina.startSingleMeasurement();
  v = ina.getBusVoltage_V();
  ma = ina.getCurrent_mA();
  connect(false);
  iox_set(IOX_PORT_SELFTEST, false);

  float ma_expected = (vf / SELF_TEST_LOAD_OHMS) * 1000.0f;
  snprintf(buf, LINE_MAX_LENGTH, "%s2 %.2f %.2f %.2f", name, v, ma, ma_expected);
  if (!_in_tol(v, vf, SELF_TEST_V_TOL) || !_in_tol(ma, ma_expected, SELF_TEST_MA_TOL)) {
    oled_print(OLED_LINE_DEBUG, buf, true);
    return -1;
  }
  oled_print(OLED_LINE_DEBUG, buf, false);
  return 0;
}

static void _vbat_connect(bool assert) {
  iox_set(IOX_PORT_VBAT_CON, assert);
}

/* bond_self_test
 *  - measures VDUT and VBAT, unloaded and with the SELF_TEST load, to confirm operation
 *  - always leaves BOND in the reset state
 */
int bond_self_test(void) {
  static const uint16_t vdut_voltages[] = {2000, 4000, 6000, 8000};
  static const uint16_t vbat_voltages[] = {2000, 4000};
  int rc = 0;

  for (uint16_t mv : vdut_voltages) {
    if (vdut_set_mv(mv)) { rc = -1; break; }
    delay(SELF_TEST_SETTLE_MS);
    if (_check_supply(ina226_vdut, "vdut", mv, vdut_connect)) { rc = -1; break; }
  }

  for (uint16_t mv : vbat_voltages) {
    if (rc) break;
    uint16_t measured_mv = 0;
    if (battemu_set_mv(mv, &measured_mv)) {
      oled_print(OLED_LINE_DEBUG, "vbat set err", true);
      rc = -1;
      break;
    }
    if (_check_supply(ina226_vbat, "vbat", mv, _vbat_connect)) { rc = -1; break; }
  }

  bond_reset();
  return rc;
}
