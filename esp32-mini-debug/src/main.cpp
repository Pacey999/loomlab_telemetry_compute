#include <Arduino.h>

#include <driver/twai.h>

#include "can_config.h"
#include "frame_output.h"
#include "health.h"
#include "mini_decode.h"

namespace {

uint32_t g_seq            = 0;
uint32_t g_last_health_ms = 0;
uint32_t g_last_warn_ms   = 0;

#ifdef RX_SERIAL_QUIET
uint32_t g_last_sample_ms = 0;
uint32_t g_last_can_id29  = 0;
uint8_t  g_last_data[8]   = {};
uint8_t  g_last_dlc       = 0;
#endif

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

    /* LISTEN_ONLY: safe alone on FT600 bench (no ACK). For 2-node ESP32 loopback test with
     * esp32-can-sim, build env bench-pair — NORMAL mode so this node ACKs simulator frames. */
#ifdef BENCH_TWO_NODE_ACK
    constexpr twai_mode_t k_twai_mode = TWAI_MODE_NORMAL;
#else
    constexpr twai_mode_t k_twai_mode = TWAI_MODE_LISTEN_ONLY;
#endif

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

#ifdef BENCH_TWO_NODE_ACK
    constexpr const char* k_twai_mode_json = "\"twai_mode\":\"NORMAL\"";
#else
    constexpr const char* k_twai_mode_json = "\"twai_mode\":\"LISTEN_ONLY\"";
#endif
#ifdef RX_SERIAL_QUIET
    Serial.printf("{\"type\":\"startup\",\"firmware\":\"esp32-mini-debug\",\"version\":\"1.0.2\","
                  "\"rx_serial_quiet\":true,\"bench\":\"ftcan_two_node\",%s}\n",
                  k_twai_mode_json);
#else
    Serial.printf("{\"type\":\"startup\",\"firmware\":\"esp32-mini-debug\",\"version\":\"1.0.2\",%s}\n",
                  k_twai_mode_json);
#endif
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
#ifdef RX_SERIAL_QUIET
        g_last_can_id29 = msg.identifier & 0x1FFFFFFFu;
        g_last_dlc        = msg.data_length_code > 8 ? 8 : msg.data_length_code;
        for (uint8_t i = 0; i < 8; i++) {
            g_last_data[i] = msg.data[i];
        }
        (void)ts;
#else
        emit_raw_frame(Serial, msg, ts, g_seq);
        try_mini_decode(msg);
#endif
    }

    const uint32_t now = millis();
    if (static_cast<int32_t>(now - g_last_health_ms) >= 1000) {
        g_last_health_ms = now;
        update_health();
        emit_health_json(Serial);

#ifdef RX_SERIAL_QUIET
        if (g_health.rx_count > 0 && (now - g_last_sample_ms) >= 2000u) {
            g_last_sample_ms = now;
            Serial.printf(
                "{\"type\":\"ftcan_sample\",\"id29\":\"0x%08lX\",\"dlc\":%u,\"data\":[%u,%u,%u,%u,%u,%u,%u,%u],"
                "\"note\":\"FTCAN 2.0 extended @ 1 Mbps; big-endian tuples\"}\n",
                static_cast<unsigned long>(g_last_can_id29),
                static_cast<unsigned>(g_last_dlc),
                static_cast<unsigned>(g_last_data[0]),
                static_cast<unsigned>(g_last_data[1]),
                static_cast<unsigned>(g_last_data[2]),
                static_cast<unsigned>(g_last_data[3]),
                static_cast<unsigned>(g_last_data[4]),
                static_cast<unsigned>(g_last_data[5]),
                static_cast<unsigned>(g_last_data[6]),
                static_cast<unsigned>(g_last_data[7]));
        }
#endif

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
