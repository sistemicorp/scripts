/*  Sistemi Corporation, copyright, all rights reserved, 2021-2026
 *  Martin Guthrie
 *
 *  BOND reset (DUT safe state) and power up self test
 */
#pragma once

#include <Arduino.h>

// internal API, use these from other modules, never the RPC functions
void bond_reset(void);
int bond_self_test(void);

// RPC API
String reset(void);
