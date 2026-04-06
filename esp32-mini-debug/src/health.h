#pragma once

#include <Arduino.h>
#include <stdint.h>

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
};

extern NodeHealth g_health;

void health_init();
/** Call for each received frame (hot path: only increments + timestamp). */
void health_on_rx();
/** Accumulate edge-detected alert conditions (call after twai_read_alerts). */
void health_process_alerts(uint32_t alerts);
/** Refresh fields from TWAI status + millis. */
void update_health();
void emit_health_json(Stream& out);
