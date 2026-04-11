esp32-full — single embedded target for full FTCAN (SSOT + gateway-style output)
--------------------------------------------------------------------------------
This is the only full-map firmware: do not use esp32-ftcan-gateway (removed).

Includes:
  - src/ftcan_registry.h     — generated from measure-registry.json
  - src/decoder.cpp          — tuple + simplified + segmented decode
  - src/gateway_header.*     — type=header JSON (parsed ProductID / DataFieldID / MessageID)
  - Per-frame: header (extended) + frame + decoded lines + health

UART: 921600 (match tools / mini-debug / FT600 sessions).

TWAI:
  - esp32dev (default): LISTEN_ONLY — safe on FT600 without ACKing foreign frames.
  - bench-pair: NORMAL — use with esp32-can-sim two-node bench (ACK).

Regenerate registry:
  python -m shared.protocol.ftcan.generators.gen_cpp

Flash:
  pio run -e esp32dev -t upload --upload-port /dev/ttyUSB0

Host pipeline / replay: shared/protocol/ftcan2/ (Python) complements this firmware.
