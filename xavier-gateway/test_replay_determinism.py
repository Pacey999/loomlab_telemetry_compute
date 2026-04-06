#!/usr/bin/env python3
"""Assert replay produces byte-identical output for identical raw input."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from gateway.replay import replay_session

_REPO_ROOT = Path(__file__).resolve().parent.parent
_FIXTURE = _REPO_ROOT / "fixtures" / "ftcan" / "simplified_0x14080600.jsonl"


def test_replay_twice_byte_identical() -> None:
    assert _FIXTURE.is_file(), f"missing fixture: {_FIXTURE}"

    with tempfile.TemporaryDirectory() as tmp:
        tdir = Path(tmp)
        raw_copy = tdir / "session_raw.jsonl"
        shutil.copy(_FIXTURE, raw_copy)

        out_a = tdir / "out_a.jsonl"
        out_b = tdir / "out_b.jsonl"

        stats_a = replay_session(raw_copy, out_a)
        stats_b = replay_session(raw_copy, out_b)

        assert stats_a == stats_b
        assert stats_a["frames_in"] > 0
        assert stats_a["samples_out"] > 0
        assert stats_a["errors"] == 0

        ba = out_a.read_bytes()
        bb = out_b.read_bytes()
        assert ba == bb, "replay determinism: outputs differ"


if __name__ == "__main__":
    test_replay_twice_byte_identical()
    print("ok: replay determinism")
