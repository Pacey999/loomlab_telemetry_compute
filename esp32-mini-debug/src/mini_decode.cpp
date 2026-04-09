#include "mini_decode.h"

#include <Arduino.h>
#include <cstdio>

#include "ftcan_segment_asm.h"
#include "id_parser.h"

static void emit_decoded(const char* channel, double value, const char* unit) {
    char line[160];
    snprintf(line, sizeof(line),
             "{\"type\":\"decoded\",\"channel\":\"%s\",\"value\":%.5g,\"unit\":\"%s\"}",
             channel, value, unit);
    Serial.println(line);
}

static inline int16_t i16be(const uint8_t* d, uint8_t off) {
    return static_cast<int16_t>((static_cast<uint16_t>(d[off]) << 8) | d[off + 1]);
}

static inline uint16_t u16be(const uint8_t* d, uint8_t off) {
    return (static_cast<uint16_t>(d[off]) << 8) | d[off + 1];
}

/*
 * MeasureID → channel (subset; expand from shared/protocol/ftcan/registry/measure-registry.json).
 * Values are signed int16 big-endian raw words unless noted.
 */
static void decode_measure(uint16_t measure_id, int16_t raw) {
    switch (measure_id) {
        case 0x0002:
            emit_decoded("engine.tps_pct", static_cast<double>(raw) * 0.1, "%");
            break;
        case 0x0004:
            emit_decoded("engine.map_bar", static_cast<double>(raw) * 0.001, "bar");
            break;
        case 0x0006:
            emit_decoded("engine.air_temp_c", static_cast<double>(raw) * 0.1, "C");
            break;
        case 0x0008:
            emit_decoded("engine.coolant_temp_c", static_cast<double>(raw) * 0.1, "C");
            break;
        case 0x000A:
            emit_decoded("engine.oil_pressure_bar", static_cast<double>(raw) * 0.001, "bar");
            break;
        case 0x000C:
            emit_decoded("engine.fuel_pressure_bar", static_cast<double>(raw) * 0.001, "bar");
            break;
        case 0x000E:
            emit_decoded("engine.water_pressure_bar", static_cast<double>(raw) * 0.001, "bar");
            break;
        case 0x0012:
            emit_decoded("electrical.battery_v", static_cast<double>(raw) * 0.01, "V");
            break;
        case 0x004E:
            emit_decoded("lambda.exhaust_o2", static_cast<double>(raw) * 0.001, "lambda");
            break;
        case 0x0084:
            emit_decoded("engine.rpm", static_cast<double>(raw), "RPM");
            break;
        case 0x0086:
            emit_decoded("engine.inj_time_a_ms", static_cast<double>(raw) * 0.01, "ms");
            break;
        case 0x0088:
            emit_decoded("engine.inj_time_b_ms", static_cast<double>(raw) * 0.01, "ms");
            break;
        default:
            break;
    }
}

static void decode_tuple_payload(const uint8_t* payload, uint16_t len) {
    for (uint16_t off = 0; off + 4 <= len; off += 4) {
        decode_measure(u16be(payload, off), i16be(payload, off + 2));
    }
}

static void decode_realtime_tuple(uint32_t id29, const FtcanId& id, const twai_message_t& msg) {
    const uint8_t dlc = msg.data_length_code > 8 ? 8 : msg.data_length_code;

    if (id.data_field_id == 0x00 || id.data_field_id == 0x01) {
        if (dlc >= 4) {
            decode_tuple_payload(msg.data, dlc);
        }
        return;
    }

    if (id.data_field_id != 0x02 && id.data_field_id != 0x03) {
        return;
    }
    if (dlc < 1) {
        return;
    }

    const uint8_t seg = msg.data[0];
    if (seg == 0xFF) {
        if (dlc >= 5) {
            decode_tuple_payload(msg.data + 1, dlc - 1);
        }
        return;
    }

    static uint8_t s_asm_buf[FTCAN_SEG_MAX_PAYLOAD];
    uint16_t       assembled_len = 0;
    if (ftcan_segment_feed(id29, msg.data, dlc, s_asm_buf, &assembled_len)) {
        decode_tuple_payload(s_asm_buf, assembled_len);
    }
}

/*
 * Simplified 0x600–0x608 — fixed 4× int16 BE; layout matches measure-registry.json
 * under "simplifiedPackets" for FT600.
 */
