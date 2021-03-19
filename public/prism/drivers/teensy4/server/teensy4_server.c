#include <simpleRPC.h>
#include <ArduinoJson.h>

#define RESPONSE_BUFFER_SIZE 200
#define MAC_SIZE 6

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
    init_gpio,"init_gpio: initializes GPIO (INPUT, INPUT_PULLUP, OUTPUT).",
    reset, "reset: Resets Teensy.");
}

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

 doc["result"]["version"] = "0.1.0";
 return _response(doc);
}

String init_gpio(int pin_number, String& mode){
  DynamicJsonDocument doc = _helper(__func__);

  //mode.toUpperCase();

  if(pin_number >= 0 && pin_number <= 41){
    if(mode == "INPUT"){
      pinMode(pin_number, INPUT);
    }
    else if(mode == "OUTPUT"){
      pinMode(pin_number, OUTPUT);
    }
    else if(mode == "INPUT_PULLUP"){
      pinMode(pin_number, INPUT_PULLUP);
    }
    else{
      doc["success"] = false;
      doc["result"]["error"] = "invalid pin mode";
    }
  }
  else{
      doc["success"] = false;
      doc["result"]["error"] = "invalid pin number";
  }

  if(doc["success"]){
      String pin_n = String(pin_number);
      String init = "Set pin ";
      init += pin_n;
      init += " to ";
      init += mode;
      doc["result"]["init"] = init;
  }
  return _response(doc);
}

String reset(){
  DynamicJsonDocument doc = _helper(__func__);

  return _response(doc);
}

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