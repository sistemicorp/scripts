/*  Sistemi Corporation, copyright, all rights reserved, 2023-2026
 *  Martin Guthrie
 *
 *  MAX11311 on each DUT Header, see bond_max_hdr.h
 */
#include "bond_max_hdr.h"
#include "bond_pins.h"
#include "rpc_helpers.h"
#include "src/MAX11311/MAX11300.h"
#include "src/oled/bond_oled.h"

#define MAX11311_DEV_ID     0x424  // see datasheet
#define BIST_VREF_TOL_MV    20
#define BIST_VREF_MV        2500
#define DAC_CODE_MAX        4095
#define INIT_REGS_MAX       48     // 15 fixed writes + at most 2 per port

#define PORT_CFG_GPI        0x1000  // mode 1
#define PORT_CFG_GPO        0x3000  // mode 3
#define PORT_CFG_DAC        0x5100  // mode 5, 0 to +10V
#define PORT_CFG_ADC        0x7100  // mode 7, 0 to +10V
#define DEVICE_CONTROL      0xc1    // internal ref, ADC single sweep on CNVT
#define DELAY_FLAG          reserved_6A  // init sequence entry that is a 1 ms delay only

typedef enum {
  HDR_MODE_NONE = 0,
  HDR_MODE_ADC,
  HDR_MODE_DAC,
  HDR_MODE_GPO,
  HDR_MODE_GPI,
} hdr_mode_t;

typedef struct {
  MAX11300 max;
  uint8_t cs_pin;
  bool ready;                     // configured by bond_max_hdr_init()
  hdr_mode_t mode[HDR_PORT_NUM];
} _hdr_t;

static _hdr_t hdrs[HDR_NUM] = {
  {.max = MAX11300(), .cs_pin = SPI_CS_HDR1_Pin, .ready = false, .mode = {}},
  {.max = MAX11300(), .cs_pin = SPI_CS_HDR2_Pin, .ready = false, .mode = {}},
  {.max = MAX11300(), .cs_pin = SPI_CS_HDR3_Pin, .ready = false, .mode = {}},
  {.max = MAX11300(), .cs_pin = SPI_CS_HDR4_Pin, .ready = false, .mode = {}},
};

static const MAX11300RegAddress_t dac_data_regs[HDR_PORT_NUM] = {
  dac_data_port_p0, dac_data_port_p1, dac_data_port_p2, dac_data_port_p3,
  dac_data_port_p4, dac_data_port_p5, dac_data_port_p6, dac_data_port_p7,
  dac_data_port_p8, dac_data_port_p9, dac_data_port_p10, dac_data_port_p11,
};

static const MAX11300RegAddress_t port_cfg_regs[HDR_PORT_NUM] = {
  port_cfg_p0, port_cfg_p1, port_cfg_p2, port_cfg_p3, port_cfg_p4, port_cfg_p5,
  port_cfg_p6, port_cfg_p7, port_cfg_p8, port_cfg_p9, port_cfg_p10, port_cfg_p11,
};

static const MAX11300::MAX11300_Ports pixi_ports[HDR_PORT_NUM] = {
  MAX11300::PIXI_PORT0, MAX11300::PIXI_PORT1, MAX11300::PIXI_PORT2, MAX11300::PIXI_PORT3,
  MAX11300::PIXI_PORT4, MAX11300::PIXI_PORT5, MAX11300::PIXI_PORT6, MAX11300::PIXI_PORT7,
  MAX11300::PIXI_PORT8, MAX11300::PIXI_PORT9, MAX11300::PIXI_PORT10, MAX11300::PIXI_PORT11,
};

typedef struct {
  MAX11300RegAddress_t r;
  uint16_t d;
} _init_regs_t;

static _hdr_t *_get_hdr(int hdr) {
  if (hdr < 1 || hdr > HDR_NUM) return NULL;
  return &hdrs[hdr - 1];
}

static uint16_t _mv_to_code(int mv, int full_scale_mv) {
  uint32_t code = ((uint32_t)mv * 4096 + full_scale_mv / 2) / full_scale_mv;
  return code > DAC_CODE_MAX ? DAC_CODE_MAX : (uint16_t)code;
}

static uint32_t _code_to_mv(uint16_t code) {
  return ((uint32_t)code * HDR_DAC_MV_MAX + 2048) / 4096;
}

/* GPO data word with every GPO at its idle level
 * - all GPOs are low, except the active low VBUS GPO which is high (deasserted)
 */
