#include <simpleRPC.h>
#include <ArduinoJson.h>

#define RESPONSE_BUFFER_SIZE 200

void setup(void) {
  Serial.begin(9600);
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop(void) {
  interface(
    Serial,
    teensy_Reset, "teensy_reset: Resets Teensy.",
    unique_id, "unique_id: Shows Teensy's unique id",
    slot, "slot: Shows the Teensy's id so you know which Teensy you are using",
    setLed, "set_led: Set LED ON/OFF.",
    currVersion, "version: Shows current version.");
}

String unique_id() {
  char buffer[RESPONSE_BUFFER_SIZE];
  DynamicJsonDocument doc = helper();

  doc["result"]["unique_id"] = "12345";
  serializeJsonPretty(doc, buffer);
  return buffer;
}

String slot() {
  char buffer[RESPONSE_BUFFER_SIZE];
  DynamicJsonDocument doc = helper();

  doc["result"]["id"] = 1;
  serializeJsonPretty(doc, buffer);
  return buffer;
}

String setLed(bool on) {
  char buffer[RESPONSE_BUFFER_SIZE];
  DynamicJsonDocument doc = helper();

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
  //serializeJsonPretty(doc, buffer);
  return serialize(doc, buffer);
}

String currVersion(){
 char buffer[RESPONSE_BUFFER_SIZE];
 DynamicJsonDocument doc = helper();

 doc["result"]["version"] = "0.1.0";
 serializeJsonPretty(doc, buffer);
 return buffer;
}

String teensy_Reset(){
  char buffer[RESPONSE_BUFFER_SIZE];
  DynamicJsonDocument doc = helper();

  doc["result"]["action"] = "reset";
  serializeJsonPretty(doc, buffer);
  return buffer;
}

DynamicJsonDocument helper(){
  DynamicJsonDocument doc(RESPONSE_BUFFER_SIZE);
  doc["success"] = true;
  JsonObject result = doc.createNestedObject("result");
  return doc;
}

String serialize(DynamicJsonDocument doc, char buffer[]){
  unsigned int s = serializeJsonPretty(doc, buffer, RESPONSE_BUFFER_SIZE);
  if (s == RESPONSE_BUFFER_SIZE) {
    doc["success"] = false;
    doc["result"]["action"] = "RPC buffer response overrun";
    char bufferV2[RESPONSE_BUFFER_SIZE];
    serializeJsonPretty(doc, bufferV2);
    return bufferV2;
    // need to start all over, the buffer is overrun (not big enough)..
    // we want to send back success=false, and we want to tell the client a message, "rpc buffer response overrun"
  }
  else{
    return buffer;
  }
}