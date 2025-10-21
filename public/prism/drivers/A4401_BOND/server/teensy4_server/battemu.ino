/*  Sistemi Corporation, copyright, all rights reserved, 2023-2025
 *  Martin Guthrie
 *
 *  Battery Emulator the BOND design, a4401.
 *  VBAT output depends on the LTM8052 ADJ pin resistors.uint16_t.uint16_t
 *  Here 5.1k & 5.1k were used.
 *
*/
#include "bond_max_iox.h"
#include "src/oled/bond_oled.h"

#define VBAT_START_MV     1500
#define VBAT_STOP_MV      5000
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
} _batt_ctx_t;
static _batt_ctx_t batt_ctx;

static uint16_t _vbat_mv(void) {
    ina219_vbat.startSingleMeasurement();
    float tmp = ina219_vbat.getBusVoltage_V();
    return (uint16_t)(tmp * 1000.0f);
}

                                     // See DDR - cannot use value that results in output less than 1.19V
#define BATTEMU_DAC_START      800  // 800 maps to ~1.43V with R36=5.1K, R34=6.8K
#define BATTEMU_DAC_STEP       1
#define BATTEMU_DAC_NEXT_STEP  6
#define BATTEMU_SETTLE_MS      4
int battemu_init(void) {
    uint16_t dac_value = BATTEMU_DAC_START;
    char buf[LINE_MAX_LENGTH];
    bool error_set = false;

    if (batt_ctx.cal_done) return 0;

    iox_vbat_con(false);
    iox_vbat_en(true);
    delay(BATTEMU_SETTLE_MS * 2);  // TODO: measure this

    // DEBUG: if you are debugging, use vbat_set() DEBUG note to
    // set an specific DAC value, and then return early here.
    //return 0;

    // NOTE: As the DAC value goes down, the battery emulator voltage goes up

    // create LUT for output
    for (int i = 0; i < LUT_NUM_ENTRIES; i++) {
        if (error_set) break;

        batt_ctx._lut[i].vbat_mv = VBAT_START_MV + i * VBAT_STEP_MV;

        while (!error_set) {
            max_iox.single_ended_dac_write(MAX11300::PIXI_PORT4, dac_value);
            delay(BATTEMU_SETTLE_MS);
            uint16_t vbat = _vbat_mv();

            while (!error_set) {
                max_iox.single_ended_dac_write(MAX11300::PIXI_PORT4, dac_value);
                delay(BATTEMU_SETTLE_MS);
                uint16_t vbat = _vbat_mv();

                // stop when VBAT goes just above the desired value
                if (vbat > batt_ctx._lut[i].vbat_mv) {
                    batt_ctx._lut[i].dac = dac_value;
                    break;
                }
                dac_value -= BATTEMU_DAC_STEP;
                if (dac_value == 0) {
                    snprintf(buf, LINE_MAX_LENGTH, "bemu E1: %u %u mV", dac_value, batt_ctx._lut[i].vbat_mv);
                    oled_print(OLED_LINE_DEBUG, buf, true);
                    error_set = true;
                    break;
                }
            }
            // debug print to display
            if (!error_set && batt_ctx._lut[i].vbat_mv % 50 == 0) {  // squelch
                snprintf(buf, LINE_MAX_LENGTH, "bemu: %4u %4u mV", dac_value, batt_ctx._lut[i].vbat_mv);
                oled_print(OLED_LINE_DEBUG, buf, false);
            }
            break; // this cal point is done, move to the next
        }
        if (dac_value > BATTEMU_DAC_NEXT_STEP) dac_value -= BATTEMU_DAC_NEXT_STEP;
        else dac_value = 0; // triggers error
        if (dac_value == 0) {
            snprintf(buf, LINE_MAX_LENGTH, "bemu E2: %u %u mV", dac_value, batt_ctx._lut[i].vbat_mv);
            oled_print(OLED_LINE_DEBUG, buf, true);
            error_set = true;
        }
    }

    // leave the battery emulator set to a low voltage
    batt_ctx.vbat_mv = batt_ctx._lut[0].vbat_mv;
    max_iox.single_ended_dac_write(MAX11300::PIXI_PORT4, BATTEMU_DAC_START);
    delay(BATTEMU_SETTLE_MS);

    batt_ctx.vbat_connect = false;

    if (!error_set) {
        batt_ctx.cal_done = true;
        return 0;
    }
    return -1;
}

