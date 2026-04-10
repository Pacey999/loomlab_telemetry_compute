#!/usr/bin/env python3
"""Compare a captured session against a bench fingerprint (required IDs + channels).

Usage:
  python3 tools/ftcan_compare_session.py --capture runs/foo.jsonl --fingerprint fixtures/ftcan/bench_fingerprint.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO / "tools") not in sys.path:
    sys.path.insert(0, str(_REPO / "tools"))

from ftcan_session_analysis import analyze_session


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--capture", type=Path, required=True)
    ap.add_argument(
        "--fingerprint",
        type=Path,
        default=_REPO / "fixtures" / "ftcan" / "bench_fingerprint.json",
    )
    args = ap.parse_args()

    if not args.capture.is_file():
        print(f"Missing capture: {args.capture}", file=sys.stderr)
        return 1
    if not args.fingerprint.is_file():
        print(f"Missing fingerprint: {args.fingerprint}", file=sys.stderr)
        return 1

    with open(args.fingerprint, encoding="utf-8") as f:
        fp = json.load(f)

    st = analyze_session(args.capture)
    errs: list[str] = []

    req_ids = {str(x) for x in fp.get("required_id29", [])}
    missing_ids = req_ids - st.id29
    if missing_ids:
        errs.append(f"missing id29: {sorted(missing_ids)}")

    req_ch = {str(x) for x in fp.get("required_channels", [])}
    missing_ch = req_ch - st.decoded_channels
    if missing_ch:
        errs.append(f"missing decoded channels: {sorted(missing_ch)}")

    min_ids = int(fp.get("min_unique_id29", 0))
    if min_ids and len(st.id29) < min_ids:
        errs.append(f"unique id29 {len(st.id29)} < min {min_ids}")

    min_ch = int(fp.get("min_decoded_channel_count", 0))
    if min_ch and len(st.decoded_channels) < min_ch:
        errs.append(f"decoded channel count {len(st.decoded_channels)} < min {min_ch}")

    min_frames = int(fp.get("min_frame_lines", 0))
    if min_frames and st.frame_lines < min_frames:
        errs.append(f"frame_lines {st.frame_lines} < min {min_frames}")

    if fp.get("fail_on_parse_errors") and st.parse_errors:
        errs.append(f"parse_errors={st.parse_errors}")

    be_max = fp.get("max_bus_error_delta")
    if be_max is not None and st.bus_error_first is not None and st.bus_error_last is not None:
        if st.bus_error_last - st.bus_error_first > int(be_max):
            errs.append(
                f"bus_error_count delta {st.bus_error_last - st.bus_error_first} > max {be_max}"
            )

    if not fp.get("allow_bus_off_increase", False):
        if st.bus_off_first is not None and st.bus_off_last is not None and st.bus_off_last > st.bus_off_first:
            errs.append(f"bus_off_count increased {st.bus_off_first}->{st.bus_off_last}")

    print(f"Capture: {args.capture}")
    print(f"  frames={st.frame_lines} decoded_lines={st.decoded_lines} unique_id29={len(st.id29)} channels={len(st.decoded_channels)}")
    print(f"  parse_errors={st.parse_errors}")

    if errs:
        for e in errs:
            print("FAIL:", e)
        return 1
    print("COMPARE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
