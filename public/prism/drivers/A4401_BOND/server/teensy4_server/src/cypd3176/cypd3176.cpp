/**  Sistemi Corporation, Martin Guthrie
 *
 * Refer to https://www.infineon.com/assets/row/public/documents/24/44/infineon-ez-pd-tm-bcr-plus-bcr-lite-host-processor-interface-specification-cypd3176-cypd3178-usermanual-en.pdf
 *
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

  uint16_t CYPD3176::readRegisterHWord(const uint16_t pointerRegister) {
    this->wire.beginTransmission(this->i2cAddress);
    this->wire.write(pointerRegister);
    this->wire.endTransmission(false);
    this->wire.requestFrom(this->i2cAddress, (uint8_t)2, (uint8_t)true);

    uint16_t result = 0;
    uint8_t shift = 0;
    while (Wire.available()) { // While there are bytes available to read
      uint8_t c = Wire.read();    // Read a byte
      result |= (c << shift);     // Shift the bits over and add to the result
      shift += 8;                // Increment the shift counter
    }

    // write to INTERRUPT register to clear???
    this->wire.beginTransmission(this->i2cAddress);
    this->wire.write(0x0006);
    this->wire.endTransmission(true);

    return result;
  }

  uint8_t CYPD3176::readRegisterByte(const uint16_t pointerRegister) {
    this->wire.beginTransmission(this->i2cAddress);
    this->wire.write(pointerRegister);
    this->wire.endTransmission(false);
    this->wire.requestFrom(this->i2cAddress, (uint8_t)1, (uint8_t)true);
    uint16_t result = 0;
    uint8_t shift = 0;
    while (Wire.available()) { // While there are bytes available to read
      uint8_t c = Wire.read();    // Read a byte
      result |= (c << shift);     // Shift the bits over and add to the result
      shift += 8;                // Increment the shift counter
    }

    // write to INTERRUPT register to clear???
    this->wire.beginTransmission(this->i2cAddress);
    this->wire.write(0x0006);
    this->wire.endTransmission(true);

    return result;
  }

  uint32_t CYPD3176::readRegisterWord(const uint16_t pointerRegister) {
    this->wire.beginTransmission(this->i2cAddress);
    this->wire.write(pointerRegister);
    this->wire.endTransmission(false);
    this->wire.requestFrom(this->i2cAddress, (uint8_t)4, (uint8_t)true);
    uint16_t result = 0;
    uint8_t shift = 0;
    while (Wire.available()) { // While there are bytes available to read
      uint8_t c = Wire.read();    // Read a byte
      result |= (c << shift);     // Shift the bits over and add to the result
      shift += 8;                // Increment the shift counter
    }

    // write to INTERRUPT register to clear???
    this->wire.beginTransmission(this->i2cAddress);
    this->wire.write(0x0006);
    this->wire.endTransmission(true);

    return result;
  }

  // ALWAYS WORKS
  uint16_t CYPD3176::getDeviceId() {
    return (uint16_t)(this->readRegisterHWord(0x0002));
  }

  // FIXME: Does not work, always returns 0
  //        See https://community.infineon.com/t5/EZ-PD-USB-Type-C/CYPD3177-I2C-communication-no-response/td-p/909323
  //        Note the Usermanual (link at top) Section 3.5 seems to indicate that we need to write to
  //        INTERRUPT register to clear after every other register read.
  //        Or, see usermanual section 4.6.1 where it might be that one has to set a request to read some
  //        of these registers.
  uint32_t CYPD3176::getBusVoltageMV() {
    uint8_t units_100mV = this->readRegisterByte(0x100d);
    return ((uint32_t)units_100mV * 100u);
  }

  // FIXME: Does not work, always returns 0
  uint32_t CYPD3176::getCStatus() {
    return (uint32_t)(this->readRegisterWord(0x100c));
  }

  // ALWAYS WORKS
  uint32_t CYPD3176::getPDResponse() {
    return (uint32_t)(this->readRegisterWord(0x1400));
  }

  // ALWAYS WORKS
  uint16_t CYPD3176::getDevResponse() {
    return (uint16_t)(this->readRegisterHWord(0x007e));
  }


}   // namespace CYPD3176
