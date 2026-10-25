/*  Sistemi Corporation, copyright, all rights reserved, 2023-2026
 *  Martin Guthrie
 *
 *  Battery Emulator, see battemu.h
 *  VBAT output depends on the LTM8052 ADJ pin resistors, 5.1k & 5.1k were used.
 */
#include "battemu.h"
#include "bond_board.h"
#include "bond_max_iox.h"
#include "rpc_helpers.h"
#include "src/oled/bond_oled.h"

#define VBAT_TOLERANCE_MV      50  // same as the power up self test
#define LUT_NUM_ENTRIES        ((VBAT_STOP_MV - VBAT_START_MV) / VBAT_STEP_MV + 1)
#define DEBUG_LUT_ENTRIES      10  // not all the LUT fits in an RPC response

// See DDR - cannot use value that results in output less than 1.19V
#define BATTEMU_DAC_START      800  // 800 maps to ~1.43V with R36=5.1K, R34=6.8K
#define BATTEMU_DAC_STEP       1
#define BATTEMU_DAC_NEXT_STEP  6
#define BATTEMU_SETTLE_MS      4
#define VBAT_SETTLE_MS         50

typedef struct {
  uint16_t dac;      // digital setting
  uint16_t vbat_mv;
} _lut_t;

typedef struct {
  _lut_t lut[LUT_NUM_ENTRIES];
  bool cal_done;
} _batt_ctx_t;
static _batt_ctx_t batt_ctx;

/* battemu_init
 * - build the DAC to VBAT LUT
 * - as the DAC value goes down, the battery emulator voltage goes up
 */
int battemu_init(void) {
  uint16_t dac_value = BATTEMU_DAC_START;
  char buf[LINE_MAX_LENGTH];
  int rc = 0;

  batt_ctx.cal_done = false;
  iox_set(IOX_PORT_VBAT_CON, false);
  iox_set(IOX_PORT_VBAT_EN, true);
  delay(BATTEMU_SETTLE_MS * 2);

  for (int i = 0; i < LUT_NUM_ENTRIES && rc == 0; i++) {
    batt_ctx.lut[i].vbat_mv = VBAT_START_MV + i * VBAT_STEP_MV;

    // stop when VBAT goes just above the desired value
    while (true) {
      max_iox.single_ended_dac_write(IOX_PORT_VBAT_ADJ, dac_value);
      delay(BATTEMU_SETTLE_MS);
      if (ina226_read_mv(ina226_vbat) > batt_ctx.lut[i].vbat_mv) {
        batt_ctx.lut[i].dac = dac_value;
        break;
      }
      if (dac_value <= BATTEMU_DAC_STEP) {
        snprintf(buf, LINE_MAX_LENGTH, "bemu E1: %u mV", batt_ctx.lut[i].vbat_mv);
        oled_print(OLED_LINE_DEBUG, buf, true);
        rc = -1;
        break;
      }
      dac_value -= BATTEMU_DAC_STEP;
    }
    if (rc) break;

    snprintf(buf, LINE_MAX_LENGTH, "bemu: %4u %4u mV", dac_value, batt_ctx.lut[i].vbat_mv);
    oled_print(OLED_LINE_DEBUG, buf, false);

    // the next point is at least BATTEMU_DAC_NEXT_STEP away
    if (i < LUT_NUM_ENTRIES - 1) {
      if (dac_value <= BATTEMU_DAC_NEXT_STEP) {
        snprintf(buf, LINE_MAX_LENGTH, "bemu E2: %u mV", batt_ctx.lut[i].vbat_mv);
        oled_print(OLED_LINE_DEBUG, buf, true);
        rc = -1;
        break;
      }
      dac_value -= BATTEMU_DAC_NEXT_STEP;
    }
  }

  // leave the battery emulator set to a low voltage
  max_iox.single_ended_dac_write(IOX_PORT_VBAT_ADJ, BATTEMU_DAC_START);
  delay(BATTEMU_SETTLE_MS);

  if (rc) return rc;
  batt_ctx.cal_done = true;
  return 0;
}

/* battemu_set_mv
 * - set VBAT, mv is VBAT_START_MV..VBAT_STOP_MV in VBAT_STEP_MV steps
 * - return 0, -1 not calibrated, -2 invalid mv, -3 measured out of tolerance
 */
int battemu_set_mv(uint16_t mv, uint16_t *measured_mv) {
  if (!batt_ctx.cal_done) return -1;
  if (mv % VBAT_STEP_MV != 0 || mv > VBAT_STOP_MV || mv < VBAT_START_MV) return -2;

  int i = (mv - VBAT_START_MV) / VBAT_STEP_MV;
  max_iox.single_ended_dac_write(IOX_PORT_VBAT_ADJ, batt_ctx.lut[i].dac);
  delay(VBAT_SETTLE_MS);
  *measured_mv = ina226_read_mv(ina226_vbat);

  if (*measured_mv > mv + VBAT_TOLERANCE_MV || *measured_mv < mv - VBAT_TOLERANCE_MV) return -3;
  return 0;
}

/* bond_batt_emu_cal
 * - repeat the battery emulator calibration (setup() already did one)
 */
String bond_batt_emu_cal(void) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API
  if (battemu_init()) return rpc_error(doc, "battemu_init");
  return rpc_response(doc);  // always the last line of RPC API
}

String vbat_set(uint16_t mv) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API
  char buf[LINE_MAX_LENGTH];

  uint16_t measured_mv = 0;
  int rc = battemu_set_mv(mv, &measured_mv);
  if (rc == -1) return rpc_error(doc, "init/cal not done");
  if (rc == -2) return rpc_error(doc, "1500 <= mv <= 5000, multiple of 50");

  doc["result"]["mv"] = mv;
  doc["result"]["measured_mv"] = measured_mv;

  snprintf(buf, LINE_MAX_LENGTH, "vbat %u %u mV", mv, measured_mv);
  oled_print(OLED_LINE_DEBUG, buf, rc != 0);
  if (rc == -3) return rpc_error(doc, "set vbat beyond tolerance limit");
  return rpc_response(doc);  // always the last line of RPC API
}

/* vbat_read
 *  - VBAT INA226 bus voltage (V) and current (mA)
 */
String vbat_read(void) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API

  ina226_vbat.startSingleMeasurement();
  doc["result"]["v"] = ina226_vbat.getBusVoltage_V();
  doc["result"]["ima"] = ina226_vbat.getCurrent_mA();
  return rpc_response(doc);  // always the last line of RPC API
}

// return the first DEBUG_LUT_ENTRIES of the battery emulator LUT
String debug_batt_emu(void) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API

  JsonArray vbat = doc["result"]["vbat"].to<JsonArray>();
  JsonArray dac = doc["result"]["dac"].to<JsonArray>();
  for (int i = 0; i < DEBUG_LUT_ENTRIES; i++) {
    vbat.add(batt_ctx.lut[i].vbat_mv);
    dac.add(batt_ctx.lut[i].dac);
  }
  return rpc_response(doc);  // always the last line of RPC API
}
