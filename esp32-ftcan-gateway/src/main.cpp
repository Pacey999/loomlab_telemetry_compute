#include <Arduino.h>

#include <driver/twai.h>

#include "can_config.h"
#include "frame_output.h"
#include "gateway_header.h"
#include "health.h"

namespace {

uint32_t g_seq            = 0;
uint32_t g_last_health_ms = 0;
uint32_t g_last_warn_ms   = 0;

void emit_rx_watchdog_warn() {
    Serial.println("{\"type\":\"warn\",\"msg\":\"no CAN frames for 30s\"}");
}

bool rx_stale(uint32_t now_ms) {
    if (g_health.rx_count == 0) {
        return now_ms >= 30000u;
    }
    if (g_health.last_frame_ms == 0) {
        return false;
    }
    return (now_ms - g_health.last_frame_ms) >= 30000u;
}

}  // namespace

void setup() {
    Serial.begin(921600);
    delay(200);

    health_init();

    constexpr twai_mode_t k_twai_mode = TWAI_MODE_LISTEN_ONLY;

    twai_general_config_t g_config =
        TWAI_GENERAL_CONFIG_DEFAULT(static_cast<gpio_num_t>(CAN_TX_GPIO),
                                    static_cast<gpio_num_t>(CAN_RX_GPIO),
                                    k_twai_mode);
    g_config.rx_queue_len = CAN_RX_QUEUE_LEN;

    twai_timing_config_t t_config = CAN_TIMING_1MBPS();
    twai_filter_config_t f_config = can_filter_ext_accept_all();

    esp_err_t err = twai_driver_install(&g_config, &t_config, &f_config);
    if (err != ESP_OK) {
        Serial.printf("{\"type\":\"error\",\"msg\":\"twai_driver_install failed\",\"code\":%i}\n", static_cast<int>(err));
        while (true) {
            delay(1000);
        }
    }

    err = twai_reconfigure_alerts(CAN_ALERT_MASK, nullptr);
    if (err != ESP_OK) {
        Serial.printf("{\"type\":\"error\",\"msg\":\"twai_reconfigure_alerts failed\",\"code\":%i}\n",
                      static_cast<int>(err));
    }

    err = twai_start();
    if (err != ESP_OK) {
        Serial.printf("{\"type\":\"error\",\"msg\":\"twai_start failed\",\"code\":%i}\n", static_cast<int>(err));
        while (true) {
            delay(1000);
        }
    }

    Serial.printf(
        "{\"type\":\"startup\",\"firmware\":\"esp32-ftcan-gateway\",\"version\":\"0.1.0\","
        "\"twai_mode\":\"LISTEN_ONLY\",\"role\":\"ftcan2_gateway\"}\n");
    g_last_health_ms = millis();
}

void loop() {
    uint32_t alerts = 0;
    if (twai_read_alerts(&alerts, 0) == ESP_OK && alerts != 0) {
        health_process_alerts(alerts);
    }

    twai_message_t msg{};
    while (twai_receive(&msg, 0) == ESP_OK) {
        const uint32_t ts = millis();
        g_seq++;
        health_on_rx();
        if ((msg.flags & TWAI_MSG_FLAG_EXTD) != 0) {
            emit_ftcan_header_json(Serial, msg, g_seq);
        }
        emit_raw_frame(Serial, msg, ts, g_seq);
    }

    const uint32_t now = millis();
    if (static_cast<int32_t>(now - g_last_health_ms) >= 1000) {
        g_last_health_ms = now;
        update_health();
        emit_health_json(Serial);

        if (rx_stale(now)) {
            if (g_last_warn_ms == 0 || (now - g_last_warn_ms) >= 5000u) {
                g_last_warn_ms = now;
                emit_rx_watchdog_warn();
            }
        } else {
            g_last_warn_ms = 0;
        }
    }

    delay(1);
}
