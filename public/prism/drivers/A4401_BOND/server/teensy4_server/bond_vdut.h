/*  Sistemi Corporation, copyright, all rights reserved, 2023-2026
 *  Martin Guthrie
 *
 *  VDUT supply, TPS55289 buck-boost (see schematic SMPS sheet), measured by INA226 (0x41)
 */
#pragma once

#include <Arduino.h>

#define VDUT_MAX_MV  9000
#define VDUT_MIN_MV  1000

// internal API, use these from other modules, never the RPC functions
int vdut_init(void);
int vdut_set_mv(uint16_t mv);
void vdut_connect(bool assert);

// RPC API
String vdut_set(uint16_t mv);
String vdut_read(void);
String vdut_con(bool assert);
String vdut_en(bool assert);
String vdut_get_fault(void);
String vdut_reset(void);
