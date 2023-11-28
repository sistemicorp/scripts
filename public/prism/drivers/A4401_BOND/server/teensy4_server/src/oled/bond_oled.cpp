/*  Sistemi Corporation, copyright, all rights reserved, 2023
 *  Martin Guthrie
 *
 *  OLED Display API
 *  - with font size 12, there are 21 chars across a line
 *
*/
#include <cstdio>
#include "er_oled.h"
#include "bond_oled.h"

#define LINE_VERTICAL_SIZE  12


static uint8_t oled_buf[OLED_WIDTH * OLED_HEIGHT / 8];

void oled_init(void) {
    er_oled_begin();
    er_oled_clear(oled_buf);
}

void oled_clear(void) {
    er_oled_clear(oled_buf);
}

int oled_print(uint32_t line, const char *buf, bool invert) {
    char _buf[LINE_MAX_LENGTH];
    snprintf(_buf, LINE_MAX_LENGTH, "%-20s", buf);
    //er_oled_string(0, line * LINE_VERTICAL_SIZE, "                     ", 12, 1, oled_buf);  // clr line
    er_oled_string(0, line * LINE_VERTICAL_SIZE, _buf, 12, (invert ? 0 : 1), oled_buf);
    er_oled_display(oled_buf);
    return 0;
}
