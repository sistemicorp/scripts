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
