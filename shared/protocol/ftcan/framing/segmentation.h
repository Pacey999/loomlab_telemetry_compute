#pragma once
/**
 * FTCAN 2.0 segmented packet reassembly (C++ / ESP32).
 *
 * Single packet: first byte = 0xFF, payload in bytes 1..7.
 * Segmented: first byte = segment index (0x00..0xFE).
 *   Segment 0 carries 2-byte length metadata + 5 payload bytes.
 *   Continuation segments carry 7 payload bytes each.
 * Max payload: 1776 bytes.
 */

#include <cstdint>
#include <cstring>

static constexpr uint8_t  FTCAN_SINGLE_MARKER    = 0xFF;
static constexpr uint16_t FTCAN_MAX_PAYLOAD      = 1776;
static constexpr uint16_t FTCAN_LENGTH_MASK      = 0x07FF;

enum class SegmentResult : uint8_t {
    Accumulating,
    Complete,
    Discarded,
    SinglePacket
};

template <uint16_t BUF_SIZE = FTCAN_MAX_PAYLOAD>
class SegmentAssembler {
public:
    uint8_t  buffer[BUF_SIZE];
    uint16_t payload_length = 0;
    uint16_t buffered       = 0;
    uint32_t completed      = 0;
    uint32_t discarded      = 0;

    SegmentResult feed(const uint8_t* data, uint8_t dlc) {
        if (dlc < 1) return SegmentResult::Discarded;

        uint8_t seg = data[0];

        if (seg == FTCAN_SINGLE_MARKER) {
            reset();
            uint8_t n = (dlc > 1) ? (dlc - 1) : 0;
            memcpy(buffer, data + 1, n);
            payload_length = n;
            buffered = n;
            completed++;
            return SegmentResult::SinglePacket;
        }

        if (seg == 0x00) {
            if (dlc < 3) { discard(); return SegmentResult::Discarded; }
            uint16_t total = ((uint16_t)data[1] << 8) | data[2];
            total &= FTCAN_LENGTH_MASK;
            if (total == 0 || total > BUF_SIZE) { discard(); return SegmentResult::Discarded; }
            payload_length = total;
            uint8_t n = (dlc > 3) ? (dlc - 3) : 0;
            memcpy(buffer, data + 3, n);
            buffered = n;
            _expected = 1;
            _active = true;
            return check_complete();
        }

        if (!_active || seg != _expected) {
            discard();
            return SegmentResult::Discarded;
        }

        uint8_t n = (dlc > 1) ? (dlc - 1) : 0;
        if (buffered + n > BUF_SIZE) { discard(); return SegmentResult::Discarded; }
        memcpy(buffer + buffered, data + 1, n);
        buffered += n;
        _expected = seg + 1;
        return check_complete();
    }

    void reset() {
        payload_length = 0;
        buffered = 0;
        _expected = 0;
        _active = false;
    }

private:
    uint8_t  _expected = 0;
    bool     _active   = false;

    SegmentResult check_complete() {
        if (buffered >= payload_length) {
            completed++;
            _active = false;
            return SegmentResult::Complete;
        }
        return SegmentResult::Accumulating;
    }

    void discard() {
        discarded++;
        reset();
    }
};
