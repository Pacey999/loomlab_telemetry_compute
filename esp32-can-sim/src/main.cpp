/**
 * esp32-can-sim — Extended-ID CAN frame generator @ 1 Mbps (bench / loopback test).
 *
 * Sends known 29-bit IDs and payloads so esp32-mini-debug can prove RX path.
 * Requires SN65HVD230 (or equivalent) on this board too — ESP32 cannot drive CAN wires directly.
 *
 * TWAI_MODE_NORMAL is required to transmit. On a 2-node bus the other node must ACK;
 * use NORMAL mode on the receiver for this test (see CAN_SIM_WIRING.txt).
 */

#include <Arduino.h>

#include <driver/twai.h>

#include "can_config.h"

namespace {

/** Known IDs (29-bit) — same family as fixtures (FuelTech-style extended). */
constexpr uint32_t ID_RPM_TUPLE = 0x140001FFu;   /* realtime tuple style */
constexpr uint32_t ID_SIMPLE_600 = 0x14080600u; /* simplified 0x600 */

constexpr uint32_t TX_PERIOD_MS = 50u; /* 20 frames per second per pattern */
constexpr uint32_t SERIAL_BAUD = 921600u;

uint32_t g_tx_ok = 0;
uint32_t g_tx_fail = 0;
uint32_t g_seq = 0;
bool     g_alt_id = false;

void send_one(uint32_t id29, const uint8_t* data8) {
    twai_message_t msg{};
    msg.identifier      = id29 & 0x1FFFFFFFu;
    msg.flags           = TWAI_MSG_FLAG_EXTD;
    msg.data_length_code = 8;
    for (int i = 0; i < 8; i++) {
        msg.data[i] = data8[i];
    }

    esp_err_t err = twai_transmit(&msg, pdMS_TO_TICKS(50));
    if (err == ESP_OK) {
        g_tx_ok++;
    } else {
        g_tx_fail++;
    }
}

}  // namespace

void setup() {
    Serial.begin(SERIAL_BAUD);
    delay(200);

    twai_general_config_t g_config =
        TWAI_GENERAL_CONFIG_DEFAULT(static_cast<gpio_num_t>(CAN_TX_GPIO),
                                    static_cast<gpio_num_t>(CAN_RX_GPIO),
                                    TWAI_MODE_NORMAL);
    g_config.tx_queue_len = 16;
    g_config.rx_queue_len = CAN_RX_QUEUE_LEN;

    twai_timing_config_t t_config = CAN_TIMING_1MBPS();
    twai_filter_config_t f_config = can_filter_ext_accept_all();

    esp_err_t err = twai_driver_install(&g_config, &t_config, &f_config);
    if (err != ESP_OK) {
        Serial.printf("{\"type\":\"error\",\"msg\":\"twai_driver_install\",\"code\":%d}\n", static_cast<int>(err));
        while (true) {
            delay(1000);
        }
    }

    err = twai_reconfigure_alerts(CAN_ALERT_MASK, nullptr);
    if (err != ESP_OK) {
        Serial.printf("{\"type\":\"error\",\"msg\":\"twai_reconfigure_alerts\",\"code\":%d}\n",
                      static_cast<int>(err));
    }

    err = twai_start();
    if (err != ESP_OK) {
        Serial.printf("{\"type\":\"error\",\"msg\":\"twai_start\",\"code\":%d}\n", static_cast<int>(err));
        while (true) {
            delay(1000);
        }
    }

    Serial.println("{\"type\":\"startup\",\"firmware\":\"esp32-can-sim\",\"version\":\"1.0.0\","
                   "\"mode\":\"tx\",\"bitrate_kbps\":1000,\"extended\":true}");
}

void loop() {
    uint32_t alerts = 0;
    if (twai_read_alerts(&alerts, 0) == ESP_OK && alerts != 0) {
        if (alerts & TWAI_ALERT_BUS_OFF) {
            Serial.println("{\"type\":\"alert\",\"msg\":\"bus_off\"}");
            twai_initiate_recovery();
        }
    }

    g_seq++;

    /* RPM-style tuple: 0x0084, 0x07D0 = 2000 (big-endian) */
    uint8_t rpm[8] = {0x00, 0x84, 0x07, 0xD0, 0x00, 0x00, 0x00, 0x00};
    /* Simplified 0x600 sample-ish payload */
    uint8_t simp[8] = {0x01, 0xF4, 0x03, 0xF5, 0x00, 0xFA, 0x03, 0x84};

    if (g_alt_id) {
        send_one(ID_SIMPLE_600, simp);
    } else {
        send_one(ID_RPM_TUPLE, rpm);
    }
    g_alt_id = !g_alt_id;

    static uint32_t s_last_stats = 0;
    const uint32_t now = millis();
    if (now - s_last_stats >= 1000u) {
        s_last_stats = now;
        Serial.printf("{\"type\":\"stats\",\"tx_ok\":%lu,\"tx_fail\":%lu,\"seq\":%lu}\n",
                      static_cast<unsigned long>(g_tx_ok),
                      static_cast<unsigned long>(g_tx_fail),
                      static_cast<unsigned long>(g_seq));
    }

    delay(TX_PERIOD_MS);
}
