#!/usr/bin/env python3
"""Record esp32-mini-debug serial JSONL to a file with a metadata header line.

Usage:
  python3 tools/ftcan_session_record.py --port /dev/ttyUSB1 --out runs/session.jsonl --seconds 30
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO / "tools") not in sys.path:
    sys.path.insert(0, str(_REPO / "tools"))

from ftcan_session_analysis import analyze_session


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="/dev/ttyUSB1")
    ap.add_argument("--baud", type=int, default=921600)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seconds", type=float, default=30.0)
    ap.add_argument("--label", default="", help="Free-form note stored in meta")
    ap.add_argument(
        "--max-parse-errors",
        type=int,
        default=0,
        help="Exit 1 if JSON lines in file exceed this after capture (see footer).",
    )
    args = ap.parse_args()

    try:
        import serial
    except ImportError:
        print("Install pyserial: pip install pyserial", file=sys.stderr)
        return 2

    args.out.parent.mkdir(parents=True, exist_ok=True)
    meta = {
        "type": "session_meta",
        "version": 1,
        "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "port": args.port,
        "baud": args.baud,
        "planned_seconds": args.seconds,
        "label": args.label or None,
    }

    ser = serial.Serial(args.port, args.baud, timeout=0.2)
    time.sleep(0.15)
    # Drain buffered bytes so we do not start recording mid-line (avoids truncated JSON).
    drain_until = time.time() + 0.35
    while time.time() < drain_until:
        n = ser.in_waiting
        if n:
            ser.read(n)
        else:
            time.sleep(0.02)
    t0 = time.time()
    raw_count = 0
    deadline = t0 + args.seconds
    rx_buf = bytearray()

    # Chunked read + newline split: readline() at 921600 can lose bytes if disk I/O lags.
    with open(args.out, "w", encoding="utf-8", buffering=1024 * 1024) as fout:
        fout.write(json.dumps(meta, ensure_ascii=False) + "\n")
        while time.time() < deadline:
            n = ser.in_waiting
            if n == 0:
                time.sleep(0.0005)
                continue
            block = ser.read(min(65536, n))
            rx_buf.extend(block)
            while True:
                i = rx_buf.find(b"\n")
                if i < 0:
                    break
                line = rx_buf[: i + 1]
                del rx_buf[: i + 1]
                raw_count += 1
                fout.write(line.decode("utf-8", errors="replace"))
            if len(rx_buf) > 256 * 1024:
                rx_buf.clear()

    ser.close()
    meta["actual_seconds"] = round(time.time() - t0, 3)
    meta["raw_lines"] = raw_count

    st = analyze_session(args.out)
    footer = {
        "type": "session_footer",
        "version": 1,
        "parse_errors": st.parse_errors,
        "frame_lines": st.frame_lines,
        "decoded_lines": st.decoded_lines,
        "health_lines": st.health_lines,
        "unique_id29": len(st.id29),
        "unique_decoded_channels": len(st.decoded_channels),
        "bus_error_first": st.bus_error_first,
        "bus_error_last": st.bus_error_last,
        "bus_off_first": st.bus_off_first,
        "bus_off_last": st.bus_off_last,
    }
    with open(args.out, "a", encoding="utf-8") as fout:
        fout.write(json.dumps(footer, ensure_ascii=False) + "\n")

    print(f"Wrote {args.out}  raw_lines={raw_count}  frames={st.frame_lines}  decoded={st.decoded_lines}")
    print(f"unique id29={len(st.id29)}  unique channels={len(st.decoded_channels)}  parse_errors={st.parse_errors}")
    if st.parse_errors > args.max_parse_errors:
        print(
            f"FAIL: parse_errors {st.parse_errors} > max {args.max_parse_errors}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
