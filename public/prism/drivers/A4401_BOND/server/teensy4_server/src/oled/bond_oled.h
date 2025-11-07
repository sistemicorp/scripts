/*  Sistemi Corporation, copyright, all rights reserved, 20232025
 *  Martin Guthrie
 *
 *  OLED Display API
 *
*/

#define LINE_MAX_LENGTH     21

#define OLED_LINE_STATUS    0
#define OLED_LINE_DEBUG     1
#define OLED_LINE_ERROR     2  // FIXME: this line is not working?!
#define OLED_LINE_MEM       3
#define OLED_LINE_RPC       4

void spinner_update(void);
int oled_print(uint32_t line, const char *buf, bool invert);
void oled_clear(void);
void oled_init(void);
