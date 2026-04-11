#include "gateway_header.h"

#include <cstdio>

#include "id_parser.h"

void emit_ftcan_header_json(Stream& out, const twai_message_t& msg, uint32_t seq) {
    const uint32_t id29 = msg.identifier & 0x1FFFFFFFu;
    const FtcanId    id = parse_can_id(id29);

    char line[384];
    snprintf(
        line,
        sizeof(line),
        "{\"type\":\"header\",\"id29\":\"0x%08lX\","
        "\"product_id\":\"0x%04X\",\"product_type_id\":\"0x%03X\",\"unique_id\":\"0x%02X\","
        "\"data_field_id\":%u,\"message_id\":\"0x%03X\","
        "\"likely_ft600_ecu\":%s,\"seq\":%lu}",
        static_cast<unsigned long>(id29),
        static_cast<unsigned>(id.product_id),
        static_cast<unsigned>(id.product_type_id),
        static_cast<unsigned>(id.unique_id),
        static_cast<unsigned>(id.data_field_id),
        static_cast<unsigned>(id.message_id),
        id.is_ft600() ? "true" : "false",
        static_cast<unsigned long>(seq));
    out.println(line);
}