static void decode_simplified(const FtcanId& id, const twai_message_t& msg) {
    const uint8_t dlc = msg.data_length_code > 8 ? 8 : msg.data_length_code;
    if (dlc < 8) {
        return;
    }
    const uint8_t* d = msg.data;

    switch (id.message_id) {
        case 0x600:
            emit_decoded("engine.tps_pct", static_cast<double>(i16be(d, 0)) * 0.1, "%");
            emit_decoded("engine.map_bar", static_cast<double>(i16be(d, 2)) * 0.001, "bar");
            emit_decoded("engine.air_temp_c", static_cast<double>(i16be(d, 4)) * 0.1, "C");
            emit_decoded("engine.coolant_temp_c", static_cast<double>(i16be(d, 6)) * 0.1, "C");
            break;
        case 0x601:
            emit_decoded("engine.oil_pressure_bar", static_cast<double>(i16be(d, 0)) * 0.001, "bar");
            emit_decoded("engine.fuel_pressure_bar", static_cast<double>(i16be(d, 2)) * 0.001, "bar");
            emit_decoded("engine.water_pressure_bar", static_cast<double>(i16be(d, 4)) * 0.001, "bar");
            emit_decoded("driveline.gear", static_cast<double>(i16be(d, 6)), "");
            break;
        case 0x602:
            emit_decoded("lambda.exhaust_o2", static_cast<double>(i16be(d, 0)) * 0.001, "lambda");
            emit_decoded("engine.rpm", static_cast<double>(i16be(d, 2)), "RPM");
            emit_decoded("engine.oil_temp_c", static_cast<double>(i16be(d, 4)) * 0.1, "C");
            emit_decoded("engine.pit_limit_switch", static_cast<double>(i16be(d, 6)), "");
            break;
        case 0x603:
            emit_decoded("vehicle.wheel_speed_fr_kmh", static_cast<double>(i16be(d, 0)), "km/h");
            emit_decoded("vehicle.wheel_speed_fl_kmh", static_cast<double>(i16be(d, 2)), "km/h");
            emit_decoded("vehicle.wheel_speed_rr_kmh", static_cast<double>(i16be(d, 4)), "km/h");
            emit_decoded("vehicle.wheel_speed_rl_kmh", static_cast<double>(i16be(d, 6)), "km/h");
            break;
        case 0x604:
            emit_decoded("vehicle.traction_slip", static_cast<double>(i16be(d, 0)), "");
            emit_decoded("vehicle.traction_retard", static_cast<double>(i16be(d, 2)), "");
            emit_decoded("vehicle.traction_cut", static_cast<double>(i16be(d, 4)), "");
            emit_decoded("vehicle.heading", static_cast<double>(i16be(d, 6)), "");
            break;
        case 0x605:
            emit_decoded("vehicle.shock_fr", static_cast<double>(i16be(d, 0)) * 0.001, "");
            emit_decoded("vehicle.shock_fl", static_cast<double>(i16be(d, 2)) * 0.001, "");
            emit_decoded("vehicle.shock_rr", static_cast<double>(i16be(d, 4)) * 0.001, "");
            emit_decoded("vehicle.shock_rl", static_cast<double>(i16be(d, 6)) * 0.001, "");
            break;
        case 0x606:
            emit_decoded("vehicle.gforce_accel", static_cast<double>(i16be(d, 0)), "");
            emit_decoded("vehicle.gforce_lateral", static_cast<double>(i16be(d, 2)), "");
            emit_decoded("vehicle.yaw_frontal", static_cast<double>(i16be(d, 4)), "");
            emit_decoded("vehicle.yaw_lateral", static_cast<double>(i16be(d, 6)), "");
            break;
        case 0x607:
            emit_decoded("lambda.correction", static_cast<double>(i16be(d, 0)) * 0.001, "");
            emit_decoded("engine.inj_time_a_ms", static_cast<double>(i16be(d, 2)) * 0.01, "ms");
            emit_decoded("engine.inj_time_b_ms", static_cast<double>(i16be(d, 4)) * 0.01, "ms");
            emit_decoded("engine.fuel_flow_total_lpm", static_cast<double>(i16be(d, 6)) * 0.01, "L/min");
            break;
        case 0x608:
            emit_decoded("engine.trans_temp_c", static_cast<double>(i16be(d, 0)) * 0.1, "C");
            emit_decoded("engine.fuel_consumption_l", static_cast<double>(i16be(d, 2)), "L");
            emit_decoded("engine.brake_pressure_bar", static_cast<double>(i16be(d, 4)) * 0.001, "bar");
            emit_decoded("engine.oil_temp_c", static_cast<double>(i16be(d, 6)) * 0.1, "C");
            break;
        default:
            break;
    }
}

void try_mini_decode(const twai_message_t& msg) {
    if ((msg.flags & TWAI_MSG_FLAG_EXTD) == 0) {
        return;
    }

    const uint32_t id29 = msg.identifier & 0x1FFFFFFFu;
    const FtcanId    id = parse_can_id(id29);
    if (!id.is_ft600()) {
        return;
    }

    if (id.is_realtime_tuple()) {
        decode_realtime_tuple(id29, id, msg);
    } else if (id.is_simplified()) {
        decode_simplified(id, msg);
    }
}
