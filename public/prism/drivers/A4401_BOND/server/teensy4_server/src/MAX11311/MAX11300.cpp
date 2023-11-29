/**********************************************************************
* Copyright (C) 2016 Maxim Integrated Products, Inc., All Rights Reserved.
*
* Permission is hereby granted, free of charge, to any person obtaining a
* copy of this software and associated documentation files (the "Software"),
* to deal in the Software without restriction, including without limitation
* the rights to use, copy, modify, merge, publish, distribute, sublicense,
* and/or sell copies of the Software, and to permit persons to whom the
* Software is furnished to do so, subject to the following conditions:
*
* The above copyright notice and this permission notice shall be included
* in all copies or substantial portions of the Software.
*
* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
* OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
* MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
* IN NO EVENT SHALL MAXIM INTEGRATED BE LIABLE FOR ANY CLAIM, DAMAGES
* OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
* ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
* OTHER DEALINGS IN THE SOFTWARE.
*
* Except as contained in this notice, the name of Maxim Integrated
* Products, Inc. shall not be used except as stated in the Maxim Integrated
* Products, Inc. Branding Policy.
*
* The mere transfer of this software does not imply any licenses
* of trade secrets, proprietary technology, copyrights, patents,
* trademarks, maskwork rights, or any other form of intellectual
* property whatsoever. Maxim Integrated Products, Inc. retains all
* ownership rights.
**********************************************************************/

#include "MAX11300.h"


//*********************************************************************
MAX11300::MAX11300()
{
    //empty	
}



//*********************************************************************
void MAX11300::begin(uint8_t mosi, uint8_t miso, uint8_t sclk, uint8_t cs, uint8_t cnvt)
{
	m_mosi = mosi;
	m_miso = miso;
	m_sclk = sclk;
	m_cs = cs;
	m_cnvt = cnvt;
	
	pinMode(m_mosi, OUTPUT);
	pinMode(m_miso, INPUT);
	pinMode(m_sclk, OUTPUT);
	pinMode(m_cs, OUTPUT);
	pinMode(m_cnvt, OUTPUT);
	
	digitalWrite(m_mosi, LOW);
	digitalWrite(m_sclk, LOW);
	digitalWrite(m_cs, HIGH);
	digitalWrite(m_cnvt, HIGH);
	delayMicroseconds(1);
	init();
}

void MAX11300::shiftOutMAX(uint8_t dataPin, uint8_t clockPin, uint8_t bitOrder, byte val)
{
      int i;

      for (i = 0; i < 8; i++)  {
            if (bitOrder == LSBFIRST) {
                  digitalWrite(dataPin, !!(val & (1 << i)));
            } else {
                  digitalWrite(dataPin, !!(val & (1 << (7 - i))));
            }
            delayMicroseconds(1);

            digitalWrite(clockPin, HIGH);
            delayMicroseconds(2);
            digitalWrite(clockPin, LOW);
            delayMicroseconds(1);
      }
}

uint8_t MAX11300::shiftInMAX(uint8_t dataPin, uint8_t clockPin, uint8_t bitOrder)
{
    uint8_t value = 0;
    uint8_t i;

    for (i = 0; i < 8; ++i) {
        digitalWrite(clockPin, HIGH);
        delayMicroseconds(2);
        if (bitOrder == LSBFIRST)
            value |= digitalRead(dataPin) << i;
        else
            value |= digitalRead(dataPin) << (7 - i);
        digitalWrite(clockPin, LOW);
        delayMicroseconds(2);
    }
    return value;
}

//*********************************************************************
void MAX11300::write_register(MAX11300RegAddress_t reg, uint16_t data)
{
    digitalWrite(m_cs, LOW);
    delayMicroseconds(1);
	shiftOutMAX(m_mosi, m_sclk, MSBFIRST, MAX11300Addr_SPI_Write(reg));
	shiftOutMAX(m_mosi, m_sclk, MSBFIRST, ((0xFF00 & data) >> 8));
	shiftOutMAX(m_mosi, m_sclk, MSBFIRST, (0x00FF & data));
    digitalWrite(m_cs, HIGH);
	delayMicroseconds(1);
}

//*********************************************************************    
uint16_t MAX11300::read_register(MAX11300RegAddress_t reg)
{
    uint16_t rtn_val = 0;
    
    digitalWrite(m_cs, LOW);
    delayMicroseconds(1);
    shiftOutMAX(m_mosi, m_sclk, MSBFIRST, MAX11300Addr_SPI_Read(reg));
	rtn_val |= (shiftInMAX(m_miso, m_sclk, MSBFIRST) << 8);
	rtn_val |= shiftInMAX(m_miso, m_sclk, MSBFIRST);
    digitalWrite(m_cs, HIGH);
	delayMicroseconds(1);

    return rtn_val;
}

