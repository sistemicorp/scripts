/*
 * bond_vdut.c
 *
 *  Created on: october 15, 2025
 *      Author: Sistemi Corp, Copyright 2023, all rights reserved
 *      Author: martin
 *
 * Operation:
 * 1. TPS55289 Settings
 *    REG_VOUT_FS
 *       FB set to Internal (Default Value)
 *       INTFB (internal feedback ratio) 0.0564 (0x11) (Default Value)
 * 2. P1150 should be disconnected from the load when VMAIN is
 *    enabled.
 *
 * TODO: Enable interrupt fault handler
 *
 */
#include <Wire.h>
#include "src/oled/bond_oled.h"

#define I2C_ADDR                  0x75
#define I2C_TIMEOUT               50
#define RESET_HOLD_TICS           5
#define RESET_POST_TICS           5

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

#define REG_STATUS_SCP            0x80  // short circuit protection
#define REG_STATUS_OCP            0x40  // over current protection
#define REG_STATUS_OVP            0x20  // over voltage protection
#define REG_STATUS_BOOST          0x00  // operating boost
#define REG_STATUS_BUCK           0x01  // operating buck
#define REG_STATUS_BUCKBOOST      0x02  // operating buckbost

#define VDUT_MAX_MV               9000
#define VDUT_MIN_MV               1000
#define VDUT_TOL_MV                 25

typedef struct {
	uint8_t data_set[3];
	uint8_t data_oe[2];
  uint16_t vmain_set_mv;
	uint16_t vmain_set_vref;
  char buf[LINE_MAX_LENGTH];
} _vdut_ctx_t;
static _vdut_ctx_t vdut_ctx;

static int _i2c_writer(uint8_t *buf, uint16_t s) {
  Wire.beginTransmission(I2C_ADDR);
  for(uint16_t i=0; i<s; i++) {
    Wire.write((char)buf[i]);
  }
  return Wire.endTransmission();
}

static int _i2c_reader(uint8_t *buf, uint16_t s) {
  Wire.requestFrom(I2C_ADDR, s); 
  uint16_t idx = 0;
  while (Wire.available() && idx < s) { 
    char c = Wire.read(); // Read a byte
    buf[idx] = (uint8_t)c;
    idx++;
  }
  return 0;
}

static uint16_t _vdut_mv(void) {
    ina226_vdut.startSingleMeasurement();
    float tmp = ina226_vdut.getBusVoltage_V();
    return (uint16_t)(tmp * 1000.0f);
}

int _vdut_set(uint16_t mv) {
	// don't operate near the buck/boost switching point
	// which is ~15V for BOND, given max voltage is 9V, should be good.
	/* From TPS55289 DS
	 * VOUT = VREF / INTERNAL_FEEDBACK
	 * INTERNAL_FEEDBACK = 0.0564
	 * VREF STEP SIZE = 0.000564
	 * VREF = VOUT * INTFB
	 * VREF_SETTING = (VREF - VREF_MIN) / VREF_STEP_SIZE = (VREF - 0.045) / 0.000564
	 * VREF_SETTING = ((VOUT * INTFB) - VREF_MIN) / VREF_STEP_SIZE
	 * ...then use milli-Volts... and integer friendly form
	 */
	vdut_ctx.vmain_set_mv = mv;
	vdut_ctx.vmain_set_vref = (mv - 798 + 5) / 10;
  snprintf(vdut_ctx.buf, LINE_MAX_LENGTH, "tps55289 %u %u", vdut_ctx.vmain_set_vref, mv);
  oled_print(OLED_LINE_DEBUG, vdut_ctx.buf, false);

  uint8_t data_set[3];
  data_set[0] = REG_VREF;
  data_set[1] = vdut_ctx.vmain_set_vref & 0xFF;
  data_set[2] = (vdut_ctx.vmain_set_vref >> 8) & 0x7;
  int rc = _i2c_writer(data_set, 3);
  if (rc) {
    snprintf(vdut_ctx.buf, LINE_MAX_LENGTH, "i2cwrite %d ln%d", rc, __LINE__);
    oled_print(OLED_LINE_DEBUG, vdut_ctx.buf, true); 
    return -1;
  }
  return 0;
}

