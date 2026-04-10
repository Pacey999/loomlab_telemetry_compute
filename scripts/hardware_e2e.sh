#!/usr/bin/env bash
# Flash esp32-can-sim + esp32-mini-debug (bench-pair) and run tools/ftcan_e2e_bench.py.
# Requires: PlatformIO (pio), pyserial, two USB ESP32s wired per esp32-can-sim/CAN_SIM_WIRING.txt
#
# Env:
#   FTCAN_SIM_PORT   TX board (default /dev/ttyUSB0)
#   FTCAN_RX_PORT    RX board (default /dev/ttyUSB1)
#   SKIP_FLASH=1     Skip upload; only run serial bench (firmware already flashed)

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SIM="${FTCAN_SIM_PORT:-/dev/ttyUSB0}"
RX="${FTCAN_RX_PORT:-/dev/ttyUSB1}"
BENCH_SECONDS="${FTCAN_BENCH_SECONDS:-15}"

if [[ "${SKIP_FLASH:-0}" != "1" ]]; then
  cd "$ROOT/esp32-can-sim"
  pio run -e esp32dev -t upload --upload-port "$SIM"
  cd "$ROOT/esp32-mini-debug"
  pio run -e bench-pair -t upload --upload-port "$RX"
  sleep 2
fi

python3 "$ROOT/tools/ftcan_e2e_bench.py" --port "$RX" --seconds "$BENCH_SECONDS"