static uint16_t _gpo_idle_bits(int hdr, const hdr_mode_t *mode) {
  if (hdr == HDR_VBUS && mode[HDR_VBUS_PORT] == HDR_MODE_GPO) {
    return (uint16_t)(1 << pixi_ports[HDR_VBUS_PORT]);
  }
  return 0;
}

/* _hdr_configure
 * - program the MAX11311 port modes, following the datasheet flowchart
 * - every port 0-11 may appear only once across all the lists
 * - return NULL on success, else an error string
 */
static const char *_hdr_configure(int hdr,
                                  int *adcs, int adc_len,
                                  int *dacs, int dac_len,
                                  int *gpos, int gpo_len,
                                  int *gpis, int gpi_len,
                                  int gpo_mv, int gpi_mv) {
  _hdr_t *h = _get_hdr(hdr);
  if (h == NULL) return "1 <= hdr <= 4, invalid parameter";
  if (gpo_mv < 0 || gpo_mv > HDR_DAC_MV_MAX) return "0 <= gpo_mv <= 10000";
  if (gpi_mv < 0 || gpi_mv > HDR_GPI_MV_MAX) return "0 <= gpi_mv <= 2500";

  hdr_mode_t mode[HDR_PORT_NUM] = {};
  struct { int *ports; int len; hdr_mode_t mode; } lists[] = {
    {adcs, adc_len, HDR_MODE_ADC}, {dacs, dac_len, HDR_MODE_DAC},
    {gpos, gpo_len, HDR_MODE_GPO}, {gpis, gpi_len, HDR_MODE_GPI},
  };
  for (auto &l : lists) {
    if (l.len < 0 || l.len > HDR_PORT_NUM) return "port list length";
    for (int j = 0; j < l.len; j++) {
      int p = l.ports[j];
      if (p < 0 || p >= HDR_PORT_NUM) return "0 <= port <= 11, invalid parameter";
      if (mode[p] != HDR_MODE_NONE) return "port used more than once";
      mode[p] = l.mode;
    }
  }
  if (mode[HDR_PORT_CAL] != HDR_MODE_ADC) return "port 11 must be ADC";

  _init_regs_t regs[INIT_REGS_MAX];
  unsigned int i = 0;
  uint16_t gpi_code = _mv_to_code(gpi_mv, HDR_GPI_MV_MAX);
  uint16_t gpo_code = _mv_to_code(gpo_mv, HDR_DAC_MV_MAX);
  uint16_t gpo_idle = 0;

  regs[i++] = {device_control, 0x8000};  // reset
  regs[i++] = {device_control, DEVICE_CONTROL & 0x40b0};
  regs[i++] = {device_control, DEVICE_CONTROL & 0x40fc};
  // DAC data first: GPI threshold, GPO logic-high level, DAC outputs start at 0V
  for (int p = 0; p < HDR_PORT_NUM; p++) {
    if (mode[p] == HDR_MODE_GPI) regs[i++] = {dac_data_regs[p], gpi_code};
    if (mode[p] == HDR_MODE_GPO) {
      bool vbus = hdr == HDR_VBUS && p == HDR_VBUS_PORT;
      regs[i++] = {dac_data_regs[p], vbus ? _mv_to_code(HDR_VBUS_GPO_MV, HDR_DAC_MV_MAX) : gpo_code};
    }
    if (mode[p] == HDR_MODE_DAC) regs[i++] = {dac_data_regs[p], 0};
  }
  regs[i++] = {dac_preset_data_1, 0x0};
  regs[i++] = {dac_preset_data_2, 0x0};
  for (int p = 0; p < HDR_PORT_NUM; p++) {
    if (mode[p] == HDR_MODE_GPI) regs[i++] = {port_cfg_regs[p], PORT_CFG_GPI};
  }
  // delay 200us * num pins in mode 1 -> just delay 2ms!
  regs[i++] = {DELAY_FLAG, 0x0};
  regs[i++] = {DELAY_FLAG, 0x0};
  // GPODAT before ports go to mode 3, so GPOs start at their idle level
  gpo_idle = _gpo_idle_bits(hdr, mode);
  regs[i++] = {gpo_data_P10P6_P5P0, gpo_idle};
  regs[i++] = {gpo_data_P11, 0x0};
  for (int p = 0; p < HDR_PORT_NUM; p++) {
    if (mode[p] == HDR_MODE_GPO) regs[i++] = {port_cfg_regs[p], PORT_CFG_GPO};
  }
  for (int p = 0; p < HDR_PORT_NUM; p++) {
    if (mode[p] == HDR_MODE_DAC) regs[i++] = {port_cfg_regs[p], PORT_CFG_DAC};
  }
  regs[i++] = {gpi_irqmode_P5_P0, 0x0};
  regs[i++] = {gpi_irqmode_P10_P6, 0x0};
  regs[i++] = {gpi_irqmode_P11, 0x0};
  for (int p = 0; p < HDR_PORT_NUM; p++) {
    if (mode[p] == HDR_MODE_ADC) regs[i++] = {port_cfg_regs[p], PORT_CFG_ADC};
  }
  regs[i++] = {device_control, DEVICE_CONTROL & 0x40ff};
  regs[i++] = {device_control, DEVICE_CONTROL};
  regs[i++] = {interrupt_mask, 0xffff};

  h->ready = false;
  h->max.begin(SPI_MOSI_Pin, SPI_MISO_Pin, SPI_SCLK_Pin, h->cs_pin, MAX11311_CONVERT_Pin);
  for (unsigned int k = 0; k < i; k++) {
    if (regs[k].r != DELAY_FLAG) {
      h->max.write_register(regs[k].r, regs[k].d);
    }
    delay(1);
  }

  for (int p = 0; p < HDR_PORT_NUM; p++) h->mode[p] = mode[p];
  h->ready = true;
  return NULL;
}

