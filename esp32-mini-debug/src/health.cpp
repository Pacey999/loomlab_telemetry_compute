#include "health.h"

#include <cstring>

#include <driver/twai.h>

NodeHealth g_health;

void health_init() {
    memset(&g_health, 0, sizeof(g_health));
    strncpy(g_health.twai_state, "init", sizeof(g_health.twai_state) - 1);
}

void health_on_rx() {
    g_health.rx_count++;
    g_health.last_frame_ms = millis();
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
        g_health.tx_err_count     = st.tx_error_counter;
        g_health.rx_err_count     = st.rx_error_counter;
        g_health.arb_lost_count   = st.arb_lost_count;
        g_health.bus_error_count  = st.bus_error_count;

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
    char line[384];
    snprintf(
        line,
        sizeof(line),
        "{\"type\":\"health\",\"uptime_ms\":%lu,\"twai_state\":\"%s\","
        "\"rx_count\":%lu,\"tx_err_count\":%lu,\"rx_err_count\":%lu,"
        "\"bus_off_count\":%lu,\"rx_queue_full_count\":%lu,"
        "\"arb_lost_count\":%lu,\"bus_error_count\":%lu,\"last_frame_ms\":%lu}",
        static_cast<unsigned long>(g_health.uptime_ms),
        g_health.twai_state,
        static_cast<unsigned long>(g_health.rx_count),
        static_cast<unsigned long>(g_health.tx_err_count),
        static_cast<unsigned long>(g_health.rx_err_count),
        static_cast<unsigned long>(g_health.bus_off_count),
        static_cast<unsigned long>(g_health.rx_queue_full_count),
        static_cast<unsigned long>(g_health.arb_lost_count),
        static_cast<unsigned long>(g_health.bus_error_count),
        static_cast<unsigned long>(g_health.last_frame_ms));
    out.println(line);
}
