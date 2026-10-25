/*  Sistemi Corporation, copyright, all rights reserved, 2023-2026
 *  Martin Guthrie
 *
 *  OLED Display API, see bond_oled.h
 *  - with font size 12, there are 21 chars across a line
 *
 *  CONVENTION FOR ERROR
 *   - any error should be printed like this, create string in buf with parms, and use OLED_LINE_DEBUG
 *     and invert=true, for example,
 *
 *         snprintf(buf, LINE_MAX_LENGTH, "bemu E1: %u %u mV", dac_value, vbat_mv);
 *         oled_print(OLED_LINE_DEBUG, buf, true);
 */
#include <Arduino.h>
#include <cstdio>
#include "er_oled.h"
#include "bond_oled.h"

#define LINE_VERTICAL_SIZE  12
#define FONT_SIZE           12

void mem_info(uint32_t *stack, uint32_t *heap, uint32_t *psram);

static uint8_t oled_buf[OLED_WIDTH * OLED_HEIGHT / 8];
static char _buf[LINE_MAX_LENGTH + 1];
static const char spin_chars[] = "/-\\|";
static uint8_t _spin_idx = 0;

static bool _ready = false;         // oled_init() done, I2C is up
static bool _deferred = false;
static uint8_t _dirty_pages = 0;      // bit per 8 pixel high page that needs writing
static unsigned long _last_write_ms = 0;

static void _mark_line_dirty(uint32_t line) {
  uint32_t y0 = line * LINE_VERTICAL_SIZE;
  uint32_t y1 = y0 + LINE_VERTICAL_SIZE - 1;
  for (uint32_t page = y0 / 8; page <= y1 / 8 && page < PAGES; page++) {
    _dirty_pages |= (1 << page);
  }
}

static void _write_dirty(void) {
  if (!_ready || !_dirty_pages) return;
  er_oled_display_pages(oled_buf, _dirty_pages);
  _dirty_pages = 0;
  _last_write_ms = millis();
}

void oled_init(void) {
  er_oled_begin();
  _ready = true;
  er_oled_clear(oled_buf);
  _dirty_pages = 0xFF;
  _write_dirty();
}

void oled_clear(void) {
  er_oled_clear(oled_buf);
  _dirty_pages = 0xFF;
  if (!_deferred) _write_dirty();
}

void oled_set_deferred(bool deferred) {
  _deferred = deferred;
  if (!_deferred) _write_dirty();
}

int oled_print(uint32_t line, const char *buf, bool invert) {
  snprintf(_buf, sizeof(_buf), "%-20s", buf ? buf : "");
  er_oled_string(0, line * LINE_VERTICAL_SIZE, _buf, FONT_SIZE, (invert ? 0 : 1), oled_buf);
  _mark_line_dirty(line);

  if (_deferred) return 0;

  _write_dirty();
  if (_ready && line == OLED_LINE_DEBUG && invert) {
    delay(OLED_ERROR_HOLD_MS);  // setup() only, so the error can be read
  }
  return 0;
}

/* oled_service
 * - call from loop(), writes changed rows to the panel
 * - busy: true when an RPC request is waiting, the write is skipped so it is not delayed
 */
void oled_service(bool busy) {
  if (!_deferred || busy || !_dirty_pages) return;
  if (millis() - _last_write_ms < OLED_REFRESH_MS) return;
  _write_dirty();
}

void spinner_update(void) {
  // psram (see https://www.pjrc.com/store/psram.html) is not used
  uint32_t stack = 0, heap = 0, psram = 0;
  mem_info(&stack, &heap, &psram);

  snprintf(_buf, sizeof(_buf), "ST:%3lu HP:%3lu kB %c", stack, heap, spin_chars[_spin_idx]);
  er_oled_string(0, OLED_LINE_MEM * LINE_VERTICAL_SIZE, _buf, FONT_SIZE, 1, oled_buf);
  _mark_line_dirty(OLED_LINE_MEM);
  _spin_idx = (_spin_idx + 1) % 4;
  if (!_deferred) _write_dirty();
}
