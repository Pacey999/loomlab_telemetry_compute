/**
 * esp32-can-sim — Extended-ID CAN frame generator @ 1 Mbps (bench / loopback test).
 *
 * Sends known 29-bit IDs and payloads so esp32-mini-debug can prove RX path.
 * Requires SN65HVD230 (or equivalent) on this board too — ESP32 cannot drive CAN wires directly.
 *
 * TWAI_MODE_NORMAL is required to transmit. On a 2-node bus the other node must ACK;
 * use NORMAL mode on the receiver for this test (see CAN_SIM_WIRING.txt).
 *
 * Build with -DCAN_LOOPBACK_TEST=1 (env:loopback-test) to run the two-stage
 * connectivity test instead of the normal frame generator.
 */

#include <Arduino.h>

#include <driver/twai.h>

#include "can_config.h"

// ─── LOOPBACK / CONNECTIVITY TEST ────────────────────────────────────────────
#ifdef CAN_LOOPBACK_TEST

static constexpr uint32_t TEST_ID      = 0x1FFFFFFFu;
static constexpr uint8_t  TEST_PAYLOAD = 0xA5u;

static void twai_stop_uninstall() { twai_stop(); twai_driver_uninstall(); }

static bool install_start(twai_mode_t mode) {
    twai_general_config_t g =
        TWAI_GENERAL_CONFIG_DEFAULT(static_cast<gpio_num_t>(CAN_TX_GPIO),
                                    static_cast<gpio_num_t>(CAN_RX_GPIO),
                                    mode);
    g.rx_queue_len = 8;
    twai_timing_config_t t = CAN_TIMING_1MBPS();
    twai_filter_config_t f = can_filter_ext_accept_all();
    if (twai_driver_install(&g, &t, &f) != ESP_OK) return false;
    if (twai_start() != ESP_OK) { twai_driver_uninstall(); return false; }
    return true;
}

static void stage1_loopback() {
    if (!install_start(TWAI_MODE_NO_ACK)) {
        Serial.println("{\"test\":\"loopback\",\"stage\":1,\"result\":\"FAIL\","
                       "\"detail\":\"driver install failed\"}");
        return;
    }
    twai_message_t m{};
    m.identifier = TEST_ID; m.flags = TWAI_MSG_FLAG_EXTD;
    m.data_length_code = 1; m.data[0] = TEST_PAYLOAD;
    twai_transmit(&m, pdMS_TO_TICKS(200));

    twai_message_t rx{};
    esp_err_t err = twai_receive(&rx, pdMS_TO_TICKS(500));
    if (err == ESP_OK && rx.identifier == TEST_ID && rx.data[0] == TEST_PAYLOAD) {
        Serial.println("{\"test\":\"loopback\",\"stage\":1,\"result\":\"PASS\","
                       "\"detail\":\"transceiver wiring OK\"}");
    } else if (err == ESP_ERR_TIMEOUT) {
        Serial.println("{\"test\":\"loopback\",\"stage\":1,\"result\":\"FAIL\","
                       "\"detail\":\"timeout — check TXD/RXD wires to transceiver\"}");
    } else {
        Serial.printf("{\"test\":\"loopback\",\"stage\":1,\"result\":\"FAIL\","
                      "\"detail\":\"err %d\"}\n", (int)err);
    }
    twai_stop_uninstall();
    delay(300);
}

