/*  Sistemi Corporation, copyright, all rights reserved, 2021-2026
 *  Martin Guthrie
 *
 *  Teensy "on board" functions: identity, status, GPIO, ADC, and BOND supply rail BIST
 */
#pragma once

#include <Arduino.h>

#define BIST_VOLTAGE_TOLERANCE_MV  200  // FIXME: change to 100mV for BOND r2

typedef struct {
  uint8_t pin;
  uint16_t mv;       // expected reading
  const char *name;
} bist_voltage_t;

// supply rails checked by setup() and bist_voltage(), index 0 is V6V
extern const bist_voltage_t bist_voltages[];
extern const unsigned int bist_voltages_num;

// internal API, use these from other modules, never the RPC functions
unsigned int teensy_read_adc(unsigned int pin, unsigned int sample_num, unsigned int sample_rate_ms);
unsigned int bist_adc_to_mv(unsigned int adc_raw);
void mem_info(uint32_t *stack, uint32_t *heap, uint32_t *psram);
void set_setup_fail_code(uint16_t code);

// RPC API
String unique_id(void);
String slot(void);
String version(void);
String status(void);
String temperature(void);
String reboot_to_bootloader(void);
String set_led(bool on);
String read_adc(unsigned int pin_number, unsigned int sample_num, unsigned int sample_rate);
String init_gpio(int pin_number, String &mode);
String read_gpio(int pin_number);
String write_gpio(int pin_number, bool state);
String bist_voltage(String name);
