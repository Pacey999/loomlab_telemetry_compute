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
#include "id_parser.h"

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

#else  // ─── NORMAL FRAME GENERATOR (FTCAN 2.0 E2E bench) ─────────────────────

namespace {

/** FT600 default ProductID (unique ID 0). All IDs must pass mini_decode is_ft600(). */
constexpr uint16_t k_ft600_pid = 0x5020u;

/*
 * Rotating E2E pattern — one frame per tick (~12.5 Hz per phase @ 80 ms).
 * Covers: realtime tuples (DFI 0x00 / 0x02), simplified 0x600–0x608, 2-frame segmented.
 */
constexpr uint32_t TX_PERIOD_MS = 80u;
constexpr uint32_t SERIAL_BAUD    = 921600u;
constexpr uint8_t  k_num_phases   = 13u;

uint32_t g_tx_ok = 0;
uint32_t g_tx_fail = 0;
uint32_t g_seq = 0;
uint8_t  g_phase = 0;
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

    Serial.println("{\"type\":\"startup\",\"firmware\":\"esp32-can-sim\",\"version\":\"1.2.0\","
                   "\"mode\":\"ftcan_e2e\",\"product_id\":\"0x5020\",\"phases\":13,"
                   "\"bitrate_kbps\":1000,\"extended\":true}");
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

    /* Pre-built payloads — big-endian int16 per FTCAN spec. */
    uint8_t d[8] = {};

    uint32_t id29   = 0;
    bool     skip_single_send = false;
    switch (g_phase) {
        case 0: {
            /* Realtime tuple, DFI 0x00, MID 0x1FF — two measures: TPS + MAP */
            id29 = build_can_id(k_ft600_pid, 0x00, 0x1FF);
            d[0] = 0x00;
            d[1] = 0x02;
            d[2] = 0x03;
            d[3] = 0xE8; /* TPS raw 1000 → 100.0 % */
            d[4] = 0x00;
            d[5] = 0x04;
            d[6] = 0x03;
            d[7] = 0xE8; /* MAP raw 1000 → 1.000 bar */
        } break;
        case 1: {
            /* FTCAN 2.0 single-packet (seg 0xFF), MID 0x2FF — TPS only */
            id29 = build_can_id(k_ft600_pid, 0x02, 0x2FF);
            d[0] = 0xFF;
            d[1] = 0x00;
            d[2] = 0x02;
            d[3] = 0x03;
            d[4] = 0xE8;
            d[5] = 0x00;
            d[6] = 0x00;
            d[7] = 0x00;
        } break;
        case 2: {
            /* FTCAN 2.0 first segment: total payload 4 B, one tuple TPS */
            id29 = build_can_id(k_ft600_pid, 0x02, 0x0FF);
            d[0] = 0x00;
            d[1] = 0x00;
            d[2] = 0x04;
            d[3] = 0x00;
            d[4] = 0x02;
            d[5] = 0x03;
            d[6] = 0xE8;
            d[7] = 0x00;
        } break;
        case 3: {
            /* Simplified 0x600 — matches measure-registry simplifiedPackets.0x600 */
            id29 = build_can_id(k_ft600_pid, 0x00, 0x600);
            d[0] = 0x01;
            d[1] = 0xF4; /* TPS 500 → 50 % */
            d[2] = 0x03;
            d[3] = 0xE8; /* MAP 1000 → 1 bar */
            d[4] = 0x01;
            d[5] = 0x90; /* air 400 → 40 °C */
            d[6] = 0x03;
            d[7] = 0x20; /* coolant 800 → 80 °C */
        } break;
        case 4: {
            id29 = build_can_id(k_ft600_pid, 0x00, 0x601);
            d[0] = 0x03;
            d[1] = 0xE8;
            d[2] = 0x03;
            d[3] = 0xE8;
            d[4] = 0x03;
            d[5] = 0xE8;
            d[6] = 0x00;
            d[7] = 0x05;
        } break;
        case 5: {
            id29 = build_can_id(k_ft600_pid, 0x00, 0x602);
            d[0] = 0x07;
            d[1] = 0xD0; /* lambda raw */
            d[2] = 0x07;
            d[3] = 0xD0; /* 2000 RPM */
            d[4] = 0x00;
            d[5] = 0xB4;
            d[6] = 0x00;
            d[7] = 0x01;
        } break;
        case 6: {
            id29 = build_can_id(k_ft600_pid, 0x00, 0x603);
            d[0] = 0x00;
            d[1] = 0x64;
            d[2] = 0x00;
            d[3] = 0x65;
            d[4] = 0x00;
            d[5] = 0x66;
            d[6] = 0x00;
            d[7] = 0x67;
        } break;
        case 7: {
            id29 = build_can_id(k_ft600_pid, 0x00, 0x604);
            d[0] = 0x00;
            d[1] = 0x0A;
            d[2] = 0x00;
            d[3] = 0x14;
            d[4] = 0x00;
            d[5] = 0x1E;
            d[6] = 0x01;
            d[7] = 0x2C;
        } break;
        case 8: {
            id29 = build_can_id(k_ft600_pid, 0x00, 0x605);
            d[0] = 0x03;
            d[1] = 0xE8;
            d[2] = 0x03;
            d[3] = 0xE9;
            d[4] = 0x03;
            d[5] = 0xEA;
            d[6] = 0x03;
            d[7] = 0xEB;
        } break;
        case 9: {
            id29 = build_can_id(k_ft600_pid, 0x00, 0x606);
            d[0] = 0x00;
            d[1] = 0x64;
            d[2] = 0xFF;
            d[3] = 0x9C;
            d[4] = 0x00;
            d[5] = 0x32;
            d[6] = 0x00;
            d[7] = 0x33;
        } break;
        case 10: {
            id29 = build_can_id(k_ft600_pid, 0x00, 0x607);
            d[0] = 0x03;
            d[1] = 0xE8;
            d[2] = 0x01;
            d[3] = 0xF4;
            d[4] = 0x02;
            d[5] = 0x58;
            d[6] = 0x00;
            d[7] = 0xC8;
        } break;
        case 11: {
            id29 = build_can_id(k_ft600_pid, 0x00, 0x608);
            d[0] = 0x01;
            d[1] = 0xF4;
            d[2] = 0x00;
            d[3] = 0x64;
            d[4] = 0x13;
            d[5] = 0x88;
            d[6] = 0x02;
            d[7] = 0xBC;
        } break;
        case 12: {
            /* Two CAN frames: 8 B payload = TPS + MAP tuples, MID 0x3FF, DFI 0x02 */
            id29 = build_can_id(k_ft600_pid, 0x02, 0x3FF);
            const uint8_t s0[8] = {0x00, 0x00, 0x08, 0x00, 0x02, 0x03, 0xE8, 0x00};
            const uint8_t s1[8] = {0x01, 0x04, 0x03, 0xE8, 0x00, 0x00, 0x00, 0x00};
            send_one(id29, s0);
            send_one(id29, s1);
            skip_single_send = true;
        } break;
        default:
            break;
    }

    if (!skip_single_send) {
        send_one(id29, d);
    }
    g_phase = static_cast<uint8_t>((g_phase + 1u) % k_num_phases);

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
