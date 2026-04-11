#pragma once

#include <Arduino.h>

#include <driver/twai.h>

/** Emit Layer-2 JSON (`type":"header"`) for every extended frame — no product-band gate. */
void emit_ftcan_header_json(Stream& out, const twai_message_t& msg, uint32_t seq);
