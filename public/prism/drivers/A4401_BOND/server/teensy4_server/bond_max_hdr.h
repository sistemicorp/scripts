/*  Sistemi Corporation, copyright, all rights reserved, 2023-2026
 *  Martin Guthrie
 *
 *  MAX11311 on each DUT Header (1-4), see schematic Hdr1..Hdr4 sheets.
 *
 *  Port 11 of every header MAX11311 is wired to the 2.5V reference (REF2V5) for self test.
 *  Ports 0-10 are configured by the Python driver from the header definition (JSON) file,
 *  see bond_max_hdr_init(). The firmware remembers each port's mode, and the ADC, DAC,
 *  GPO and GPI RPCs refuse a port that is not in that mode.
 *
 *  Voltage ranges (DAC reference 2.5V),
 *  - ADC, DAC and GPO logic-high: 0 to 10V, code = mV * 4096 / 10000
 *  - GPI threshold: 0 to 2.5V, code = mV * 4096 / 2500
 */
#pragma once

#include <Arduino.h>

#define HDR_NUM          4
#define HDR_PORT_NUM     12   // ports 0-11
#define HDR_PORT_CAL     11   // wired to REF2V5
#define HDR_DAC_MV_MAX   10000
#define HDR_GPI_MV_MAX   2500

// HDR3 port 9 drives relay RL3 (LED anode on V5VA, 200R) that connects VBUS to the External
// USB-C connector, active low. Its GPO high level is fixed at HDR_VBUS_GPO_MV, not the header
// gpo_mv, a lower high level leaves the relay LED on.
#define HDR_VBUS         3
#define HDR_VBUS_PORT    9
#define HDR_VBUS_GPO_MV  5000

// internal API, use these from other modules, never the RPC functions
int init_max_hdr_bist(void);
void max_hdr_reset_outputs(void);

// RPC API
String bond_max_hdr_init(int hdr,
                         int *adcs, int adc_len,
                         int *dacs, int dac_len,
                         int *gpos, int gpo_len,
                         int *gpis, int gpi_len,
                         int gpo_mv, int gpi_mv);
String bond_max_hdr_adc_cal(int hdr);
String bond_max_hdr_adc(int hdr, int port);
String bond_max_hdr_dac(int hdr, int port, int mv);
String bond_max_hdr_gpo(int hdr, int port, bool state);
String bond_max_hdr_gpi(int hdr, int port);
String vbus_en(bool assert);
