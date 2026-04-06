#include "health.h"

#include <cstring>

#include <driver/twai.h>

NodeHealth g_health;

namespace {

void id_track_note(uint32_t id29) {
    id29 &= 0x1FFFFFFFu;
    for (size_t i = 0; i < g_health.id_bucket_count; i++) {
        if (g_health.id_buckets[i].id29 == id29) {
            g_health.id_buckets[i].period_count++;
            return;
        }
    }
    if (g_health.id_bucket_count < HEALTH_ID_TRACK_CAP) {
        g_health.id_buckets[g_health.id_bucket_count++] = {id29, 1};
        return;
    }
    size_t min_i = 0;
    uint32_t min_c = g_health.id_buckets[0].period_count;
    for (size_t i = 1; i < HEALTH_ID_TRACK_CAP; i++) {
        if (g_health.id_buckets[i].period_count < min_c) {
            min_c = g_health.id_buckets[i].period_count;
            min_i = i;
        }
    }
    g_health.id_buckets[min_i] = {id29, 1};
}

void id_rates_reset_period() {
    for (size_t i = 0; i < g_health.id_bucket_count; i++) {
        g_health.id_buckets[i].period_count = 0;
    }
}

}  // namespace

void health_init() {
    memset(&g_health, 0, sizeof(g_health));
    strncpy(g_health.twai_state, "init", sizeof(g_health.twai_state) - 1);
    g_health.id_bucket_count = 0;
}

void health_on_rx() {
    g_health.rx_count++;
    g_health.last_frame_ms = millis();
}

void health_on_frame_id(uint32_t id29) {
    id_track_note(id29);
}

void health_process_alerts(uint32_t alerts) {
    if (alerts & TWAI_ALERT_BUS_OFF) {
        g_health.bus_off_count++;
    }
    if (alerts & TWAI_ALERT_RX_QUEUE_FULL) {
        g_health.rx_queue_full_count++;
    }
}

void update_health() {
    g_health.uptime_ms = millis();

    twai_status_info_t st{};
    if (twai_get_status_info(&st) == ESP_OK) {
        g_health.tx_err_count    = st.tx_error_counter;
        g_health.rx_err_count    = st.rx_error_counter;
        g_health.arb_lost_count  = st.arb_lost_count;
        g_health.bus_error_count = st.bus_error_count;

        const char* s = "unknown";
        switch (st.state) {
            case TWAI_STATE_STOPPED:
                s = "stopped";
                break;
            case TWAI_STATE_RUNNING:
                s = "running";
                break;
            case TWAI_STATE_BUS_OFF:
                s = "bus_off";
                break;
            case TWAI_STATE_RECOVERING:
                s = "recovering";
                break;
            default:
                break;
        }
        strncpy(g_health.twai_state, s, sizeof(g_health.twai_state) - 1);
        g_health.twai_state[sizeof(g_health.twai_state) - 1] = '\0';
    }
}

void emit_health_json(Stream& out) {
    uint8_t order[HEALTH_ID_TRACK_CAP];
    size_t  n = 0;
    for (size_t i = 0; i < g_health.id_bucket_count; i++) {
        if (g_health.id_buckets[i].period_count > 0) {
            order[n++] = static_cast<uint8_t>(i);
        }
    }
    for (size_t a = 0; a + 1 < n; a++) {
        for (size_t b = 0; b + 1 < n - a; b++) {
            if (g_health.id_buckets[order[b]].period_count < g_health.id_buckets[order[b + 1]].period_count) {
                uint8_t t    = order[b];
                order[b]     = order[b + 1];
                order[b + 1] = t;
            }
        }
    }
    size_t top = n;
    if (top > HEALTH_ID_TOP_N) {
        top = HEALTH_ID_TOP_N;
    }

    char line[512];
    snprintf(
        line,
        sizeof(line),
        "{\"type\":\"health\",\"uptime_ms\":%lu,\"twai_state\":\"%s\","
        "\"rx_count\":%lu,\"tx_err_count\":%lu,\"rx_err_count\":%lu,"
        "\"bus_off_count\":%lu,\"rx_queue_full_count\":%lu,"
        "\"arb_lost_count\":%lu,\"bus_error_count\":%lu,\"last_frame_ms\":%lu,"
        "\"unknown_id_count\":%lu,\"segmentation_error_count\":%lu,"
        "\"segmentation_complete_count\":%lu,\"decoded_sample_count\":%lu,"
        "\"id_rates\":[",
        static_cast<unsigned long>(g_health.uptime_ms),
        g_health.twai_state,
        static_cast<unsigned long>(g_health.rx_count),
        static_cast<unsigned long>(g_health.tx_err_count),
        static_cast<unsigned long>(g_health.rx_err_count),
        static_cast<unsigned long>(g_health.bus_off_count),
        static_cast<unsigned long>(g_health.rx_queue_full_count),
        static_cast<unsigned long>(g_health.arb_lost_count),
        static_cast<unsigned long>(g_health.bus_error_count),
        static_cast<unsigned long>(g_health.last_frame_ms),
        static_cast<unsigned long>(g_health.unknown_id_count),
        static_cast<unsigned long>(g_health.segmentation_error_count),
        static_cast<unsigned long>(g_health.segmentation_complete_count),
        static_cast<unsigned long>(g_health.decoded_sample_count));
    out.print(line);

    for (size_t k = 0; k < top; k++) {
        const IdRateBucket& b = g_health.id_buckets[order[k]];
        snprintf(line,
                 sizeof(line),
                 "%s{\"id29\":\"0x%08lX\",\"hz\":%lu}",
                 (k == 0) ? "" : ",",
                 static_cast<unsigned long>(b.id29),
                 static_cast<unsigned long>(b.period_count));
        out.print(line);
    }

    out.println("]}");

    id_rates_reset_period();
}
