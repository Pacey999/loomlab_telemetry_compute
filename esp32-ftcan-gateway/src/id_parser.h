#pragma once
/**
 * FTCAN 2.0 — 29-bit CAN identifier decomposition (C++ / ESP32).
 *
 * Bit layout:
 *   bits 28..14  ProductID   (15 bits)
 *   bits 13..11  DataFieldID ( 3 bits)
 *   bits 10.. 0  MessageID   (11 bits)
 */

#include <cstdint>

struct FtcanId {
    uint32_t raw;
    uint16_t product_id;
    uint16_t product_type_id;
    uint8_t  unique_id;
    uint8_t  data_field_id;
    uint16_t message_id;

    inline bool is_ft600() const {
        return product_id >= 0x5020 && product_id <= 0x503F;
    }

    inline bool is_realtime_tuple() const {
        return message_id == 0x0FF || message_id == 0x1FF ||
               message_id == 0x2FF || message_id == 0x3FF;
    }

    inline bool is_simplified() const {
        return message_id >= 0x600 && message_id <= 0x608;
    }

    inline bool is_segmented() const {
        return data_field_id == 0x02 || data_field_id == 0x03;
    }

    inline bool is_standard() const {
        return data_field_id == 0x00 || data_field_id == 0x01;
    }
};

inline FtcanId parse_can_id(uint32_t id29) {
    FtcanId r;
    r.raw            = id29;
    r.product_id     = (id29 >> 14) & 0x7FFF;
    r.data_field_id  = (id29 >> 11) & 0x07;
    r.message_id     = id29 & 0x7FF;
    r.product_type_id = (r.product_id >> 5) & 0x3FF;
    r.unique_id      = r.product_id & 0x1F;
    return r;
}

inline uint32_t build_can_id(uint16_t product_id, uint8_t data_field_id, uint16_t message_id) {
    return ((uint32_t)(product_id & 0x7FFF) << 14) |
           ((uint32_t)(data_field_id & 0x07) << 11) |
           (uint32_t)(message_id & 0x7FF);
}
