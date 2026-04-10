#!/usr/bin/env python3
"""Long-run serial soak: periodic stats + final ftcan_bench_expectations checks.

Usage:
  python3 tools/ftcan_soak_bench.py --port /dev/ttyUSB1 --minutes 5 --report-interval 30
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_TOOLS = _REPO / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from ftcan_bench_expectations import (
    BenchHealthState,
    accumulate_health,
    accumulate_line,
    check_bench,
    check_health,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="/dev/ttyUSB1")
    ap.add_argument("--baud", type=int, default=921600)
    ap.add_argument("--minutes", type=float, default=5.0)
    ap.add_argument("--report-interval", type=float, default=30.0)
    ap.add_argument("--max-bus-error-delta", type=int, default=50)
    ap.add_argument("--allow-bus-off-increase", action="store_true")
    ap.add_argument("--no-health-check", action="store_true")
    ap.add_argument(
        "--max-parse-errors",
        type=int,
        default=0,
        help="Fail if JSON parse errors on serial exceed this (UART line integrity).",
    )
    args = ap.parse_args()

    try:
        import serial
    except ImportError:
        print("Install pyserial", file=sys.stderr)
        return 2

    ser = serial.Serial(args.port, args.baud, timeout=0.2)
    time.sleep(0.2)

    frames = 0
    ids: set[str] = set()
    decoded: set[str] = set()
    health = BenchHealthState()
    parse_errors = 0
    t0 = time.time()
    deadline = t0 + args.minutes * 60.0
    next_report = t0

    print(f"Soak started: {args.minutes} min on {args.port}", flush=True)
    while time.time() < deadline:
        raw = ser.readline()
        if not raw:
            continue
        try:
            o = json.loads(raw.decode("utf-8", errors="replace").strip())
        except json.JSONDecodeError:
            parse_errors += 1
            continue
        frames, ids, decoded = accumulate_line(o, frames, ids, decoded)
        accumulate_health(o, health)

        now = time.time()
        if now >= next_report:
            print(
                f"[{now - t0:6.0f}s] frames={frames} id29={len(ids)} decoded_ch={len(decoded)} "
                f"health_lines={health.health_lines} parse_err={parse_errors}",
                flush=True,
            )
            next_report = now + args.report_interval

    ser.close()

    ok, errs = check_bench(frames, ids, decoded)
    ok_h = True
    errs_h: list[str] = []
    if not args.no_health_check:
        ok_h, errs_h = check_health(
            health,
            max_bus_error_delta=args.max_bus_error_delta,
            allow_bus_off_increase=args.allow_bus_off_increase,
        )

    print(
        f"TOTAL frames={frames} unique id29={len(ids)} unique channels={len(decoded)} "
        f"parse_errors={parse_errors}"
    )
    if health.health_lines:
        print(
            f"Health: bus_error {health.bus_error_first}->{health.bus_error_last}  "
            f"bus_off {health.bus_off_first}->{health.bus_off_last}"
        )

    if parse_errors > args.max_parse_errors:
        print(f"FAIL: parse_errors {parse_errors} > max {args.max_parse_errors}", file=sys.stderr)
        return 1

    if not ok:
        for e in errs:
            print("FAIL:", e)
        return 1
    if not ok_h:
        for e in errs_h:
            print("FAIL health:", e)
        return 1
    print("SOAK: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
