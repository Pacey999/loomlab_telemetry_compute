#include "decoder.h"

#include "frame_output.h"
#include "ftcan_registry.h"
#include "health.h"
#include "id_parser.h"
#include "segmentation.h"

namespace {

constexpr int kAsmPoolSize = 8;

struct AsmSlot {
    uint16_t            product_id = 0;
    uint16_t            message_id = 0;
    bool                in_use     = false;
    SegmentAssembler<>  asm_;
};

AsmSlot g_asm_slots[kAsmPoolSize];

SegmentAssembler<>* asm_find_or_alloc(uint16_t product_id, uint16_t message_id) {
    int empty_idx = -1;
    for (int i = 0; i < kAsmPoolSize; i++) {
        if (g_asm_slots[i].in_use && g_asm_slots[i].product_id == product_id &&
            g_asm_slots[i].message_id == message_id) {
            return &g_asm_slots[i].asm_;
        }
        if (!g_asm_slots[i].in_use && empty_idx < 0) {
            empty_idx = i;
        }
    }
    if (empty_idx >= 0) {
        g_asm_slots[empty_idx].in_use     = true;
        g_asm_slots[empty_idx].product_id = product_id;
        g_asm_slots[empty_idx].message_id = message_id;
        g_asm_slots[empty_idx].asm_.reset();
        return &g_asm_slots[empty_idx].asm_;
    }
    g_asm_slots[0].asm_.reset();
    g_asm_slots[0].in_use     = true;
    g_asm_slots[0].product_id = product_id;
    g_asm_slots[0].message_id = message_id;
    return &g_asm_slots[0].asm_;
}

void decode_tuple_payload(const uint8_t* data, uint16_t len, uint32_t seq, Stream& out) {
    for (uint16_t off = 0; off + 4 <= len; off += 4) {
        const uint16_t mid  = static_cast<uint16_t>((data[off] << 8) | data[off + 1]);
        const uint16_t uraw = static_cast<uint16_t>((data[off + 2] << 8) | data[off + 3]);
        const MeasureEntry* e = ftcan_find_measure(mid);
        if (!e) {
            health_bump_unknown_id();
            continue;
        }
        const float value =
            e->is_signed ? static_cast<float>(static_cast<int16_t>(uraw)) * e->scale
                         : static_cast<float>(uraw) * e->scale;
        const char* quality = (mid & 1u) ? "status" : "good";
        emit_decoded_sample(out, e->channel, value, e->unit, quality, mid, seq);
        health_bump_decoded_sample();
    }
}

void decode_simplified(const FtcanId& id, const uint8_t* data, uint8_t dlc, uint32_t seq, Stream& out) {
    for (uint16_t i = 0; i < FTCAN_SIMPLIFIED_SLOTS_COUNT; i++) {
        const SimplifiedSlot& sl = FTCAN_SIMPLIFIED_SLOTS[i];
        if (sl.message_id != id.message_id) {
            continue;
        }
        if (sl.measure_id == 0) {
            continue;
        }
        const unsigned off = static_cast<unsigned>(sl.position) * 2u;
        if (off + 2u > static_cast<unsigned>(dlc)) {
            continue;
        }
        const uint16_t uraw =
            static_cast<uint16_t>((data[off] << 8) | data[off + 1]);
        const MeasureEntry* e = ftcan_find_measure(sl.measure_id);
        if (!e) {
            health_bump_unknown_id();
            continue;
        }
        const float value =
            e->is_signed ? static_cast<float>(static_cast<int16_t>(uraw)) * e->scale
                         : static_cast<float>(uraw) * e->scale;
        const char* quality = (sl.measure_id & 1u) ? "status" : "good";
        emit_decoded_sample(out, e->channel, value, e->unit, quality, sl.measure_id, seq);
        health_bump_decoded_sample();
    }
}

}  // namespace

void decode_frame(const twai_message_t& msg, uint32_t seq, Stream& out) {
    const uint32_t id29 = msg.identifier & 0x1FFFFFFFu;
    const FtcanId  id   = parse_can_id(id29);
    const uint8_t  dlc  = msg.data_length_code > 8 ? 8 : msg.data_length_code;

#ifdef FILTER_SIMPLIFIED_ONLY
    if (!id.is_simplified() || id.data_field_id != 0) {
        return;
    }
    decode_simplified(id, msg.data, dlc, seq, out);
    return;
#endif

    if (id.is_segmented()) {
        SegmentAssembler<>* asmp = asm_find_or_alloc(id.product_id, id.message_id);
        const SegmentResult   sr = asmp->feed(msg.data, dlc);
        if (sr == SegmentResult::Discarded) {
            health_bump_segmentation_error();
            return;
        }
        if (sr == SegmentResult::Complete || sr == SegmentResult::SinglePacket) {
            health_bump_segmentation_complete();
            decode_tuple_payload(asmp->buffer, asmp->payload_length, seq, out);
        }
        return;
    }

    if (id.is_realtime_tuple() && (id.data_field_id == 0x00 || id.data_field_id == 0x01)) {
        decode_tuple_payload(msg.data, dlc, seq, out);
        return;
    }

    if (id.is_simplified() && id.data_field_id == 0x00) {
        decode_simplified(id, msg.data, dlc, seq, out);
    }
}
