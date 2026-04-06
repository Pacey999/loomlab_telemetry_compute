#include "mini_decode.h"

#include <Arduino.h>
#include <cstdio>

#include "id_parser.h"

static void emit_decoded(const char* channel, double value, const char* unit) {
    char line[160];
    snprintf(
        line,
        sizeof(line),
        "{\"type\":\"decoded\",\"channel\":\"%s\",\"value\":%.5g,\"unit\":\"%s\"}",
        channel,
        value,
        unit);
    Serial.println(line);
}

void try_mini_decode(const twai_message_t& msg) {
    if ((msg.flags & TWAI_MSG_FLAG_EXTD) == 0) {
        return;
    }
    if (msg.data_length_code < 4) {
        return;
    }

    const FtcanId id = parse_can_id(msg.identifier & 0x1FFFFFFFu);
    if (!id.is_realtime_tuple()) {
        return;
    }
    if (id.data_field_id != 0x00) {
        return;
    }

    const uint16_t measure_id =
        static_cast<uint16_t>((static_cast<uint16_t>(msg.data[0]) << 8) | msg.data[1]);
    const int16_t raw =
        static_cast<int16_t>((static_cast<uint16_t>(msg.data[2]) << 8) | msg.data[3]);

    switch (measure_id) {
        case 0x0002:
            emit_decoded("engine.tps_pct", static_cast<double>(raw) * 0.1, "%");
            break;
        case 0x0004:
            emit_decoded("engine.map_bar", static_cast<double>(raw) * 0.001, "bar");
            break;
        case 0x0012:
            emit_decoded("electrical.battery_v", static_cast<double>(raw) * 0.01, "V");
            break;
        default:
            break;
    }
}
