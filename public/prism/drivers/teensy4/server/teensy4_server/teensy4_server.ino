#include <simpleRPC.h>
#include <ArduinoJson.h>
#include "version.h"

#define RESPONSE_BUFFER_SIZE 200
#define MAC_SIZE 6

//-------------------------------------------------------------------------------------------------------------
//simpleRPC Functions

String unique_id() {
  DynamicJsonDocument doc = _helper(__func__);
  
  uint8_t mac_address[MAC_SIZE];
  
  doc["result"]["unique_id"] = _teensyMAC(mac_address);
  return _response(doc);
}

String slot() {
  DynamicJsonDocument doc = _helper(__func__); 

  doc["result"]["id"] = 1;
  return _response(doc);
}

String set_led(bool on) {
  DynamicJsonDocument doc = _helper(__func__);
  
  if (on){
    doc["result"]["state"] = "on";
    if (digitalRead(LED_BUILTIN) == LOW){
      digitalWrite(LED_BUILTIN, HIGH);
    }
  }
  else{
    doc["result"]["state"] = "off";
    if (digitalRead(LED_BUILTIN) == HIGH){
      digitalWrite(LED_BUILTIN, LOW);
    }
  }
  return _response(doc);
}

String version(){
 DynamicJsonDocument doc = _helper(__func__);
 
 doc["result"]["version"] = VERSION;
 return _response(doc);
}

String read_adc(int pin_number, int sample_num, int sample_rate){
  DynamicJsonDocument doc = _helper(__func__);

  unsigned long currentMillis = millis();
  unsigned long previousMillis = 0;
  double reading = 0;

  for(int count = 0; count <= sample_num; count++){
    if(currentMillis - previousMillis >= sample_rate){
      reading += analogRead(pin_number);
      previousMillis = currentMillis;
    }
  }

  reading = reading/sample_num;
  doc["result"]["reading"] = reading;

  return _response(doc);
}

String init_gpio(int pin_number, String& mode){
  DynamicJsonDocument doc = _helper(__func__);
  
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
 
  return _response(doc);
}

String read_gpio(int pin_number){
  DynamicJsonDocument doc = _helper(__func__);

  doc["result"]["state"] = digitalRead(pin_number);

  return _response(doc);
}

String write_gpio(int pin_number, bool state){
  DynamicJsonDocument doc = _helper(__func__);

  digitalWrite(pin_number, state);

  doc["result"]["state"] = state;

  return _response(doc);
}

String reset(){
  DynamicJsonDocument doc = _helper(__func__);

  // ... add any required resetting code here ...
  
  return _response(doc);
}

//-------------------------------------------------------------------------------------------------------------
//Helper Functions

DynamicJsonDocument _helper(String f){
  DynamicJsonDocument doc(RESPONSE_BUFFER_SIZE);
  doc["success"] = true;
  doc["method"] = f;
  JsonObject result = doc.createNestedObject("result");
  return doc;
}

String _response(DynamicJsonDocument doc){
  char buffer[RESPONSE_BUFFER_SIZE];
  int s = serializeJsonPretty(doc, buffer);
  if (s >= (RESPONSE_BUFFER_SIZE-1)){
    doc.clear();
    doc["success"] = false;
    doc["result"]["error"] = "RPC buffer response overrun";
    serializeJsonPretty(doc, buffer);
  }
  return buffer;
}

String _teensyMAC(uint8_t *mac){
    uint32_t m1 = HW_OCOTP_MAC1;
    uint32_t m2 = HW_OCOTP_MAC0;
    mac[0] = m1 >> 8;
    mac[1] = m1 >> 0;
    mac[2] = m2 >> 24;
    mac[3] = m2 >> 16;
    mac[4] = m2 >> 8;
    mac[5] = m2 >> 0;

    char unique_id[18];

    snprintf(unique_id, sizeof(unique_id), "%02x:%02x:%02x:%02x:%02x:%02x", mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    
    return unique_id;
}

//-------------------------------------------------------------------------------------------------------------
//set-up/loop Functions

void setup(void) {
  Serial.begin(9600);
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop(void) {
  interface(
    Serial,
    unique_id, "unique_id: Shows Teensy's unique id",
    slot, "slot: Shows the Teensy's slot to differentiate multiple Teensys",
    set_led, "set_led: Set LED (ON/OFF).",
    version, "version: Shows current version.",
    read_adc, "read_adc: Reads analog pin.",
    init_gpio, "init_gpio: Initializes GPIO (INPUT, INPUT_PULLUP, OUTPUT).",
    read_gpio, "read_gpio: Reads GPIO (HIGH or LOW).",
    write_gpio, "write_gpio: Writes GPIO (HIGH or LOW).",
    reset, "reset: Resets Teensy.");
}
