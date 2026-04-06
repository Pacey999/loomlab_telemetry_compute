#pragma once

#include <Arduino.h>

#include <driver/twai.h>

void decode_frame(const twai_message_t& msg, uint32_t seq, Stream& out);
