/*  Sistemi Corporation, copyright, all rights reserved, 2023
 *  Martin Guthrie
 *
 *  Battery Emulator the BOND design, a4401.
 *  VBAT output depends on the LTM8052 ADJ pin resistors.uint16_t.uint16_t
 *  Here 5.1k & 5.1k were used.
 *
*/
#include "bond_max_iox.h"
#include "src/oled/bond_oled.h"

//extern int8_t oled_buf[OLED_WIDTH * OLED_HEIGHT / 8];

#define VBAT_START_MV     500
#define VBAT_STOP_MV      5500
#define VBAT_STEP_MV      50
#define VBAT_TOLERANCE_MV 10
#define LUT_NUM_ENTRIES   ((VBAT_STOP_MV - VBAT_START_MV) / VBAT_STEP_MV + 1)


typedef struct {
   uint16_t dac;      // digital setting
   uint16_t vbat_mv;
} _lut_t;

typedef struct {
    _lut_t _lut[LUT_NUM_ENTRIES];
    bool cal_done;

    uint16_t vbat_mv;
    bool vbat_connect;
} _ctx_t;
static _ctx_t ctx;

uint16_t _vbat_mv(void) {
    ina219_vbat.startSingleMeasurement();
    float tmp = ina219_vbat.getBusVoltage_V();
    return (uint16_t)(tmp * 1000.0f);
}


int battemu_init(void) {
    uint16_t dac_value = 1600;
    char buf[LINE_MAX_LENGTH];

    if (ctx.cal_done) return 0;

    iox_vbat_en(true);
    delay(12);  // TODO: measure this

    // create LUT for output
    for (int i = 0; i < LUT_NUM_ENTRIES; i++) {
        ctx._lut[i].vbat_mv = VBAT_START_MV + i * VBAT_STEP_MV;

        while (true) {
            max_hdr1.single_ended_dac_write(MAX11300::PIXI_PORT9, dac_value);
            delay(10);
            uint16_t vbat = _vbat_mv();

            if (vbat > ctx._lut[i].vbat_mv) {
                ctx._lut[i].dac = dac_value;
                dac_value -= 4;
                if (ctx._lut[i].vbat_mv % 500 == 0) {
                    snprintf(buf, LINE_MAX_LENGTH, "bemu: %4u %4u mV", dac_value, vbat);
                    oled_print(OLED_LINE_DEBUG, buf, false);
                }
                break;
            }
            dac_value -= 2;
        }
    }

    ctx.vbat_mv = ctx._lut[0].vbat_mv;
    max_hdr1.single_ended_dac_write(MAX11300::PIXI_PORT9, ctx._lut[0].dac);
    ctx.vbat_connect = false;

    ctx.cal_done = true;
    return 0;
}

String vbat_set(uint16_t mv) {
    DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API

    char _buf[LINE_MAX_LENGTH];
    if (!ctx.cal_done) {
        snprintf(_buf, LINE_MAX_LENGTH, "%s init", __func__);
        oled_print(OLED_LINE_RPC, _buf, true);
        doc["success"] = false;
        doc["result"]["error"] = "init/cal not done";
        return _response(doc);  // always the last line of RPC API
    }

    if (mv % VBAT_STEP_MV != 0 || mv > VBAT_STOP_MV || mv < VBAT_START_MV) {
        snprintf(_buf, LINE_MAX_LENGTH, "%s %u", __func__, mv);
        oled_print(OLED_LINE_RPC, _buf, true);
        doc["success"] = false;
        doc["result"]["error"] = "invalid argument";
        return _response(doc);  // always the last line of RPC API
    }

    int i = 0;
    for (i = 0; i < LUT_NUM_ENTRIES; i++) {
        if (mv == ctx._lut[i].vbat_mv) break;
    }
    if (i == LUT_NUM_ENTRIES) {
        snprintf(_buf, LINE_MAX_LENGTH, "%s idx %u", __func__, i);
        oled_print(OLED_LINE_RPC, _buf, true);
        doc["success"] = false;
        doc["result"]["error"] = "index";
        return _response(doc);  // always the last line of RPC API
    }

    max_hdr1.single_ended_dac_write(MAX11300::PIXI_PORT9, ctx._lut[i].dac);
    delay(50);
    uint16_t vbat = _vbat_mv();
    snprintf(_buf, LINE_MAX_LENGTH, "%s %u mV", __func__, vbat);
    oled_print(OLED_LINE_RPC, _buf, false);

    doc["result"]["mv"] = mv;
    doc["result"]["measured_mv"] = vbat;
    doc["result"]["i"] = i;
    doc["result"]["dac"] = ctx._lut[i].dac;
    return _response(doc);  // always the last line of RPC API
}