/* _hdr_port
 * - checks hdr, port and the port's configured mode
 * - return NULL on success, else an error string
 */
static const char *_hdr_port(int hdr, int port, hdr_mode_t mode, _hdr_t **h_out) {
  _hdr_t *h = _get_hdr(hdr);
  if (h == NULL) return "1 <= hdr <= 4, invalid parameter";
  if (!h->ready) return "header not initialized";
  if (port < 0 || port >= HDR_PORT_NUM) return "0 <= port <= 11, invalid parameter";
  if (h->mode[port] != mode) return "port not configured for this mode";
  *h_out = h;
  return NULL;
}

static uint32_t _adc_read_mv(_hdr_t *h, int port) {
  uint16_t data = 0;
  h->max.single_ended_adc_read(pixi_ports[port], &data);
  return _code_to_mv(data);
}

int init_max_hdr_bist(void) {
  /* Each MAX11311 on a header has port 11 mapped as an ADC which is
     connected to BOND's Vref (2.5V). On power up, setup() inits
     all headers with only PORT 11 mapped as ADC and this voltage is checked.
  */
  char buf[LINE_MAX_LENGTH];

  for (int hdr = 1; hdr <= HDR_NUM; hdr++) {
    _hdr_t *h = _get_hdr(hdr);
    h->max.begin(SPI_MOSI_Pin, SPI_MISO_Pin, SPI_SCLK_Pin, h->cs_pin, MAX11311_CONVERT_Pin);

    uint16_t _dev_id = h->max.read_register(dev_id);
    if (_dev_id != MAX11311_DEV_ID) {
      snprintf(buf, LINE_MAX_LENGTH, "hdr %d id %x", hdr, _dev_id);
      oled_print(OLED_LINE_DEBUG, buf, true);
      return -1;
    }

    int adcs[] = {HDR_PORT_CAL};
    const char *err = _hdr_configure(hdr, adcs, 1, NULL, 0, NULL, 0, NULL, 0, 0, 0);
    if (err) {
      snprintf(buf, LINE_MAX_LENGTH, "hdr %d cfg err", hdr);
      oled_print(OLED_LINE_DEBUG, buf, true);
      return -1;
    }
    snprintf(buf, LINE_MAX_LENGTH, "hdr %d", hdr);
    oled_print(OLED_LINE_DEBUG, buf, false);
  }

  for (int hdr = 1; hdr <= HDR_NUM; hdr++) {
    uint32_t mv = _adc_read_mv(_get_hdr(hdr), HDR_PORT_CAL);
    snprintf(buf, LINE_MAX_LENGTH, "hdr %d %lu mV", hdr, mv);
    if (mv > (BIST_VREF_MV + BIST_VREF_TOL_MV) || mv < (BIST_VREF_MV - BIST_VREF_TOL_MV)) {
      oled_print(OLED_LINE_DEBUG, buf, true);
      return -1;
    }
    oled_print(OLED_LINE_DEBUG, buf, false);
  }
  return 0;
}

