#include "frame_output.h"

#include <cstdio>

void emit_raw_frame(Stream& out, const twai_message_t& msg, uint32_t ts_ms, uint32_t seq) {
    const uint32_t id29 = msg.identifier & 0x1FFFFFFFu;
    const uint8_t  dlc  = msg.data_length_code > 8 ? 8 : msg.data_length_code;

    char  data_seg[96];
    char* p   = data_seg;
    char* end = data_seg + sizeof(data_seg);
    *p++ = '[';
    for (uint8_t i = 0; i < dlc; i++) {
        int n = snprintf(p, static_cast<size_t>(end - p), "%s%u", (i == 0) ? "" : ",", msg.data[i]);
        if (n <= 0 || static_cast<size_t>(n) >= static_cast<size_t>(end - p)) {
            break;
        }
        p += static_cast<size_t>(n);
    }
    if (p < end) {
        *p++ = ']';
        *p   = '\0';
    } else {
        data_seg[sizeof(data_seg) - 2] = ']';
        data_seg[sizeof(data_seg) - 1] = '\0';
    }

    char line[320];
    snprintf(
        line,
        sizeof(line),
        "{\"type\":\"frame\",\"id29\":\"0x%08lX\",\"dlc\":%u,\"data\":%s,"
        "\"ts_ms\":%lu,\"seq\":%lu}",
        static_cast<unsigned long>(id29),
        static_cast<unsigned>(msg.data_length_code),
        data_seg,
        static_cast<unsigned long>(ts_ms),
        static_cast<unsigned long>(seq));
    out.println(line);
}

void emit_decoded_sample(Stream&     out,
                         const char* channel,
                         float       value,
                         const char* unit,
                         const char* quality,
                         uint16_t    measure_id,
                         uint32_t    seq) {
    char line[384];
    snprintf(line,
             sizeof(line),
             "{\"type\":\"decoded\",\"channel\":\"%s\",\"value\":%.9g,\"unit\":\"%s\","
             "\"quality\":\"%s\",\"measure_id\":%u,\"seq\":%lu}",
             channel,
             static_cast<double>(value),
             unit,
             quality,
             static_cast<unsigned>(measure_id),
             static_cast<unsigned long>(seq));
    out.println(line);
}
