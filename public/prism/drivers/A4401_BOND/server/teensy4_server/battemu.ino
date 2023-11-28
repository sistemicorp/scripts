/*  Sistemi Corporation, copyright, all rights reserved, 2023
 *  Martin Guthrie
 *
 *  Battery Emulator the BOND design, a4401.
 *
*/
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
    char buf[32];

    // create LUT for output
    for (int i = 0; i < LUT_NUM_ENTRIES; i++) {
        max_iox.single_ended_dac_write(MAX11300::PIXI_PORT9, dac_value);
        delay(1);
        uint16_t vbat = (uint16_t)(ina219_vbus.getBusVoltage_V() * 1000);
        snprintf(buf, 32, "battemu_init: %u %u", dac_value, vbat);

        oled_print(OLED_LINE_DEBUG, buf, false);
        break;

    }

    return 0;
}

