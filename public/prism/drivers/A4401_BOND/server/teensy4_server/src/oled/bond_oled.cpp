/*  Sistemi Corporation, copyright, all rights reserved, 2023
 *  Martin Guthrie
 *
 *  OLED Display API
 *  - with font size 12, there are 21 chars across a line
 *
 *  CONVENTION FOR ERROR
 *   - any error should be printed like this, create string in buf with parms, and use OLED_LINE_DEBUG
       and invert=true, for example,
 *
 *         snprintf(buf, LINE_MAX_LENGTH, "bemu E1: %u %u mV", dac_value, batt_ctx._lut[i].vbat_mv);
 *         oled_print(OLED_LINE_DEBUG, buf, true);
*/
#include <Arduino.h>
#include <cstdio>
#include "er_oled.h"
#include "bond_oled.h"

#define LINE_VERTICAL_SIZE  12

void mem_info(uint32_t *stack, uint32_t *heap, uint32_t *psram) ;

static uint8_t oled_buf[OLED_WIDTH * OLED_HEIGHT / 8];
static char _buf[LINE_MAX_LENGTH];
static char spin_chars[] = "/-\\|";
static uint8_t _spin_idx = 0;

void oled_init(void) {
    er_oled_begin();
    er_oled_clear(oled_buf);
}

void oled_clear(void) {
    er_oled_clear(oled_buf);
}

void spinner_update(void) {
    // psram (see https://www.pjrc.com/store/psram.html) is not used
    uint32_t stack = 0, heap = 0, psram = 0;
    mem_info(&stack, &heap, &psram);

    snprintf(_buf, LINE_MAX_LENGTH, "ST:%3lu HP:%3lu kB %c", stack, heap, spin_chars[_spin_idx]);
    er_oled_string(0, OLED_LINE_MEM * LINE_VERTICAL_SIZE, _buf, 12, 1, oled_buf);
    _spin_idx = (_spin_idx + 1) % 4;
    er_oled_display(oled_buf);
}


int oled_print(uint32_t line, const char *buf, bool invert) {
    snprintf(_buf, LINE_MAX_LENGTH, "%-20s", buf);
    //er_oled_string(0, line * LINE_VERTICAL_SIZE, "                     ", 12, 1, oled_buf);  // clr line
    er_oled_string(0, line * LINE_VERTICAL_SIZE, _buf, 12, (invert ? 0 : 1), oled_buf);
    er_oled_display(oled_buf);

    // show error for long time
    if (line == OLED_LINE_DEBUG && invert == true) {
       delay(2000);
    }

    return 0;
}
