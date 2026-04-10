#!/usr/bin/env bash
# Long soak on receiver serial (default 45 min). Tune MINUTES or use for overnight runs.
# Requires: pyserial, esp32-can-sim + esp32-mini-debug bench-pair on CAN.
#
# Usage:
#   ./scripts/bench_soak_long.sh
#   MINUTES=60 FTCAN_RX_PORT=/dev/ttyUSB1 ./scripts/bench_soak_long.sh

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MINUTES="${MINUTES:-45}"
PORT="${FTCAN_RX_PORT:-/dev/ttyUSB1}"

exec python3 "$ROOT/tools/ftcan_soak_bench.py" --port "$PORT" --minutes "$MINUTES" --report-interval 60
