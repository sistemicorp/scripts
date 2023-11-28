/*  Sistemi Corporation, copyright, all rights reserved, 2023
 *  Martin Guthrie
 *
 *  OLED Display API
 *
*/

#define OLED_LINE_STATUS 0
#define OLED_LINE_DEBUG  1
#define OLED_LINE_RPC    4

int oled_print(uint32_t line, char *buf, bool invert);
void oled_clear(void);
void oled_init(void);
