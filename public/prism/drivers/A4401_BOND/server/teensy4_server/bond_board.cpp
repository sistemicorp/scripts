/*  Sistemi Corporation, copyright, all rights reserved, 2021-2026
 *  Martin Guthrie
 *
 *  BOND on-board I2C devices, see bond_board.h
 */
#include <Wire.h>
#include "bond_board.h"

INA226_WE ina226_vbat = INA226_WE(INA226_VBAT_I2C_ADDRESS);
INA226_WE ina226_vdut = INA226_WE(INA226_VDUT_I2C_ADDRESS);
TMP1075::TMP1075 tmp1075 = TMP1075::TMP1075(Wire);
CYPD3176::CYPD3176 cypd3176 = CYPD3176::CYPD3176(Wire);

/* ina226_read_mv
 * - triggered single measurement of the bus voltage, in mV
 */
uint16_t ina226_read_mv(INA226_WE &ina) {
  ina.startSingleMeasurement();
  float v = ina.getBusVoltage_V();
  return (uint16_t)(v * 1000.0f);
}
