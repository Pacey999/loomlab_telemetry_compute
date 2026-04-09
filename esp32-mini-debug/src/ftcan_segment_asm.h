#pragma once

/**
 * FTCAN 2.0 segmented payload reassembly (DataFieldID 0x02 / 0x03).
 * Matches shared/protocol/ftcan/framing/segmentation.py behaviour.
 */

#include <cstdint>

/** Max reassembled payload bytes (spec max 1776; cap for embedded RAM). */
constexpr uint16_t FTCAN_SEG_MAX_PAYLOAD = 512;

/**
 * Feed one CAN data field (dlc bytes, max 8).
 * @param id29 29-bit extended ID (stream key)
 * @return true if a complete payload is ready in out_payload / out_len
 */
bool ftcan_segment_feed(uint32_t id29, const uint8_t* data, uint8_t dlc,
                        uint8_t* out_payload, uint16_t* out_len);

/** Reset all segment assemblers (e.g. on bus-off recovery). */
void ftcan_segment_reset_all(void);
