#pragma once

#include <Arduino.h>
#include <stdint.h>

struct IdRateBucket {
    uint32_t id29;
    uint32_t period_count;
};

static constexpr size_t HEALTH_ID_TRACK_CAP = 48;
static constexpr size_t HEALTH_ID_TOP_N     = 16;

struct NodeHealth {
    uint32_t uptime_ms;
    char     twai_state[16];
    uint32_t rx_count;
    uint32_t tx_err_count;
    uint32_t rx_err_count;
    uint32_t bus_off_count;
    uint32_t rx_queue_full_count;
    uint32_t arb_lost_count;
    uint32_t bus_error_count;
    uint32_t last_frame_ms;

    uint32_t unknown_id_count;
    uint32_t segmentation_error_count;
    uint32_t segmentation_complete_count;
    uint32_t decoded_sample_count;

    IdRateBucket id_buckets[HEALTH_ID_TRACK_CAP];
    size_t       id_bucket_count;
};

extern NodeHealth g_health;

void health_init();
void health_on_rx();
void health_on_frame_id(uint32_t id29);
void health_process_alerts(uint32_t alerts);
void update_health();

inline void health_bump_unknown_id() {
    g_health.unknown_id_count++;
}
inline void health_bump_segmentation_error() {
    g_health.segmentation_error_count++;
}
inline void health_bump_segmentation_complete() {
    g_health.segmentation_complete_count++;
}
inline void health_bump_decoded_sample() {
    g_health.decoded_sample_count++;
}

void emit_health_json(Stream& out);
