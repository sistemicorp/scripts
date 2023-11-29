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

static _lut_t _lut[LUT_NUM_ENTRIES];
static bool cal_done = false;

int battemu_init(void) {
    uint16_t vbat_target_mv = VBAT_START_MV;
    uint16_t dac_value = 1600;
    char buf[LINE_MAX_LENGTH];

    if (cal_done) return 0;

    iox_vbat_en(true);
    delay(12);  // TODO: measure this

    // create LUT for output
    for (int i = 0; i < LUT_NUM_ENTRIES; i++) {
        _lut[i].vbat_mv = VBAT_START_MV + i * VBAT_STEP_MV;

        while (true) {
            max_hdr1.single_ended_dac_write(MAX11300::PIXI_PORT9, dac_value);
            delay(10);
            ina219_vbat.startSingleMeasurement();
            float tmp = ina219_vbat.getBusVoltage_V();
            uint16_t vbat = (uint16_t)(tmp * 1000.0f);

            if (vbat > _lut[i].vbat_mv) {
                _lut[i].dac = dac_value;
                dac_value--;
                if (_lut[i].vbat_mv % 500 == 0) {
                    snprintf(buf, LINE_MAX_LENGTH, "battemu: %u %u mV", dac_value, vbat);
                    oled_print(OLED_LINE_DEBUG, buf, false);
                }
                break;
            }
            dac_value--;
        }
    }

    cal_done = true;
    return 0;
}

