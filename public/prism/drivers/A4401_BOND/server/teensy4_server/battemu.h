/*  Sistemi Corporation, copyright, all rights reserved, 2023-2026
 *  Martin Guthrie
 *
 *  Battery Emulator (VBAT), LTM8052 adjusted by IOX DAC port 4, measured by INA226 (0x40)
 *  - calibrated at power up by setup(), bond_batt_emu_cal() repeats the calibration
 *  - VBAT_START_MV to VBAT_STOP_MV in VBAT_STEP_MV steps
 */
#pragma once

#include <Arduino.h>

#define VBAT_START_MV     1500
#define VBAT_STOP_MV      5000
#define VBAT_STEP_MV      50

// internal API, use these from other modules, never the RPC functions
int battemu_init(void);
int battemu_set_mv(uint16_t mv, uint16_t *measured_mv);

// RPC API
String bond_batt_emu_cal(void);
String vbat_set(uint16_t mv);
String vbat_read(void);
String debug_batt_emu(void);
