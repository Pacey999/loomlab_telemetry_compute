#!/usr/bin/env python3
"""Print SessionStats JSON for a recorded JSONL session."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO / "tools") not in sys.path:
    sys.path.insert(0, str(_REPO / "tools"))

from ftcan_session_analysis import SessionStats, analyze_session


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("session", type=Path)
    args = ap.parse_args()
    if not args.session.is_file():
        print(f"Missing {args.session}", file=sys.stderr)
        return 1
    st = analyze_session(args.session)
    d = asdict(st)
    # sets -> sorted lists for JSON
    d["id29"] = sorted(d["id29"], key=lambda x: int(x, 16))
    d["decoded_channels"] = sorted(d["decoded_channels"])
    d["other_types"] = dict(st.other_types)
    print(json.dumps(d, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
