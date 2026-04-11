#!/usr/bin/env python3
"""Replay JSONL `frame` lines through FtcanPipeline (deterministic decode for CI).

Usage:
  python3 tools/ftcan2_replay.py --session shared/protocol/ftcan2/fixtures/sample_session.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from shared.protocol.ftcan2.model import RawCanFrame
from shared.protocol.ftcan2.pipeline import FtcanPipeline


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", type=Path, required=True, help="JSONL with type=frame lines")
    args = ap.parse_args()

    pipe = FtcanPipeline()
    n = 0
    with open(args.session, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            if o.get("type") != "frame":
                continue
            id_s = o.get("id29", "")
            if not isinstance(id_s, str) or not id_s.startswith("0x"):
                continue
            id29 = int(id_s, 16)
            dlc = int(o.get("dlc", 0))
            raw_data = o.get("data")
            if not isinstance(raw_data, list):
                continue
            b = bytes(int(x) & 0xFF for x in raw_data[:8])
            dlc = min(dlc, len(b))
            ts = int(o.get("ts_ms", 0))
            fr = RawCanFrame(ts_ms=ts, id29=id29, dlc=dlc, data=b[:dlc])
            r = pipe.process(fr)
            rec = {
                "type": "ftcan2_pipeline",
                "seq": n,
                "stage": int(r.stage),
                "header": r.header,
                "datafield": r.datafield,
                "error": r.error,
            }
            print(json.dumps(rec, ensure_ascii=False))
            n += 1
    return 0 if n > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
