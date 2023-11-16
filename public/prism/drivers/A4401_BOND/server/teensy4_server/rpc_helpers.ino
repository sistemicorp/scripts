//-------------------------------------------------------------------------------------------------------------
// RPC Helper Functions
// - these functions are related to the simpleRPC library
// 

#define RESPONSE_BUFFER_SIZE 400
DynamicJsonDocument doc(RESPONSE_BUFFER_SIZE);

/* _helper
 * - sets up (intializes) response document for any RPC function
 * - every RPC function should call this function first
 */
DynamicJsonDocument _helper(String f){
  doc.clear();
  doc["success"] = true;  // ASSUME RPC call was a success, called must set to false if there was error
  doc["method"] = f;
  JsonObject result = doc.createNestedObject("result");
  (void)result;
  return doc;
}

/* _response
 * - every RPC function "returns" thru this function
 * - serializes DynamicJsonDocument into a string that is 
 *   returned to the caller
 */
String _response(DynamicJsonDocument doc){
  char buffer[RESPONSE_BUFFER_SIZE];
  int s = serializeJsonPretty(doc, buffer);
  if (s >= (RESPONSE_BUFFER_SIZE-1)){
    doc.clear();
    doc["success"] = false;
    doc["result"]["error"] = "RPC buffer response overrun";
    serializeJsonPretty(doc, buffer);
  } else if (s < 0) {
    doc.clear();
    doc["success"] = false;
    char buf[30];
    doc["result"]["error"] = snprintf(buf, 30, "serializeJsonPretty %d", s);
    serializeJsonPretty(doc, buffer);    
  }
  return buffer;
}
