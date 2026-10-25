/*  Sistemi Corporation, copyright, all rights reserved, 2021-2026
 *  Martin Guthrie
 *
 *  BOND (a4402) Teensy 4.1 pin assignments, see schematic a4402-SCH_05, Teensy4 sheet.
 */
#pragma once

#define BUTTON1_PIN             6   // Jig Closed Detection, reads 1 when the jig is closed
#define BUTTON2_PIN             7   // User defined
#define MAX11311_CONVERT_Pin    8   // schematic name ADC_CNVRT, shared by all MAX11311s
#define VDUT_SMPS_EN_PIN        10  // schematic name VDUTSMPS_EN
#define VDUT_CONNECT_PIN        11  // schematic name VDUT_EN
#define BIST_VOLTAGE_V3V3D_PIN  22  // ADC input
#define BIST_VOLTAGE_V3V3A_PIN  23  // ADC input
#define BIST_VOLTAGE_V6V_PIN    24  // ADC input
#define BIST_VOLTAGE_V5V_PIN    25  // ADC input
#define SPI_MOSI_Pin            26
#define SPI_SCLK_Pin            27
#define VSYS_EN_PIN             31
#define SPI_CS_IOX_Pin          33
#define SPI_CS2_HDR4_Pin        34
#define SPI_CS_HDR4_Pin         35
#define SPI_CS_HDR3_Pin         36
#define SPI_CS_HDR2_Pin         37
#define SPI_CS_HDR1_Pin         38
#define SPI_MISO_Pin            39
#define VDUTSMPS_INT            40
#define BIST_VOLTAGE_NEG2V5_PIN 41  // ADC input

#define GPIO_NUMBER_MAX         41  // highest Teensy GPIO number accepted by the GPIO RPCs
