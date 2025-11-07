/***************************************************
//Web: http://www.buydisplay.com
EastRising Technology Co.,LTD
****************************************************/

#include <Wire.h>
#include "er_oled.h"
#include "Arduino.h"

void I2C_Write_Byte(uint8_t value, uint8_t Cmd)
{
  uint8_t Addr = 0x3c;
  Wire.beginTransmission(Addr);
  Wire.write(Cmd);
  Wire.write(value);
  Wire.endTransmission();
}

void er_oled_begin()
{
    pinMode(OLED_RST, OUTPUT);
    digitalWrite(OLED_RST, HIGH);
    delay(10);
    digitalWrite(OLED_RST, LOW);
    delay(10);
    digitalWrite(OLED_RST, HIGH);

    command(0xAE);//--turn off oled panel
    command(0x02);//---set low column address
    command(0x10);//---set high column address
    command(0x40);//--set start line address  Set Mapping RAM Display Start Line (0x00~0x3F)
    command(0xA1);//--Set SEG/Column Mapping     
    command(0xC8);//Set COM/Row Scan Direction   
    command(0xA6);//--set normal display
    command(0xA8);//--set multiplex ratio(1 to 64)
    command(0x3F);//--1/64 duty
    command(0xD3);//-set display offset    Shift Mapping RAM Counter (0x00~0x3F)
    command(0x00);//-not offset
    command(0xd5);//--set display clock divide ratio/oscillator frequency
    command(0x80);//--set divide ratio, Set Clock as 100 Frames/Sec
    command(0xAD);//--set charge pump
    command(0x8B);  //set Charge Pump enable
    command(0xDA);//--set com pins hardware configuration
    command(0x12);
    command(0x81);//--set contrast control register
    command(0x80);
    command(0xD9);//--set pre-charge period
    command(0x22);//Set Pre-Charge 
    command(0xDB);//--set vcomh
    command(0x40);//Set VCOM Deselect Level
    command(0x20);//-Set Page Addressing Mode (0x00/0x01/0x02)
    command(0x02);//
    command(0xA4);// Disable Entire Display On (0xa4/0xa5)
    command(0xA6);// Disable Inverse Display On (0xa6/a7) 
    command(0xAF);//--turn on oled panel
    delay(10);
}

void er_oled_clear(uint8_t* buffer)
{
	int i;
	for(i = 0;i < OLED_WIDTH * OLED_HEIGHT / 8;i++)
	{
		buffer[i] = 0;
	}
}

void er_oled_pixel(int x, int y, char color, uint8_t* buffer)
{
    if(x > OLED_WIDTH || y > OLED_HEIGHT)return ;
    if(color)
        buffer[x+(y/8)*OLED_WIDTH] |= 1<<(y%8);
    else
        buffer[x+(y/8)*OLED_WIDTH] &= ~(1<<(y%8));
}

void er_oled_char1616(uint8_t x, uint8_t y, uint8_t chChar, uint8_t* buffer)
{
	uint8_t i, j;
	uint8_t chTemp = 0, y0 = y, chMode = 0;

	for (i = 0; i < 32; i++) {
		chTemp = pgm_read_byte(&Font1612[chChar - 0x30][i]);
		for (j = 0; j < 8; j++) {
			chMode = chTemp & 0x80? 1 : 0; 
			er_oled_pixel(x, y, chMode, buffer);
			chTemp <<= 1;
			y++;
			if ((y - y0) == 16) {
				y = y0;
				x++;
				break;
			}
		}
	}
}

void er_oled_char(unsigned char x, unsigned char y, char acsii, char size, char mode, uint8_t* buffer)
{
    unsigned char i, j, y0=y;
    char temp;
    unsigned char ch = acsii - ' ';
    for(i = 0;i<size;i++) {
        if(size == 12)
        {
            if(mode)temp = pgm_read_byte(&Font1206[ch][i]);
            else temp = ~pgm_read_byte(&Font1206[ch][i]);
        }
        else 
        {            
            if(mode)temp = pgm_read_byte(&Font1608[ch][i]);
            else temp = ~pgm_read_byte(&Font1608[ch][i]);
        }
        for(j =0;j<8;j++)
        {
            if(temp & 0x80) er_oled_pixel(x, y, 1, buffer);
            else er_oled_pixel(x, y, 0, buffer);
            temp <<= 1;
            y++;
            if((y-y0) == size)
            {
                y = y0;
                x++;
                break;
            }
        }
    }
}

void er_oled_string(uint8_t x, uint8_t y, const char *pString, uint8_t Size, uint8_t Mode, uint8_t* buffer)
{
    while (*pString != '\0') {       
        if (x > (OLED_WIDTH - Size / 2)) {
            x = 0;
            y += Size;
            if (y > (OLED_HEIGHT - Size)) {
                y = x = 0;
            }
        }
        
        er_oled_char(x, y, *pString, Size, Mode, buffer);
        x += Size / 2;
        pString++;
    }
}

void er_oled_char3216(uint8_t x, uint8_t y, uint8_t chChar, uint8_t* buffer)
{
    uint8_t i, j;
    uint8_t chTemp = 0, y0 = y, chMode = 0;

    for (i = 0; i < 64; i++) {
        chTemp = pgm_read_byte(&Font3216[chChar - 0x30][i]);
        for (j = 0; j < 8; j++) {
            chMode = chTemp & 0x80? 1 : 0; 
            er_oled_pixel(x, y, chMode, buffer);
            chTemp <<= 1;
            y++;
            if ((y - y0) == 32) {
                y = y0;
                x++;
                break;
            }
        }
    }
}

void er_oled_bitmap(uint8_t x,uint8_t y,const uint8_t *pBmp, uint8_t chWidth, uint8_t chHeight, uint8_t* buffer)
{
	uint8_t i, j, byteWidth = (chWidth + 7)/8;
	for(j = 0;j < chHeight;j++){
		for(i = 0;i <chWidth;i++){
			if(pgm_read_byte(pBmp + j * byteWidth + i / 8) & (128 >> (i & 7))){
				er_oled_pixel(x + i,y + j, 1, buffer);
			}
		}
	}		
}

void er_oled_display(uint8_t* pBuf)
{    uint8_t page,i;   
    for (page = 0; page < PAGES; page++) {         
        command(0xB0 + page);/* set page address */     
        command(0x02);   /* set low column address */      
        command(0x10);  /* set high column address */           
        for(i = 0; i< OLED_WIDTH; i++ ) {
          data(pBuf[i+page*OLED_WIDTH]);// write data one
        }        
    }
}