// return batt emulator lut
String debug_batt_emu(void) {
    DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API

    JsonArray vbatArray = doc.createNestedArray("vbat");
    JsonArray dacArray = doc.createNestedArray("dac");
    //for (int i = 0; i < LUT_NUM_ENTRIES; i++) {
    // NOTE: not all the values can fit in the buffer so take snapshot
    for (int i = 0; i < 10; i++) {
        uint16_t vbat_mv = batt_ctx._lut[i].vbat_mv;
        uint16_t dac = batt_ctx._lut[i].dac;
        vbatArray.add(vbat_mv);
        dacArray.add(dac);
    }

    return _response(doc);  // always the last line of RPC API
}

String vbat_set(uint16_t mv) {
    DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
    char _buf[LINE_MAX_LENGTH];

    // DEBUG Battery Emulator
    // Provides a way to set the DAC so the board can be tested
    if (false) {
        max_iox.single_ended_dac_write(MAX11300::PIXI_PORT4, mv);
        delay(100);
        uint16_t vbat = _vbat_mv();
        doc["result"]["vbat_mv"] = vbat;
        snprintf(_buf, LINE_MAX_LENGTH, "DAC %u -> %u mV", mv, vbat);
        oled_print(OLED_LINE_RPC, _buf, false);
        return _response(doc);  // always the last line of RPC API
    }

    if (!batt_ctx.cal_done) {
        snprintf(_buf, LINE_MAX_LENGTH, "%s init", __func__);
        oled_print(OLED_LINE_RPC, _buf, true);
        doc["success"] = false;
        doc["result"]["error"] = "init/cal not done";
        return _response(doc);  // always the last line of RPC API
    }

    // TODO: support LUT extrapolation

    if (mv % VBAT_STEP_MV != 0 || mv > VBAT_STOP_MV || mv < VBAT_START_MV) {
        snprintf(_buf, LINE_MAX_LENGTH, "%s %u", __func__, mv);
        oled_print(OLED_LINE_RPC, _buf, true);
        doc["success"] = false;
        doc["result"]["error"] = "invalid argument";
        return _response(doc);  // always the last line of RPC API
    }

    int i = 0;
    for (i = 0; i < LUT_NUM_ENTRIES; i++) {
        if (mv == batt_ctx._lut[i].vbat_mv) break;
    }
    if (i == LUT_NUM_ENTRIES) {
        snprintf(_buf, LINE_MAX_LENGTH, "%s idx %u", __func__, i);
        oled_print(OLED_LINE_RPC, _buf, true);
        doc["success"] = false;
        doc["result"]["error"] = "index";
        return _response(doc);  // always the last line of RPC API
    }

    max_iox.single_ended_dac_write(MAX11300::PIXI_PORT4, batt_ctx._lut[i].dac);
    delay(50);
    uint16_t vbat = _vbat_mv();
    snprintf(_buf, LINE_MAX_LENGTH, "%s %u / %u mV", __func__, mv, vbat);
    oled_print(OLED_LINE_RPC, _buf, false);

    doc["result"]["mv"] = mv;
    doc["result"]["measured_mv"] = vbat;
    doc["result"]["lut_index"] = i;
    doc["result"]["dac"] = batt_ctx._lut[i].dac;
    //doc["result"]["dac1"] = batt_ctx._lut[LUT_NUM_ENTRIES - 1].dac;
    //doc["result"]["dac2"] = batt_ctx._lut[LUT_NUM_ENTRIES - 2].dac;
    //doc["result"]["dac3"] = batt_ctx._lut[LUT_NUM_ENTRIES - 3].dac;
    return _response(doc);  // always the last line of RPC API
}