static void stage2_bus_link() {
    if (!install_start(TWAI_MODE_NORMAL)) {
        Serial.println("{\"test\":\"bus_link\",\"stage\":2,\"result\":\"FAIL\","
                       "\"detail\":\"driver install failed\"}");
        return;
    }
    uint32_t tx_ok = 0, tx_fail = 0, rx_count = 0;
    const uint32_t deadline = millis() + 5000u;
    while (millis() < deadline) {
        twai_message_t m{};
        m.identifier = TEST_ID; m.flags = TWAI_MSG_FLAG_EXTD;
        m.data_length_code = 1; m.data[0] = TEST_PAYLOAD;
        if (twai_transmit(&m, pdMS_TO_TICKS(50)) == ESP_OK) tx_ok++; else tx_fail++;
        twai_message_t rx{};
        while (twai_receive(&rx, 0) == ESP_OK) rx_count++;
        delay(100);
    }
    twai_message_t rx{};
    while (twai_receive(&rx, pdMS_TO_TICKS(50)) == ESP_OK) rx_count++;

    const bool pass = tx_ok > 0 && rx_count > 0;
    const char* note = tx_fail > 0 && rx_count == 0
        ? "no ACK — is receiver also flashed and connected?"
        : tx_ok > 0 && rx_count == 0
            ? "tx ok but rx=0 — check CAN-H/CAN-L between boards"
            : "tx and rx both working";
    Serial.printf("{\"test\":\"bus_link\",\"stage\":2,\"result\":\"%s\","
                  "\"tx_ok\":%lu,\"tx_fail\":%lu,\"rx_count\":%lu,\"note\":\"%s\"}\n",
                  pass ? "PASS" : "FAIL",
                  (unsigned long)tx_ok, (unsigned long)tx_fail,
                  (unsigned long)rx_count, note);
    twai_stop_uninstall();
}

void setup() {
    Serial.begin(921600);
    delay(300);
    Serial.printf("{\"test\":\"start\",\"pin_tx\":%d,\"pin_rx\":%d,\"bitrate\":\"1Mbps\"}\n",
                  CAN_TX_GPIO, CAN_RX_GPIO);
    stage1_loopback();
    delay(500);
    stage2_bus_link();
    Serial.println("{\"test\":\"done\"}");
}
void loop() { delay(5000); }

#else  // ─── NORMAL FRAME GENERATOR ──────────────────────────────────────────

namespace {

/** Known IDs (29-bit) — same family as fixtures (FuelTech-style extended). */
constexpr uint32_t ID_RPM_TUPLE = 0x140001FFu;   /* realtime tuple style */
constexpr uint32_t ID_SIMPLE_600 = 0x14080600u; /* simplified 0x600 */

/** ~10 Hz total (~5 Hz per ID) — leaves headroom for ACK + UART on both boards. */
constexpr uint32_t TX_PERIOD_MS = 100u;
constexpr uint32_t SERIAL_BAUD = 921600u;

uint32_t g_tx_ok = 0;
uint32_t g_tx_fail = 0;
uint32_t g_seq = 0;
bool     g_alt_id = false;
bool     g_logged_tx_err = false;

void send_one(uint32_t id29, const uint8_t* data8) {
    twai_message_t msg{};
    msg.identifier      = id29 & 0x1FFFFFFFu;
    msg.flags           = TWAI_MSG_FLAG_EXTD;
    msg.data_length_code = 8;
    for (int i = 0; i < 8; i++) {
        msg.data[i] = data8[i];
    }

    esp_err_t err = twai_transmit(&msg, pdMS_TO_TICKS(500));
    if (err == ESP_OK) {
        g_tx_ok++;
    } else {
        g_tx_fail++;
        if (!g_logged_tx_err) {
            g_logged_tx_err = true;
            Serial.printf(
                "{\"type\":\"tx_err\",\"code\":%d,\"msg\":\"first twai_transmit failure; "
                "ESP_ERR_TIMEOUT often means no ACK (receiver must be NORMAL on 2-node bus)\"}\n",
                static_cast<int>(err));
        }
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

    Serial.println("{\"type\":\"startup\",\"firmware\":\"esp32-can-sim\",\"version\":\"1.0.1\","
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

    /* Drain RX so error frames / stray traffic do not fill the queue. */
    twai_message_t rx{};
    while (twai_receive(&rx, 0) == ESP_OK) {
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

#endif  // CAN_LOOPBACK_TEST
