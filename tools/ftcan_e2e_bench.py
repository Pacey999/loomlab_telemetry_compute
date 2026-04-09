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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="/dev/ttyUSB1", help="Serial port (receiver)")
    ap.add_argument("--baud", type=int, default=921600)
    ap.add_argument("--seconds", type=float, default=8.0)
    args = ap.parse_args()

    try:
        import serial
    except ImportError:
        print("Install pyserial: pip install pyserial", file=sys.stderr)
        return 2

    ser = serial.Serial(args.port, args.baud, timeout=0.25)
    time.sleep(0.2)

    frames = 0
    decoded = set()
    ids = set()
    t0 = time.time()
    while time.time() - t0 < args.seconds:
        raw = ser.readline()
        if not raw:
            continue
        try:
            o = json.loads(raw.decode("utf-8", errors="replace").strip())
        except json.JSONDecodeError:
            continue
        if o.get("type") == "frame" and "id29" in o:
            frames += 1
            ids.add(o["id29"])
        if o.get("type") == "decoded" and "channel" in o:
            decoded.add(o["channel"])

    ser.close()

    want_ids = {
        "0x140801FF",
        "0x140812FF",
        "0x140810FF",
        "0x14080600",
        "0x14080608",
        "0x140813FF",
    }
    want_ch = {
        "engine.tps_pct",
        "engine.map_bar",
        "vehicle.wheel_speed_fr_kmh",
        "engine.trans_temp_c",
    }

    ok_ids = bool(ids & want_ids)
    ok_ch = want_ch.issubset(decoded)

    print(f"Frames: {frames}, unique id29: {len(ids)}, decoded channels: {len(decoded)}")
    print("Sample id29:", sorted(ids)[:8])
    print("PASS ids:", ok_ids, " PASS channels:", ok_ch)

    if frames < 10:
        print("FAIL: too few frames (check CAN wiring + bench-pair firmware on receiver)")
        return 1
    if not ok_ch:
        print("Missing channels:", want_ch - decoded)
        return 1
    if not ok_ids:
        print("Missing expected CAN IDs (got):", ids)
        return 1
    print("OVERALL: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
