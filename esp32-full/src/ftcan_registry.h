#pragma once
// AUTO-GENERATED from measure-registry.json — do not edit by hand.
// Regenerate with: python -m shared.protocol.ftcan.generators.gen_cpp

#include <cstdint>

struct MeasureEntry {
    uint16_t measure_id;
    const char* channel;
    const char* unit;
    float scale;
    bool is_signed;
};

static constexpr MeasureEntry FTCAN_MEASURES[] = {
    {0x0002, "engine.tps_pct", "%", 0.1f, true},
    {0x0004, "engine.map_bar", "bar", 0.001f, true},
    {0x0006, "engine.air_temp_c", "°C", 0.1f, true},
    {0x0008, "engine.coolant_temp_c", "°C", 0.1f, true},
    {0x000A, "engine.oil_pressure_bar", "bar", 0.001f, true},
    {0x000C, "engine.fuel_pressure_bar", "bar", 0.001f, true},
    {0x000E, "engine.water_pressure_bar", "bar", 0.001f, true},
    {0x0010, "engine.launch_mode", "-", 1f, true},
    {0x0012, "electrical.battery_v", "V", 0.01f, true},
    {0x0014, "vehicle.traction_speed_kmh", "km/h", 1f, true},
    {0x0016, "vehicle.drag_speed_kmh", "km/h", 1f, true},
    {0x0018, "vehicle.wheel_speed_fl_kmh", "km/h", 1f, true},
    {0x001A, "vehicle.wheel_speed_fr_kmh", "km/h", 1f, true},
    {0x001C, "vehicle.wheel_speed_rl_kmh", "km/h", 1f, true},
    {0x001E, "vehicle.wheel_speed_rr_kmh", "km/h", 1f, true},
    {0x0020, "driveline.driveshaft_rpm", "rpm", 1f, true},
    {0x0022, "driveline.gear", "-", 1f, true},
    {0x004E, "lambda.exhaust_o2", "λ", 0.001f, true},
    {0x007A, "engine.egt_exhaust_c", "°C", 0.1f, true},
    {0x0084, "engine.rpm", "rpm", 1f, true},
    {0x0086, "engine.inj_time_a_ms", "ms", 0.01f, true},
    {0x0088, "engine.inj_time_b_ms", "ms", 0.01f, true},
    {0x008A, "engine.inj_duty_a_pct", "%", 0.1f, true},
    {0x008C, "engine.inj_duty_b_pct", "%", 0.1f, true},
    {0x008E, "engine.ignition_advance_deg", "°", 0.1f, true},
    {0x0090, "engine.two_step_signal", "-", 1f, true},
    {0x0096, "engine.cut_pct", "%", 1f, true},
    {0x00A2, "lambda.average_o2", "λ", 0.001f, true},
    {0x0116, "engine.trans_temp_c", "°C", 0.1f, true},
    {0x011A, "engine.oil_temp_c", "°C", 0.1f, true},
    {0x011C, "engine.pit_limit_switch", "-", 1f, true},
    {0x02E0, "vehicle.ride_height", "-", 1f, true},
    {0x02E2, "vehicle.shock_fr", "-", 0.001f, true},
    {0x02E4, "vehicle.shock_fl", "-", 0.001f, true},
    {0x02E6, "vehicle.shock_rr", "-", 0.001f, true},
    {0x02E8, "vehicle.shock_rl", "-", 0.001f, true},
    {0x0296, "engine.brake_pressure_bar", "bar", 0.001f, true},
    {0x0290, "engine.fuel_flow_total_lpm", "L/min", 0.01f, true},
    {0x0282, "engine.fuel_consumption_l", "L", 1f, true},
    {0x0024, "lambda.disabled_o2", "λ", 0.001f, true},
    {0x0026, "lambda.cyl1_o2", "λ", 0.001f, true},
    {0x004A, "lambda.left_bank_o2", "λ", 0.001f, true},
    {0x004C, "lambda.right_bank_o2", "λ", 0.001f, true},
    {0x00A0, "driveline.gear_sensor_v", "V", 0.001f, true},
};

static constexpr uint16_t FTCAN_MEASURES_COUNT = 44;

// Simplified packet slot: maps (message_id, slot_position) -> measure_id
struct SimplifiedSlot {
    uint16_t message_id;
    uint8_t  position;
    uint16_t measure_id;
    const char* channel;
};

static constexpr SimplifiedSlot FTCAN_SIMPLIFIED_SLOTS[] = {
    {0x600, 0, 0x0002, "engine.tps_pct"},
    {0x600, 1, 0x0004, "engine.map_bar"},
    {0x600, 2, 0x0006, "engine.air_temp_c"},
    {0x600, 3, 0x0008, "engine.coolant_temp_c"},
    {0x601, 0, 0x000A, "engine.oil_pressure_bar"},
    {0x601, 1, 0x000C, "engine.fuel_pressure_bar"},
    {0x601, 2, 0x000E, "engine.water_pressure_bar"},
    {0x601, 3, 0x0022, "driveline.gear"},
    {0x602, 0, 0x004E, "lambda.exhaust_o2"},
    {0x602, 1, 0x0084, "engine.rpm"},
    {0x602, 2, 0x011A, "engine.oil_temp_c"},
    {0x602, 3, 0x011C, "engine.pit_limit_switch"},
    {0x603, 0, 0x001A, "vehicle.wheel_speed_fr_kmh"},
    {0x603, 1, 0x0018, "vehicle.wheel_speed_fl_kmh"},
    {0x603, 2, 0x001E, "vehicle.wheel_speed_rr_kmh"},
    {0x603, 3, 0x001C, "vehicle.wheel_speed_rl_kmh"},
    {0x604, 0, 0x0000, "vehicle.traction_slip"},
    {0x604, 1, 0x0000, "vehicle.traction_retard"},
    {0x604, 2, 0x0000, "vehicle.traction_cut"},
    {0x604, 3, 0x0000, "vehicle.heading"},
    {0x605, 0, 0x02E2, "vehicle.shock_fr"},
    {0x605, 1, 0x02E4, "vehicle.shock_fl"},
    {0x605, 2, 0x02E6, "vehicle.shock_rr"},
    {0x605, 3, 0x02E8, "vehicle.shock_rl"},
    {0x606, 0, 0x0000, "vehicle.gforce_accel"},
    {0x606, 1, 0x0000, "vehicle.gforce_lateral"},
    {0x606, 2, 0x0000, "vehicle.yaw_frontal"},
    {0x606, 3, 0x0000, "vehicle.yaw_lateral"},
    {0x607, 0, 0x0000, "lambda.correction"},
    {0x607, 1, 0x0086, "engine.inj_time_a_ms"},
    {0x607, 2, 0x0088, "engine.inj_time_b_ms"},
    {0x607, 3, 0x0290, "engine.fuel_flow_total_lpm"},
    {0x608, 0, 0x0116, "engine.trans_temp_c"},
    {0x608, 1, 0x0282, "engine.fuel_consumption_l"},
    {0x608, 2, 0x0296, "engine.brake_pressure_bar"},
    {0x608, 3, 0x011A, "engine.oil_temp_c"},
};

static constexpr uint16_t FTCAN_SIMPLIFIED_SLOTS_COUNT = 36;

// Lookup helpers
inline const MeasureEntry* ftcan_find_measure(uint16_t measure_id) {
    for (uint16_t i = 0; i < FTCAN_MEASURES_COUNT; i++) {
        if (FTCAN_MEASURES[i].measure_id == measure_id) return &FTCAN_MEASURES[i];
    }
    return nullptr;
}
