/*  Sistemi Corporation, copyright, all rights reserved, 2023
 *  Martin Guthrie
 *
*/
#pragma once

typedef struct {
   MAX11300RegAddress_t r;
   uint16_t d;
   int delay;
} _init_regs_t;

String bond_max_hdr_init(int hdr,  // 1-4
                         int *adcs, int adc_len,
                         int *dacs, int dac_len,
                         int *gpos, int gpo_len,
                         int *gpis, int gpi_len,
                         int gpo_mv, int gpi_mv);
String bond_batt_emu_cal(void);
String bond_max_hdr_adc_cal(int hdr);
String bond_max_hdr_adc(int hdr, int port);
String bond_max_hdr_dac(int hdr, int port, int mv);
String bond_max_hdr_gpi(int hdr, int port);
String bond_max_hdr_gpo(int hdr, int port, bool state);
int init_max_hdr_bist(void);