//*********************************************************************
MAX11300RegAddressEnum MAX11300::_get_adc_data_port(MAX11300_Ports port)
{
    switch(port) {
    case PIXI_PORT0: return adc_data_port_00;
    case PIXI_PORT1: return adc_data_port_01;
    case PIXI_PORT2: return adc_data_port_02;
    case PIXI_PORT3: return adc_data_port_03;
    case PIXI_PORT4: return adc_data_port_04;
    case PIXI_PORT5: return adc_data_port_05;
    case PIXI_PORT6: return adc_data_port_06;
    case PIXI_PORT7: return adc_data_port_07;
    case PIXI_PORT8: return adc_data_port_08;
    case PIXI_PORT9: return adc_data_port_09;
    case PIXI_PORT10: return adc_data_port_10;
    case PIXI_PORT11: return adc_data_port_11;
    default:
        return adc_data_port_00;
    }
}

//*********************************************************************
MAX11300RegAddressEnum MAX11300::_get_dac_data_port(MAX11300_Ports port)
{
    switch(port) {
    case PIXI_PORT0: return dac_data_port_00;
    case PIXI_PORT1: return dac_data_port_01;
    case PIXI_PORT2: return dac_data_port_02;
    case PIXI_PORT3: return dac_data_port_03;
    case PIXI_PORT4: return dac_data_port_04;
    case PIXI_PORT5: return dac_data_port_05;
    case PIXI_PORT6: return dac_data_port_06;
    case PIXI_PORT7: return dac_data_port_07;
    case PIXI_PORT8: return dac_data_port_08;
    case PIXI_PORT9: return dac_data_port_09;
    case PIXI_PORT10: return dac_data_port_10;
    case PIXI_PORT11: return dac_data_port_11;
    default:
        return dac_data_port_00;
    }
}

//*********************************************************************
void MAX11300::block_write(MAX11300RegAddress_t reg, uint16_t * data, uint8_t num_reg)
{
    for(uint8_t idx = 0; idx < num_reg; idx++)
    {
        write_register(static_cast<MAX11300RegAddress_t>(reg + idx), data[idx]);
    }
}

//*********************************************************************        
void MAX11300::block_read(MAX11300RegAddress_t reg, uint16_t * data, uint8_t num_reg)
{
    for(uint8_t idx = 0; idx < num_reg; idx++)
    {
        data[idx] = read_register(static_cast<MAX11300RegAddress_t>(reg + idx));
    }
}

//*********************************************************************    
MAX11300::CmdResult MAX11300::gpio_write(MAX11300_Ports port, uint8_t state)
{
    MAX11300::CmdResult result = MAX11300::OpFailure;
    uint16_t temp;
    uint16_t port_mask;
    
    if (port != MAX11300::PIXI_PORT11)
    {
        port_mask = (1 << port);
        temp = read_register(gpo_data_10_to_0);
        if(state & 0x01)
        {
            temp |= port_mask;
        }
        else
        {
            temp &= ~port_mask;
        }
        write_register(gpo_data_10_to_0, temp);
    }
    else
    {
        port_mask = 0x1;
        temp = read_register(gpo_data_11);
        if(state & 0x01)
        {
            temp |= port_mask;
        }
        else
        {
            temp &= ~port_mask;
        }
        write_register(gpo_data_11, temp);
    }

    //result = MAX11300::Success;

    return result;
}

//*********************************************************************
MAX11300::CmdResult MAX11300::gpio_read(MAX11300_Ports port, uint8_t &state)
{
    MAX11300::CmdResult result = MAX11300::OpFailure;
    
    if(port != MAX11300::PIXI_PORT11)
    {
        state = (read_register(gpi_data_10_to_0) >> port);
    }
    else
    {
        state = (read_register(gpi_data_11) >> (port - MAX11300::PIXI_PORT11));
    }

    result = MAX11300::Success;

    return result;
}

//*********************************************************************
MAX11300::CmdResult MAX11300::single_ended_adc_read(MAX11300_Ports port, uint16_t *data)
{
    MAX11300::CmdResult result = MAX11300::OpFailure;
    uint8_t num_samples = 1;

    while(num_samples--)
    {
        digitalWrite(m_cnvt, LOW);
        delayMicroseconds(100);
        digitalWrite(m_cnvt, HIGH);
        delayMicroseconds(100);
    }
    *data = read_register(_get_adc_data_port(port));

    result = MAX11300::Success;
    return result;
}

//*********************************************************************
MAX11300::CmdResult MAX11300::single_ended_dac_write(MAX11300_Ports port, uint16_t data)
{
    MAX11300::CmdResult result = MAX11300::OpFailure;
    
    write_register(_get_dac_data_port(port), data);
    result = MAX11300::Success;

    return result;
}

//*********************************************************************
void MAX11300::init(void)
{

}

