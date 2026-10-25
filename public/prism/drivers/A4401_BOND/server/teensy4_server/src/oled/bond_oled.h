/*  Sistemi Corporation, copyright, all rights reserved, 2023-2026
 *  Martin Guthrie
 *
 *  OLED Display API
 *
 *  oled_print() only draws into a RAM frame buffer and marks the rows it touched.
 *  - Before oled_set_deferred(true) (during setup()), the panel is written at once and
 *    errors on OLED_LINE_DEBUG are held on screen for OLED_ERROR_HOLD_MS.
 *  - After oled_set_deferred(true) (loop()), the panel is written by oled_service(),
 *    so RPC calls do not wait on the I2C display transfer.
 */
#pragma once

#include <stdint.h>

#define LINE_MAX_LENGTH     21

#define OLED_LINE_STATUS    0
#define OLED_LINE_DEBUG     1
#define OLED_LINE_ERROR     2
#define OLED_LINE_MEM       3
#define OLED_LINE_RPC       4

#define OLED_ERROR_HOLD_MS  2000  // setup() only, time an error stays readable
#define OLED_REFRESH_MS     100   // loop(), minimum time between panel writes

void oled_init(void);
void oled_clear(void);
void oled_set_deferred(bool deferred);
int oled_print(uint32_t line, const char *buf, bool invert);
void oled_service(bool busy);
void spinner_update(void);
