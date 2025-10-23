/**  Sistemi Corporation, Martin Guthrie
*/
#ifndef CYPD3176_H
#define CYPD3176_H

#include <stdint.h>   // uint16_t, etc.

#include <Arduino.h>
#include <Wire.h>     // TwoWire

namespace CYPD3176 {

  class CYPD3176
  {
    public:
      // i2cAddress is the default address when A0, A1 and A2 is tied low
      explicit CYPD3176(TwoWire& wire, uint8_t i2cAddress = 0x48);

      void begin();
      uint16_t getDeviceId();
    private:
      TwoWire& wire;
      void writeRegister(uint8_t reg, uint16_t value);
      void writeRegister(uint8_t reg, uint8_t value);
      uint16_t readRegister(uint8_t reg);
      uint8_t i2cAddress;
  };
}
#endif    // CYPD3176_H