String vdut_set(uint16_t mv) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API

	if (mv > VDUT_MAX_MV) {
    snprintf(vdut_ctx.buf, LINE_MAX_LENGTH, "vdut_set:%u > %u", mv, VDUT_MAX_MV);
    oled_print(OLED_LINE_DEBUG, vdut_ctx.buf, true);

    snprintf(vdut_ctx.buf, LINE_MAX_LENGTH, "%s %u mV", __func__, mv);
    oled_print(OLED_LINE_RPC, vdut_ctx.buf, true);
    doc["success"] = false;
    doc["result"]["error"] = "invalid arg exceeds maximum";    
    return _response(doc);  // always the last line of RPC API
	}

	if (mv < VDUT_MIN_MV) {
    snprintf(vdut_ctx.buf, LINE_MAX_LENGTH, "vdut_set:%u < %u", mv, VDUT_MIN_MV);
    oled_print(OLED_LINE_DEBUG, vdut_ctx.buf, true);

    snprintf(vdut_ctx.buf, LINE_MAX_LENGTH, "%s %u mV", __func__, mv);
    oled_print(OLED_LINE_RPC, vdut_ctx.buf, true);
    doc["success"] = false;
    doc["result"]["error"] = "invalid arg exceeds minmum";    
    return _response(doc);  // always the last line of RPC API
	}

  int rc = _vdut_set(mv);
  if (rc) {
    snprintf(vdut_ctx.buf, LINE_MAX_LENGTH, "_vdut_set %d ln%d", rc, __LINE__);
    oled_print(OLED_LINE_DEBUG, vdut_ctx.buf, true); 
    doc["success"] = false;
    doc["result"]["error"] = vdut_ctx.buf;      
    return _response(doc);  // always the last line of RPC API
  }

  delay(10);  // allow to settle
  uint16_t vdut_mv = _vdut_mv();
  doc["result"]["mv"] = mv;
  doc["result"]["measured_mv"] = vdut_mv;

  if (vdut_mv > mv + VDUT_TOL_MV || vdut_mv < mv - VDUT_TOL_MV) {
    snprintf(vdut_ctx.buf, LINE_MAX_LENGTH, "vdut tol %u %u", mv, vdut_mv);
    oled_print(OLED_LINE_DEBUG, vdut_ctx.buf, true);      
    doc["success"] = false;
    doc["result"]["error"] = "set vdut beyond tolerance limit";      
    return _response(doc);  // always the last line of RPC API
  }
  snprintf(vdut_ctx.buf, LINE_MAX_LENGTH, "vdut %u %u mV", mv, vdut_mv);
  oled_print(OLED_LINE_DEBUG, vdut_ctx.buf, false);  

  snprintf(vdut_ctx.buf, LINE_MAX_LENGTH, "%s %u/%u", __func__, mv, vdut_mv);
  oled_print(OLED_LINE_RPC, vdut_ctx.buf, false);
  return _response(doc);  // always the last line of RPC API
}

/* @brief VDUT (TPS55289) output Enable
 */
int _vdut_oe(bool en) {
  vdut_ctx.data_oe[0] = REG_MODE;
  vdut_ctx.data_oe[1] = REG_MODE_DEFAULT;
  if (en) vdut_ctx.data_oe[1] |= 0x80;
  int rc = _i2c_writer(vdut_ctx.data_oe, 2);
  return rc;
}

/* @brief VDUT (TPS55289) output Enable
 * - this is not BOND's header output enable, this is the TPS55289 OE
 *   and its enabled by default during vdut_init().
 * - TODO: this api may be removed in the future...? Because BOND has a separate 
 *         FET for connection.
 */
String vdut_oe(bool oe) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  int rc = _vdut_oe(oe);
  if (rc) {
    snprintf(vdut_ctx.buf, LINE_MAX_LENGTH, "%s %u", __func__, oe);
    oled_print(OLED_LINE_RPC, vdut_ctx.buf, true);

    snprintf(vdut_ctx.buf, LINE_MAX_LENGTH, "error code %d", rc);
    oled_print(OLED_LINE_DEBUG, vdut_ctx.buf, true);

    doc["success"] = false;
    doc["result"]["error"] = "error code TODO";   
    return _response(doc);  // always the last line of RPC API    
  }

  snprintf(vdut_ctx.buf, LINE_MAX_LENGTH, "%s", __func__);
  oled_print(OLED_LINE_RPC, vdut_ctx.buf, false);
  return _response(doc);  // always the last line of RPC API
}


/* @brief VDUT (TPS55289) read faults
 */
