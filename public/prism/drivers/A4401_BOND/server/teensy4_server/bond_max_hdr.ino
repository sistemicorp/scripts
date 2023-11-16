/*  Sistemi Corporation, copyright, all rights reserved, 2023
 *  Martin Guthrie
 *  
*/
#include "bond_max_hdr.h"

 MAX11300 *_get_max_from_hdr(int hdr) {
  switch (hdr) {
    case 1: return &max_hdr1;
    case 2: return &max_hdr2;
    case 3: return &max_hdr3;
    case 4: return &max_hdr4;
  }
  return NULL;
 }

MAX11300RegAddress_t _reg_dac_data_port(int port) {
  switch (port) {
    case 0: return dac_data_port_00;
    case 1: return dac_data_port_01;
    case 2: return dac_data_port_02;
    case 3: return dac_data_port_03;
    case 4: return dac_data_port_04;
    case 5: return dac_data_port_05;
    case 6: return dac_data_port_06;
    case 7: return dac_data_port_07;
    case 8: return dac_data_port_08;
    case 9: return dac_data_port_09;
    case 10: return dac_data_port_10;
    case 11: return dac_data_port_11;
  }
  return dac_data_port_00;  // squelch build warning
}

MAX11300RegAddress_t _reg_port_config_port(int port) {
  switch (port) {
    case 0: return port_cfg_00;
    case 1: return port_cfg_01;
    case 2: return port_cfg_02;
    case 3: return port_cfg_03;
    case 4: return port_cfg_04;
    case 5: return port_cfg_05;
    case 6: return port_cfg_06;
    case 7: return port_cfg_07;
    case 8: return port_cfg_08;
    case 9: return port_cfg_09;
    case 10: return port_cfg_10;
    case 11: return port_cfg_11;
  }  
  return port_cfg_00;  // squelch build warning
}

String bond_max_hdr_init(int hdr,  // 1-4
                         int *adcs, int adc_len,
                         int *dacs, int dac_len,
                         int *gpos, int gpo_len,
                         int *gpis, int gpi_len,
                         int gpo_mv, int gpi_mv) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API

  #define MAX_INIT_SETTINGS  32
  _init_regs_t init_regs[MAX_INIT_SETTINGS];

/*  debug only
  doc["result"]["len_adc"] = adc_len;
  doc["result"]["len_dac"] = dac_len;
  doc["result"]["len_gpo"] = gpo_len;
  doc["result"]["len_gpi"] = gpi_len;
  doc["result"]["gpo_mv"] = gpo_mv;
  doc["result"]["gpi_mv"] = gpi_mv;
*/
  unsigned int i = 0;
  init_regs[i].r = device_control; init_regs[i].d = 0x8000; i++; // reset
  init_regs[i].r = device_control; init_regs[i].d = 0xc0 & 0x40b0; i++;
  init_regs[i].r = device_control; init_regs[i].d = 0xc0 & 0x40fc; i++;
  // Set reg DAC_DATA_port registers -----------------------------------------
  // GPIs
  uint16_t d = 0x0666;  // TODO: this comes from gpi_mv
  for (int j = 0; j < gpi_len; j++) {
    init_regs[i].r = _reg_dac_data_port(gpis[j]); init_regs[i].d = d; i++;
  }
  // GPOs
  d = 0x0666;  // TODO: this comes from gpo_mv?
  for (int j = 0; j < gpo_len; j++) {
    init_regs[i].r = _reg_dac_data_port(gpos[j]); init_regs[i].d = d; i++;
  }
  // DACs
  d = 0x0666;  // TODO: this comes from ??
  for (int j = 0; j < dac_len; j++) {
    init_regs[i].r = _reg_dac_data_port(dacs[j]); init_regs[i].d = d; i++;
  }  
  init_regs[i].r = dac_preset_data_1; init_regs[i].d = 0x0; i++;
  init_regs[i].r = dac_preset_data_2; init_regs[i].d = 0x0; i++;
  // Set reg PORT_CONFIG -----------------------------------------------------
  // GPIs
  for (int j = 0; j < gpi_len; j++) {
    init_regs[i].r = _reg_port_config_port(gpis[j]); init_regs[i].d = d; i++;
  }
  // delay 200us * num pins in mode 1 -> just delay 2ms!
  init_regs[i].r = reserved_6a; init_regs[i].d = 0x0; i++;  // !! DELAY 1 ms !!
  init_regs[i].r = reserved_6a; init_regs[i].d = 0x0; i++;  // !! DELAY 1 ms !!
  // GPODAT for ports in mode 3
  init_regs[i].r = gpo_data_10_to_0; init_regs[i].d = 0x0; i++;
  init_regs[i].r = gpo_data_11; init_regs[i].d = 0x0; i++;
  // GPOs
  d = 0x3000;
  for (int j = 0; j < gpo_len; j++) {
    init_regs[i].r = _reg_port_config_port(gpos[j]); init_regs[i].d = d; i++;
  }
  // DACs
  d = 0x5100;  // TODO: where this come from?
  for (int j = 0; j < dac_len; j++) {
    init_regs[i].r = _reg_port_config_port(dacs[j]); init_regs[i].d = d; i++;
  }  
  // IRQ modes
  init_regs[i].r = gpi_irqmode_5_to_0; init_regs[i].d = 0x0; i++;
  init_regs[i].r = gpi_irqmode_10_to_6; init_regs[i].d = 0x0; i++;
  init_regs[i].r = gpi_irqmode_11; init_regs[i].d = 0x0; i++;
  // ADCs
  d = 0x7100;  // TODO: where this come from?
  for (int j = 0; j < adc_len; j++) {
    init_regs[i].r = _reg_port_config_port(adcs[j]); init_regs[i].d = d; i++;
  }    
  init_regs[i].r = device_control; init_regs[i].d = 0xc0 & 0x40ff; i++;
  init_regs[i].r = device_control; init_regs[i].d = 0xc0; i++;
  init_regs[i].r = interrupt_mask; init_regs[i].d = 0xffff; i++;

  MAX11300 *max = _get_max_from_hdr(hdr);
  for(unsigned int k = 0; k < i; k++) {
    if (init_regs[k].r != reserved_6a) {
      max->write_register(init_regs[k].r, init_regs[k].d);
    }
    delay(1);
  }

  doc["result"]["regs_seq_len"] = i;

  return _response(doc);  // always the last line of RPC API
}
