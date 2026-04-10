#!/usr/bin/env python3
"""Replay session frame lines through GatewayDecoder (Python) and compare channel coverage to ESP32 decoded lines.

Usage:
  python3 tools/ftcan_decode_parity.py --session fixtures/ftcan/serial_bench_golden.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
if str(_REPO / "xavier-gateway") not in sys.path:
    sys.path.insert(0, str(_REPO / "xavier-gateway"))

from gateway.decoder import GatewayDecoder


_WALL0 = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


def _wall(ts_ms: int) -> str:
    dt = _WALL0 + timedelta(milliseconds=ts_ms)
    return dt.isoformat().replace("+00:00", "Z")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", type=Path, required=True)
    args = ap.parse_args()

    if not args.session.is_file():
        print(f"Missing {args.session}", file=sys.stderr)
        return 1

    dec = GatewayDecoder()
    py_channels: set[str] = set()
    esp32_channels: set[str] = set()
    frames_in = 0

    with open(args.session, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            if o.get("type") in ("session_meta", "session_footer"):
                continue
            if o.get("type") == "decoded" and "channel" in o:
                esp32_channels.add(str(o["channel"]))
                continue
            if o.get("type") != "frame" or "id29" not in o:
                continue
            frames_in += 1
            ts_ms = int(o.get("ts_ms", 0))
            mono_ns = ts_ms * 1_000_000
            out = dec.decode_frame(o, "parity", mono_ns, _wall(ts_ms))
            for row in out:
                py_channels.add(str(row["channel"]))

    only_py = py_channels - esp32_channels
    only_esp = esp32_channels - py_channels

    print(f"Session: {args.session}")
    print(f"  frame objects replayed: {frames_in}")
    print(f"  Python channels: {len(py_channels)}  ESP32 decoded channels: {len(esp32_channels)}")
    if only_py:
        print(f"  INFO only in Python ({len(only_py)}): {sorted(only_py)[:15]}...")
    if only_esp:
        print(f"  FAIL only on ESP32 (not in Python replay): {sorted(only_esp)}")

    # SSOT: every channel the firmware emitted must be reproducible from raw frames in Python.
    if only_esp:
        print("PARITY: FAIL (firmware decoded channels missing from GatewayDecoder replay)")
        return 1
    print("PARITY: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
