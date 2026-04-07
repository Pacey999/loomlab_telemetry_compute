#pragma once

/**
 * CAN / TWAI — same pinout as esp32-mini-debug (bench consistency).
 * ESP32 GPIO -> transceiver TXD/RXD -> CAN-H / CAN-L
 */

#include <driver/twai.h>

#ifndef CAN_TX_GPIO
#define CAN_TX_GPIO 21
#endif

#ifndef CAN_RX_GPIO
#define CAN_RX_GPIO 22
#endif

#define CAN_RX_QUEUE_LEN 16

#define CAN_TIMING_1MBPS TWAI_TIMING_CONFIG_1MBITS

inline twai_filter_config_t can_filter_ext_accept_all() {
    twai_filter_config_t f{};
    f.acceptance_code  = 0;
    f.acceptance_mask  = 0xFFFFFFFF;
    f.single_filter    = true;
    return f;
}

#define CAN_ALERT_MASK                                                   \
    ((uint32_t)(TWAI_ALERT_RX_DATA | TWAI_ALERT_ERR_PASS |                \
                TWAI_ALERT_BUS_ERROR | TWAI_ALERT_RX_QUEUE_FULL |         \
                TWAI_ALERT_BUS_OFF | TWAI_ALERT_BUS_RECOVERED))
