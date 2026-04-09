#include "ftcan_segment_asm.h"

#include <cstring>

namespace {

constexpr uint32_t k_len_mask = 0x07FFu;

struct Slot {
    uint32_t id29          = 0;
    bool     active        = false;
    uint8_t  expected_seg  = 0;
    uint16_t total_length  = 0;
    uint16_t buf_len       = 0;
    uint8_t  buffer[FTCAN_SEG_MAX_PAYLOAD];
};

constexpr int k_slots = 6;
Slot g_slot[k_slots];

void slot_clear(int i) {
    g_slot[i].active       = false;
    g_slot[i].buf_len      = 0;
    g_slot[i].total_length = 0;
    g_slot[i].expected_seg = 0;
}

int slot_find_active(uint32_t id29) {
    for (int i = 0; i < k_slots; ++i) {
        if (g_slot[i].active && g_slot[i].id29 == id29) {
            return i;
        }
    }
    return -1;
}

/** Allocate or reuse a slot for a new segment-0 stream. */
int slot_acquire(uint32_t id29) {
    int same = slot_find_active(id29);
    if (same >= 0) {
        return same;
    }
    for (int i = 0; i < k_slots; ++i) {
        if (!g_slot[i].active) {
            return i;
        }
    }
    /* All busy — overwrite slot 0 (rare on a quiet bench). */
    slot_clear(0);
    return 0;
}

bool emit_complete(int si, uint8_t* out_payload, uint16_t* out_len) {
    const uint16_t n = g_slot[si].total_length;
    if (g_slot[si].buf_len < n) {
        return false;
    }
    std::memcpy(out_payload, g_slot[si].buffer, n);
    *out_len = n;
    slot_clear(si);
    return true;
}

}  // namespace

void ftcan_segment_reset_all(void) {
    for (int i = 0; i < k_slots; ++i) {
        slot_clear(i);
    }
}

bool ftcan_segment_feed(uint32_t id29, const uint8_t* data, uint8_t dlc,
                        uint8_t* out_payload, uint16_t* out_len) {
    if (!data || !out_payload || !out_len || dlc < 1) {
        return false;
    }
    *out_len = 0;

    const uint8_t seg = data[0];
    /* Single-packet marker — handled by caller, not the reassembler. */
    if (seg == 0xFFu) {
        return false;
    }

    if (seg == 0x00u) {
        if (dlc < 3u) {
            return false;
        }
        const uint16_t meta = (static_cast<uint16_t>(data[1]) << 8) | data[2];
        const uint16_t total = static_cast<uint16_t>(meta & k_len_mask);
        if (total == 0u || total > FTCAN_SEG_MAX_PAYLOAD) {
            return false;
        }

        const int si = slot_acquire(id29);
        g_slot[si].id29          = id29;
        g_slot[si].active        = true;
        g_slot[si].total_length  = total;
        g_slot[si].expected_seg  = 1;
        g_slot[si].buf_len       = 0;

        for (uint8_t i = 3; i < dlc; ++i) {
            if (g_slot[si].buf_len >= FTCAN_SEG_MAX_PAYLOAD) {
                break;
            }
            g_slot[si].buffer[g_slot[si].buf_len++] = data[i];
        }

        if (emit_complete(si, out_payload, out_len)) {
            return true;
        }
        return false;
    }

    const int si = slot_find_active(id29);
    if (si < 0 || !g_slot[si].active || seg != g_slot[si].expected_seg) {
        if (si >= 0) {
            slot_clear(si);
        }
        return false;
    }

    /* Continuation: up to 7 payload bytes in bytes [1..7]. */
    const uint8_t ncopy = static_cast<uint8_t>(dlc > 0 ? (dlc - 1u) : 0u);
    for (uint8_t i = 0; i < ncopy && i < 7u; ++i) {
        if (g_slot[si].buf_len >= FTCAN_SEG_MAX_PAYLOAD) {
            break;
        }
        g_slot[si].buffer[g_slot[si].buf_len++] = data[1u + i];
    }
    g_slot[si].expected_seg = static_cast<uint8_t>(seg + 1u);

    if (emit_complete(si, out_payload, out_len)) {
        return true;
    }
    return false;
}
