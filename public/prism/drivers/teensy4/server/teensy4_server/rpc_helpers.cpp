/*  Sistemi Corporation, copyright, all rights reserved, 2021-2026
 *  Martin Guthrie
 *
 *  RPC response helpers, see rpc_helpers.h
 */
#include "rpc_helpers.h"

static JsonDocument doc;

/* rpc_begin
 * - sets up (initializes) the response document for an RPC function
 * - the RPC is assumed to succeed, rpc_error() marks it failed
 */
JsonDocument &rpc_begin(const char *method) {
  doc.clear();
  doc["success"] = true;
  doc["method"] = method;
  doc["result"].to<JsonObject>();
  return doc;
}

/* rpc_response
 * - serializes the response document into the String returned to the caller
 */
String rpc_response(JsonDocument &doc) {
  if (measureJson(doc) > RPC_RESPONSE_MAX) {
    const char *method = doc["method"].as<const char *>();
    String m = method ? method : "";
    doc.clear();
    doc["success"] = false;
    doc["method"] = m;
    doc["result"]["error"] = "RPC response too long";
  }

  String s;
  serializeJson(doc, s);
  return s;
}

/* rpc_error
 * - marks the RPC failed with an error string, and returns the response
 */
String rpc_error(JsonDocument &doc, const char *error) {
  doc["success"] = false;
  doc["result"]["error"] = error;
  return rpc_response(doc);
}