String vdut_get_fault(void) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API

  uint8_t data[] = {REG_STATUS};
  int rc = _i2c_writer(data, 1);
  if (rc) {
    snprintf(vdut_ctx.buf, LINE_MAX_LENGTH, "i2cwrite %d %d", rc, __LINE__);
    oled_print(OLED_LINE_DEBUG, vdut_ctx.buf, true);    
    doc["success"] = false;
    doc["result"]["error"] = "_i2c_writer error code TODO";      
    return _response(doc);  // always the last line of RPC API
  }
  rc = _i2c_reader(data, 1);
  if (rc) {
    snprintf(vdut_ctx.buf, LINE_MAX_LENGTH, "i2c read %d", rc);
    oled_print(OLED_LINE_DEBUG, vdut_ctx.buf, true);  
    doc["success"] = false;
    doc["result"]["error"] = "_i2c_reader error code TODO";      
    return _response(doc);  // always the last line of RPC API
  }
  if (data[0] & REG_STATUS_SCP) {
    doc["result"]["short_protection"] = "True";
  } else {
    doc["result"]["short_protection"] = "False";
  }
  if (data[0] & REG_STATUS_OCP) {
    doc["result"]["over_current_protection"] = "True";
  } else {
    doc["result"]["over_current_protection"] = "False";
  }
  if (data[0] & REG_STATUS_OVP) {
    doc["result"]["over_voltage_protection"] = "True";
  } else {
    doc["result"]["over_voltage_protection"] = "False";
  }
  if ((data[0] & 0x03) == REG_STATUS_BOOST) {
    doc["result"]["mode_boost"] = "True";
  } else if ((data[0] & 0x03) == REG_STATUS_BUCK) {
    doc["result"]["mode_buck"] = "True";
  } else if ((data[0] & 0x03) == REG_STATUS_BUCKBOOST) {
    doc["result"]["mode_buck_boost"] = "True";
  } else {
    doc["result"]["mode_unknown"] = "True";
  }

  snprintf(vdut_ctx.buf, LINE_MAX_LENGTH, "%s", __func__);
  oled_print(OLED_LINE_RPC, vdut_ctx.buf, false);
  return _response(doc);  // always the last line of RPC API
}

/* @brief VDUT (TPS55289) Reset
 */
static void _vdut_reset(void) {
  // toggle EN pin to reset
  digitalWrite(VDUT_SMPS_EN_PIN, LOW);
  delay(5);
  digitalWrite(VDUT_SMPS_EN_PIN, HIGH);
  delay(5);
}

/* Init VDUT (See SCH), TPS55289
 *
 */
int vdut_init(void) {
  int rc = 0;
	_vdut_reset();

  // read status register to confirm communication
  {
    uint8_t data[] = {REG_STATUS};
    int rc = _i2c_writer(data, 1);
    if (rc) {
      snprintf(vdut_ctx.buf, LINE_MAX_LENGTH, "i2cwrite %d %d", rc, __LINE__);
      oled_print(OLED_LINE_DEBUG, vdut_ctx.buf, true);    
      goto fail;
    }
    rc = _i2c_reader(data, 1);
    if (rc) {
      snprintf(vdut_ctx.buf, LINE_MAX_LENGTH, "i2c read %d", rc);
      oled_print(OLED_LINE_DEBUG, vdut_ctx.buf, true);  
      goto fail;
    }

    if (REG_STATUS_DEFAULT != data[0]) {
      snprintf(vdut_ctx.buf, LINE_MAX_LENGTH, "status %x", data[0]);
      oled_print(OLED_LINE_DEBUG, vdut_ctx.buf, true);
      goto fail;
    }
  }

  {
    // use lowest slew rate, there is a large cap to charge and we don't want excessive current
    uint8_t data_sr[] = {REG_VOUT_SR, 0};
    rc = _i2c_writer(data_sr, 2);
    if (rc) {
      snprintf(vdut_ctx.buf, LINE_MAX_LENGTH, "i2cwrite %d %d", rc, __LINE__);
      oled_print(OLED_LINE_DEBUG, vdut_ctx.buf, true);    
      goto fail;
    }
  }

  {
    uint8_t data_mode[] = {REG_MODE, REG_MODE_DEFAULT};
    rc = _i2c_writer(data_mode, 2);
    if (rc) {
      snprintf(vdut_ctx.buf, LINE_MAX_LENGTH, "i2cwrite %d %d", rc, __LINE__);
      oled_print(OLED_LINE_DEBUG, vdut_ctx.buf, true);    
      goto fail;
    }
  }

  rc = _vdut_oe(true);
  if (rc) {
    goto fail;
  }

  snprintf(vdut_ctx.buf, LINE_MAX_LENGTH, "vdut_init done", rc, __LINE__);
  oled_print(OLED_LINE_DEBUG, vdut_ctx.buf, false);   
  return 0;

fail:
  snprintf(vdut_ctx.buf, LINE_MAX_LENGTH, "%s", __func__);
  oled_print(OLED_LINE_RPC, vdut_ctx.buf, true);
  return -1;
}

String vdut_reset(void) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  _vdut_reset();
  if (vdut_init()) {
    snprintf(vdut_ctx.buf, LINE_MAX_LENGTH, "%s", __func__);
    oled_print(OLED_LINE_RPC, vdut_ctx.buf, true);
    doc["success"] = false;
    doc["result"]["error"] = "vdut_init failed";  
    return _response(doc);  // always the last line of RPC API
  }
  snprintf(vdut_ctx.buf, LINE_MAX_LENGTH, "%s", __func__);
  oled_print(OLED_LINE_RPC, vdut_ctx.buf, false);
  return _response(doc);  // always the last line of RPC API
}
