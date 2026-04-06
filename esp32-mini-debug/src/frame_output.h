#pragma once

#include <Arduino.h>

#include <driver/twai.h>

void emit_raw_frame(Stream& out, const twai_message_t& msg, uint32_t ts_ms, uint32_t seq);
