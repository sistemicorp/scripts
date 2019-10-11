#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corp, copyright, all rights reserved, 2019

"""
UPYB_I2C_HW_I2C1 = "X"   # on X9/10 <<-- only this one used on iba01
UPYB_I2C_HW_I2C2 = "Y"   # on Y9/10

V1_I2C_ADDR   = 0x20   # addr of GPIO expander controlling the LDO V1
V2_I2C_ADDR   = 0x21   # addr of GPIO expander controlling the LDO V2
VBAT_I2C_ADDR = 0x22   # addr of GPIO expander controlling the LDO VBAT
CON_I2C_ADDR  = 0x23   # addr of GPIO expander controlling the 9V, Relays

# PCA9535 GPIO Expander registers
PCA9555_CMD_INPUT_P0 = 0x0
PCA9555_CMD_INPUT_P1 = 0x1
PCA9555_CMD_OUTPUT_P0 = 0x2
PCA9555_CMD_OUTPUT_P1 = 0x3
PCA9555_CMD_POL_P0 = 0x4
PCA9555_CMD_POL_P1 = 0x5
PCA9555_CMD_CONFIG_P0 = 0x6
PCA9555_CMD_CONFIG_P1 = 0x7