/*  Sistemi Corporation, copyright, all rights reserved, 2021-2023
 *  Martin Guthrie
 *  
 *  Functions related to Teensy's internal capabilities
*/

#define BIST_VOLTAGE_V3V3A_NAME            "V3V3A"
#define BIST_VOLTAGE_V3V3D_NAME            "V3V3D"
#define BIST_VOLTAGE_V5V_NAME              "V5V"
#define BIST_VOLTAGE_V6V_NAME              "V6V"
#define BIST_VOLTAGE_ADC_SAMPLES           10
#define BIST_VOLTAGE_ADC_SAMPLE_RATE_MS    2

unsigned int _read_adc(unsigned int pin_number, unsigned int sample_num, unsigned int sample_rate) {
  unsigned long currentMillis = millis();
  unsigned long previousMillis = 0;  // =0 causes sample to be taken right away
  unsigned int accumulator = 0;
  unsigned int counter = sample_num;

  while (counter) {
    if ((currentMillis - previousMillis) >= sample_rate) {
      accumulator += analogRead(pin_number);
      previousMillis = currentMillis;
      counter--;
    }
    currentMillis = millis();
  }

  return (unsigned int)(accumulator / sample_num);
}
/* read_adc
 *  - read ADC value on a Teensy pin
 *  
 *  unsigned int pin_number: GPIO number
 *  unsigned int sample_num: number of samples which to average over
 *  unsigned int sample_rate: milliseconds between samples
 */
String read_adc(unsigned int pin_number, unsigned int sample_num, unsigned int sample_rate) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API

  doc["result"]["reading"] = _read_adc(pin_number, sample_num, sample_rate);

  return _response(doc);  // always the last line of RPC API
}

/* init_gpio
 *  - intit GPIO mode
 *  
 * int pin_number: GPIO number
 * String& mode: <"INPUT"|"OUTPUT"|"INPUT_PULLUP">
 */
String init_gpio(int pin_number, String& mode) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  
  if(mode == "INPUT"){
    pinMode(pin_number, INPUT);
  }
  else if(mode == "OUTPUT"){
    pinMode(pin_number, OUTPUT);
  }
  else if(mode == "INPUT_PULLUP"){
    pinMode(pin_number, INPUT_PULLUP);
  }
  doc["result"]["mode"] = mode;
 
  return _response(doc);  // always the last line of RPC API
}

/* set_led
 *  - turn LED that is on the Teensy module on or off
 *  
 *  bool on: <true|false>
 */
String set_led(bool on) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  
  if (on) {
    doc["result"]["state"] = "on";
    digitalWrite(LED_BUILTIN, HIGH);
  } else {
    doc["result"]["state"] = "off";
    digitalWrite(LED_BUILTIN, LOW);
  }
  
  return _response(doc);  // always the last line of RPC API
}

/* read_gpio
 *  - read state of GPIO
 *  
 * int pin_number: GPIO number
 */
String read_gpio(int pin_number) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API

  doc["result"]["state"] = digitalRead(pin_number);

  return _response(doc);  // always the last line of RPC API
}

/* write_gpio
 *  - read state of GPIO
 *  
 * int pin_number: GPIO number
 * bool state: <true|false>
 */
String write_gpio(int pin_number, bool state) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API

  digitalWrite(pin_number, state);

  doc["result"]["state"] = state;

  return _response(doc);  // always the last line of RPC API
}

/* bist_voltage
 *  - built in self-test (bist) read voltage
 *  
 * String name: name of voltage, one of BIST_VOLTAGE_*_NAME, see schematic
 */
String bist_voltage(String name) {
  DynamicJsonDocument doc = _helper(__func__);  // always first line of RPC API
  doc["result"]["name"] = name;

  unsigned int mv = 0;
  unsigned int pin = 0;
  char *p = const_cast<char*>(name.c_str());

  if (strcmp(p, BIST_VOLTAGE_V3V3A_NAME) == 0) {
    pin = BIST_VOLTAGE_V3V3A_PIN;

  } else if (strcmp(p, BIST_VOLTAGE_V3V3D_NAME) == 0) {
    pin = BIST_VOLTAGE_V3V3D_PIN;

  } else if (strcmp(p, BIST_VOLTAGE_V5V_NAME) == 0) {
    pin = BIST_VOLTAGE_V5V_PIN;

  } else if (strcmp(p, BIST_VOLTAGE_V6V_NAME) == 0) {
    pin = BIST_VOLTAGE_V6V_PIN;

  } else {
    doc["result"]["error"] = "Unknown name";
    doc["success"] = false;
    return _response(doc);
  }

  unsigned int adc_raw = _read_adc(pin, BIST_VOLTAGE_ADC_SAMPLES, BIST_VOLTAGE_ADC_SAMPLE_RATE_MS);
  mv = (adc_raw * 3300 * 3) / 1024;  // * 3 for resistor divider, 10k / (10k + 20k)
  doc["result"]["mv"] = mv;

  return _response(doc);  // always the last line of RPC API
}
