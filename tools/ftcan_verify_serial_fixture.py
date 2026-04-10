#!/usr/bin/env python3
"""Verify a captured mini-debug JSONL log meets ftcan_e2e_bench expectations (no serial).

Usage:
  python3 tools/ftcan_verify_serial_fixture.py
  python3 tools/ftcan_verify_serial_fixture.py --fixture fixtures/ftcan/serial_bench_golden.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from ftcan_bench_expectations import WANT_CHANNELS, WANT_IDS, accumulate_line, check_bench


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--fixture",
        type=Path,
        default=repo / "fixtures" / "ftcan" / "serial_bench_golden.jsonl",
        help="Path to JSONL (frame + decoded lines)",
    )
    args = ap.parse_args()
    path = args.fixture.resolve()
    if not path.is_file():
        print(f"Missing fixture: {path}", file=sys.stderr)
        return 1

    frames = 0
    ids: set[str] = set()
    decoded: set[str] = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            frames, ids, decoded = accumulate_line(o, frames, ids, decoded)

    ok, errs = check_bench(frames, ids, decoded)
    print(f"Fixture: {path}")
    print(f"Frames: {frames}, unique id29: {len(ids)}, decoded channels: {len(decoded)}")
    print("PASS ids:", bool(ids & WANT_IDS), " PASS channels:", WANT_CHANNELS.issubset(decoded))
    if not ok:
        for e in errs:
            print("FAIL:", e, file=sys.stderr)
        return 1
    print("OVERALL: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
