#!/usr/bin/env python3
"""Replay determinism test.

Replays raw fixture sessions twice through the Xavier canonical decoder
and asserts byte-identical output.
"""
import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "xavier-gateway"))

from gateway.replay import replay_session

FIXTURES_DIR = _ROOT / "fixtures" / "ftcan"


def test_determinism(fixture_name: str) -> bool:
    raw_path = FIXTURES_DIR / fixture_name
    if not raw_path.exists():
        print(f"SKIP {fixture_name}: not found")
        return True

    with tempfile.TemporaryDirectory() as tmpdir:
        out1 = Path(tmpdir) / "replay_1.jsonl"
        out2 = Path(tmpdir) / "replay_2.jsonl"

        stats1 = replay_session(raw_path, out1, session_id="determinism_test")
        stats2 = replay_session(raw_path, out2, session_id="determinism_test")

        if stats1 != stats2:
            print(f"FAIL {fixture_name}: stats differ {stats1} vs {stats2}")
            return False

        content1 = out1.read_text()
        content2 = out2.read_text()

        if content1 != content2:
            lines1 = content1.splitlines()
            lines2 = content2.splitlines()
            for i, (a, b) in enumerate(zip(lines1, lines2)):
                if a != b:
                    print(f"FAIL {fixture_name}: line {i+1} differs")
                    print(f"  run1: {a[:120]}")
                    print(f"  run2: {b[:120]}")
                    return False
            print(f"FAIL {fixture_name}: different number of lines ({len(lines1)} vs {len(lines2)})")
            return False

        print(f"PASS {fixture_name}: {stats1['frames_in']} frames -> {stats1['samples_out']} samples, byte-identical")
        return True


def main():
    fixtures = [
        "realtime_tuple_rpm_2000.jsonl",
        "simplified_0x14080600.jsonl",
        "simplified_0x14080603.jsonl",
        "segmented_multi_measure.jsonl",
    ]

    all_pass = True
    for f in fixtures:
        if not test_determinism(f):
            all_pass = False

    if all_pass:
        print("\nALL DETERMINISM TESTS PASS")
        sys.exit(0)
    else:
        print("\nSOME TESTS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
