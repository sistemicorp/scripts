/**  Sistemi Corporation, Martin Guthrie
 *
 * Note:
 * https://community.infineon.com/t5/EZ-PD-USB-Type-C/CYPD3177-I2C-communication-no-response/td-p/909323
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
      explicit CYPD3176(TwoWire& wire, uint8_t i2cAddress = 0x08);

      void begin();
      uint16_t getDeviceId();
      uint32_t getBusVoltageMV();
      uint32_t getCStatus();
      uint16_t getDevResponse();
      uint32_t getPDResponse();

    private:
      TwoWire& wire;
      void writeRegister(uint8_t reg, uint16_t value);
      void writeRegister(uint8_t reg, uint8_t value);
      uint8_t readRegisterByte(const uint16_t pointerRegister);
      uint16_t readRegisterHWord(const uint16_t pointerRegister);
      uint32_t readRegisterWord(const uint16_t pointerRegister);
      uint8_t i2cAddress;
  };
}
#endif    // CYPD3176_H
