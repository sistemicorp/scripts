/*  Sistemi Corporation, copyright, all rights reserved, 2021-2026
 *  Martin Guthrie
 *
 *  RPC response helpers for the simpleRPC API.
 *
 *  Every RPC function has the same shape,
 *
 *      String my_rpc(int arg) {
 *        JsonDocument &doc = rpc_begin(__func__);  // always first line of RPC API
 *        if (bad arg) return rpc_error(doc, "bad arg");
 *        doc["result"]["value"] = 42;
 *        return rpc_response(doc);  // always the last line of RPC API
 *      }
 *
 *  There is one response document, so an RPC function must never call another
 *  RPC function. Call the module's internal (non RPC) function instead.
 */
#pragma once

#include <Arduino.h>
#include <ArduinoJson.h>

#define RPC_RESPONSE_MAX  200  // largest serialized response, in chars

JsonDocument &rpc_begin(const char *method);
String rpc_response(JsonDocument &doc);
String rpc_error(JsonDocument &doc, const char *error);
