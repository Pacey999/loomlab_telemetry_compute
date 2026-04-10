#!/usr/bin/env bash
# Record a bench session, compare to fingerprint, run Python decode parity.
# Use after firmware changes; save baseline with git tag or dated filename.
#
# Usage:
#   ./scripts/bench_regression.sh [out.jsonl] [seconds]
# Env:
#   FTCAN_RX_PORT   (default /dev/ttyUSB1)
#   FINGERPRINT     path (default fixtures/ftcan/bench_fingerprint.json full bench)

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-$ROOT/runs/bench_capture.jsonl}"
SEC="${2:-45}"
PORT="${FTCAN_RX_PORT:-/dev/ttyUSB1}"
FP="${FINGERPRINT:-$ROOT/fixtures/ftcan/bench_fingerprint.json}"

mkdir -p "$(dirname "$OUT")"
python3 "$ROOT/tools/ftcan_session_record.py" --port "$PORT" --out "$OUT" --seconds "$SEC" --label "bench_regression"
python3 "$ROOT/tools/ftcan_compare_session.py" --capture "$OUT" --fingerprint "$FP"
python3 "$ROOT/tools/ftcan_decode_parity.py" --session "$OUT"
echo "REGRESSION: PASS  ($OUT)"
