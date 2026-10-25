/*  Sistemi Corporation, copyright, all rights reserved, 2021-2026
 *  Martin Guthrie
 *
 *  BOND on-board I2C devices shared by several modules, defined in bond_board.cpp
 */
#pragma once

#include <INA226_WE.h>
#include "src/tmp1075/TMP1075.h"
#include "src/cypd3176/cypd3176.h"

#define INA226_VBAT_I2C_ADDRESS 0x40
#define INA226_VDUT_I2C_ADDRESS 0x41
#define INA226_VBAT_SHUNT_OHMS  0.2f
#define INA226_VDUT_SHUNT_OHMS  0.2f
#define INA226_CURRENT_RANGE_A  1.0f

extern INA226_WE ina226_vbat;
extern INA226_WE ina226_vdut;
extern TMP1075::TMP1075 tmp1075;
extern CYPD3176::CYPD3176 cypd3176;

uint16_t ina226_read_mv(INA226_WE &ina);