/* max_hdr_reset_outputs
 * - DUT safe state between tests: every DAC port to 0V, every GPO to its idle level
 */
void max_hdr_reset_outputs(void) {
  for (int hdr = 1; hdr <= HDR_NUM; hdr++) {
    _hdr_t *h = _get_hdr(hdr);
    if (!h->ready) continue;
    for (int p = 0; p < HDR_PORT_NUM; p++) {
      if (h->mode[p] == HDR_MODE_DAC) h->max.write_register(dac_data_regs[p], 0);
    }
    h->max.write_register(gpo_data_P10P6_P5P0, _gpo_idle_bits(hdr, h->mode));
    h->max.write_register(gpo_data_P11, 0x0);
  }
}

String bond_max_hdr_init(int hdr,  // 1-4
                         int *adcs, int adc_len,
                         int *dacs, int dac_len,
                         int *gpos, int gpo_len,
                         int *gpis, int gpi_len,
                         int gpo_mv, int gpi_mv) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API

  const char *err = _hdr_configure(hdr, adcs, adc_len, dacs, dac_len, gpos, gpo_len,
                                   gpis, gpi_len, gpo_mv, gpi_mv);
  if (err) return rpc_error(doc, err);

  doc["result"]["hdr"] = hdr;
  return rpc_response(doc);  // always the last line of RPC API
}

/* Read Header <1-4> ADC Port 11 cal voltage
 * - all MAX11311's Port 11 is connected to 2500mV voltage reference
 */
String bond_max_hdr_adc_cal(int hdr) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API

  _hdr_t *h = NULL;
  const char *err = _hdr_port(hdr, HDR_PORT_CAL, HDR_MODE_ADC, &h);
  if (err) return rpc_error(doc, err);

  doc["result"]["mV"] = _adc_read_mv(h, HDR_PORT_CAL);
  return rpc_response(doc);  // always the last line of RPC API
}

String bond_max_hdr_adc(int hdr, int port) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API

  _hdr_t *h = NULL;
  const char *err = _hdr_port(hdr, port, HDR_MODE_ADC, &h);
  if (err) return rpc_error(doc, err);

  doc["result"]["mV"] = _adc_read_mv(h, port);
  return rpc_response(doc);  // always the last line of RPC API
}

String bond_max_hdr_dac(int hdr, int port, int mv) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API

  _hdr_t *h = NULL;
  const char *err = _hdr_port(hdr, port, HDR_MODE_DAC, &h);
  if (err) return rpc_error(doc, err);
  if (mv < 0 || mv > HDR_DAC_MV_MAX) return rpc_error(doc, "0 <= mv <= 10000, invalid parameter");

  uint16_t code = _mv_to_code(mv, HDR_DAC_MV_MAX);
  h->max.write_register(dac_data_regs[port], code);

  doc["result"]["dac_raw"] = code;
  doc["result"]["mV"] = mv;
  return rpc_response(doc);  // always the last line of RPC API
}

String bond_max_hdr_gpo(int hdr, int port, bool state) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API

  _hdr_t *h = NULL;
  const char *err = _hdr_port(hdr, port, HDR_MODE_GPO, &h);
  if (err) return rpc_error(doc, err);

  h->max.gpio_write(pixi_ports[port], state ? 1 : 0);
  doc["result"]["state"] = state;
  return rpc_response(doc);  // always the last line of RPC API
}

String bond_max_hdr_gpi(int hdr, int port) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API

  _hdr_t *h = NULL;
  const char *err = _hdr_port(hdr, port, HDR_MODE_GPI, &h);
  if (err) return rpc_error(doc, err);

  uint8_t state = 0;
  h->max.gpio_read(pixi_ports[port], state);
  doc["result"]["state"] = state;
  return rpc_response(doc);  // always the last line of RPC API
}

/* vbus_en
 *  - VBUS on the External USB-C connector, relay RL3 driven by Header 3 port 9, active low
 */
String vbus_en(bool assert) {
  JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API

  _hdr_t *h = NULL;
  const char *err = _hdr_port(HDR_VBUS, HDR_VBUS_PORT, HDR_MODE_GPO, &h);
  if (err) return rpc_error(doc, "HDR3 port 9 is not configured as GPO");

  h->max.gpio_write(pixi_ports[HDR_VBUS_PORT], assert ? 0 : 1);
  doc["result"]["assert"] = assert;
  doc["result"]["level"] = !assert;
  return rpc_response(doc);  // always the last line of RPC API
}
