/*  Sistemi Corporation, copyright, all rights reserved, 2023
 *  Martin Guthrie
 *
 *  Battery Emulator the BOND design, a4401.
 *
*/
#include "bond_max_iox.h"
#include "src/oled/bond_oled.h"

//extern int8_t oled_buf[OLED_WIDTH * OLED_HEIGHT / 8];

#define VBAT_START_MV     1000
#define VBAT_STOP_MV      5000
#define VBAT_STEP_MV      100
#define LUT_NUM_ENTRIES   (VBAT_STOP_MV - VBAT_START_MV) / VBAT_STEP_MV


typedef struct {
   uint16_t dac;      // digital setting
   uint16_t vbat_mv;
} _lut_t;

static _lut_t _lut[LUT_NUM_ENTRIES];

int battemu_init(void) {
    uint16_t vbat_target_mv = VBAT_START_MV;
    uint16_t dac_value = 0;
    char buf[LINE_MAX_LENGTH];

    iox_vbat_en(true);
    delay(12);  // TODO: measure this

    // create LUT for output
    for (int i = 0; i < LUT_NUM_ENTRIES; i++) {
        max_iox.single_ended_dac_write(MAX11300::PIXI_PORT9, dac_value);
        delay(2);
        ina219_vbat.startSingleMeasurement();
        float tmp = ina219_vbat.getBusVoltage_V();
        uint16_t vbat = (uint16_t)(tmp * 1000.0f);
        snprintf(buf, LINE_MAX_LENGTH, "battemu: %u %u mV", dac_value, vbat);

        oled_print(OLED_LINE_DEBUG, buf, false);
        dac_value += 50;
        //break;

    }

    return 0;
}
