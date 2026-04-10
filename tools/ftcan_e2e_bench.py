#!/usr/bin/env python3
"""
Read esp32-mini-debug serial JSON for a few seconds and verify FTCAN E2E bench output.

Usage:
  python3 tools/ftcan_e2e_bench.py --port /dev/ttyUSB1 --seconds 8

PASS: sees expected frame id29 prefixes and decoded channel names from the simulator.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from ftcan_bench_expectations import (
    BenchHealthState,
    WANT_CHANNELS,
    WANT_IDS,
    accumulate_health,
    accumulate_line,
    check_bench,
    check_health,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="/dev/ttyUSB1", help="Serial port (receiver)")
    ap.add_argument("--baud", type=int, default=921600)
    ap.add_argument("--seconds", type=float, default=8.0)
    ap.add_argument(
        "--max-bus-error-delta",
        type=int,
        default=10,
        help="Fail if bus_error_count grows by more than this over the run (from type=health lines).",
    )
    ap.add_argument(
        "--allow-bus-off-increase",
        action="store_true",
        help="Allow bus_off_count to increase (default: fail if it increases).",
    )
    ap.add_argument(
        "--no-health-check",
        action="store_true",
        help="Ignore type=health TWAI counters.",
    )
    args = ap.parse_args()

    try:
        import serial
    except ImportError:
        print("Install pyserial: pip install pyserial", file=sys.stderr)
        return 2

    ser = serial.Serial(args.port, args.baud, timeout=0.25)
    time.sleep(0.2)

    frames = 0
    decoded: set[str] = set()
    ids: set[str] = set()
    health = BenchHealthState()
    t0 = time.time()
    while time.time() - t0 < args.seconds:
        raw = ser.readline()
        if not raw:
            continue
        try:
            o = json.loads(raw.decode("utf-8", errors="replace").strip())
        except json.JSONDecodeError:
            continue
        frames, ids, decoded = accumulate_line(o, frames, ids, decoded)
        accumulate_health(o, health)

    ser.close()

    ok_ids = bool(ids & WANT_IDS)
    ok_ch = WANT_CHANNELS.issubset(decoded)
    ok, errs = check_bench(frames, ids, decoded)
    ok_h = True
    errs_h: list[str] = []
    if not args.no_health_check:
        ok_h, errs_h = check_health(
            health,
            max_bus_error_delta=args.max_bus_error_delta,
            allow_bus_off_increase=args.allow_bus_off_increase,
        )

    print(f"Frames: {frames}, unique id29: {len(ids)}, decoded channels: {len(decoded)}")
    if health.health_lines:
        print(
            f"Health lines: {health.health_lines}, bus_error {health.bus_error_first}->{health.bus_error_last}, "
            f"bus_off {health.bus_off_first}->{health.bus_off_last}"
        )
    print("Sample id29:", sorted(ids)[:8])
    print("PASS ids:", ok_ids, " PASS channels:", ok_ch, " PASS health:", ok_h)

    if not ok:
        for e in errs:
            print("FAIL:", e)
        if frames < 10:
            print("(check CAN wiring + bench-pair firmware on receiver)")
        if not ok_ch:
            print("Missing channels:", sorted(WANT_CHANNELS - decoded))
        if not ok_ids:
            print("Missing expected CAN IDs (got):", sorted(ids))
        return 1
    if not ok_h:
        for e in errs_h:
            print("FAIL health:", e)
        return 1
    print("OVERALL: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
