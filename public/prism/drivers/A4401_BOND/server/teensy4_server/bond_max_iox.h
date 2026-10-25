/*  Sistemi Corporation, copyright, all rights reserved, 2023-2026
 *  Martin Guthrie
 *
 *  MAX11311 IOX (IO Expander), see schematic IOExpand sheet
 *
 *  Header 1 LDO (TLV75901, Hdr1 sheet): enabled by Header 1 MAX port 1 (GPO), its voltage
 *  is set by IOX DAC port 5 (LDO_ADJ) through R47,
 *      VOUT = VFB + R46 / R47 * (2 * VFB - LDO_ADJ), VFB = 0.55V, R46 = 16k, R47 = R49 = 5.1k
 *  so LDO_ADJ 0V..1.1V gives 4.0V..0.55V
 *  See: https://github.com/MaximIntegratedRefDesTeam/MAX11300
 */
#pragma once

#include <Arduino.h>
#include "src/MAX11311/MAX11300.h"

#define LDO_MIN_MV  600
#define LDO_MAX_MV  3900

// IOX port assignments, see schematic a4402 IOExpand sheet
#define IOX_PORT_VBAT_CON   MAX11300::PIXI_PORT2   // GPO, active high
#define IOX_PORT_VBAT_EN    MAX11300::PIXI_PORT3   // GPO, active high
#define IOX_PORT_VBAT_ADJ   MAX11300::PIXI_PORT4   // DAC, battery emulator
#define IOX_PORT_LDO_ADJ    MAX11300::PIXI_PORT5   // DAC, Header 1 LDO voltage (LDO_ADJ)
#define IOX_PORT_SELFTEST   MAX11300::PIXI_PORT7   // GPO, active high
#define IOX_PORT_LED_GREEN  MAX11300::PIXI_PORT8
#define IOX_PORT_LED_YELLOW MAX11300::PIXI_PORT9
#define IOX_PORT_LED_RED    MAX11300::PIXI_PORT10
#define IOX_PORT_LED_BLUE   MAX11300::PIXI_PORT11

extern MAX11300 max_iox;

// internal API, use these from other modules, never the RPC functions
int init_max_iox(void);
void iox_set(MAX11300::MAX11300_Ports port, bool assert);
void iox_leds(bool green, bool yellow, bool red, bool blue);

// RPC API
String iox_led_green(bool assert);
String iox_led_yellow(bool assert);
String iox_led_red(bool assert);
String iox_led_blue(bool assert);
String iox_selftest(bool assert);
String iox_vbat_en(bool assert);
String iox_vbat_con(bool assert);
String bond_ldo_set(uint16_t mv);
