#pragma once

#include <driver/twai.h>

/** Best-effort decode of three FTCAN channels for sanity (JSONL on success). */
void try_mini_decode(const twai_message_t& msg);
