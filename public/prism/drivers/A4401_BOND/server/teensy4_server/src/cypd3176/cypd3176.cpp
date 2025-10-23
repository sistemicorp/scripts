/**  Sistemi Corporation, Martin Guthrie
*/
#include "cypd3176.h"

namespace CYPD3176 {
  CYPD3176::CYPD3176(TwoWire& _wire, const uint8_t _i2cAddress): wire(_wire), i2cAddress(_i2cAddress) {}

  void CYPD3176::begin()
  {

  }

  void CYPD3176::writeRegister(const uint8_t pointerRegister, const uint16_t value) {
    this->wire.beginTransmission(this->i2cAddress);
    this->wire.write(pointerRegister);
    this->wire.write((value >> 8) & 0xFF);
    this->wire.write((value >> 0) & 0xFF);
    this->wire.endTransmission();
  }

  void CYPD3176::writeRegister(const uint8_t pointerRegister, const uint8_t value) {
    this->wire.beginTransmission(this->i2cAddress);
    this->wire.write(pointerRegister);
    this->wire.write(value);
    this->wire.endTransmission();
  }

  uint16_t CYPD3176::readRegister(const uint8_t pointerRegister) {
    this->wire.beginTransmission(this->i2cAddress);
    this->wire.write(pointerRegister);
    this->wire.endTransmission(false);
    this->wire.requestFrom(this->i2cAddress, (uint8_t)2, (uint8_t)true);
    return this->wire.read() << 8 | this->wire.read();
  }

}   // namespace TMP1075
