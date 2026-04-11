#pragma once

#include <Arduino.h>

#include <driver/twai.h>

/** Parsed FTCAN envelope (Layer 2) — emitted before raw frame for every extended ID. */
void emit_ftcan_header_json(Stream& out, const twai_message_t& msg, uint32_t seq);
