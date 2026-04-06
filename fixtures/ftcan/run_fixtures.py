#!/usr/bin/env python3
"""Run FTCAN JSONL fixtures against shared decoders and compare to expected outputs."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

_ROOT = "/home/mark/Documents/LoomLab_Telemetry_Compute"
sys.path.insert(0, _ROOT)

from shared.protocol.ftcan.framing.segmentation import SegmentAssembler
from shared.protocol.ftcan.normalize.decoder import DecodedSample, FtcanDecoder
from shared.protocol.ftcan.parsers.id_parser import parse_can_id

_FIXTURE_DIR = Path(__file__).resolve().parent
_EXPECTED_DIR = _FIXTURE_DIR / "expected_outputs"

_FIXTURES = [
    "realtime_tuple_rpm_2000",
    "simplified_0x14080600",
    "simplified_0x14080603",
    "segmented_multi_measure",
]


def _load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _sample_to_dict(s: DecodedSample) -> dict:
    return {
        "channel": s.channel,
        "value": float(s.value),
        "unit": s.unit,
        "quality": s.quality,
    }


def _samples_close(a: dict, b: dict) -> bool:
    if a.keys() != b.keys():
        return False
    for k in a:
        if k == "value":
            if not math.isclose(float(a[k]), float(b[k]), rel_tol=0.0, abs_tol=1e-6):
                return False
        elif a[k] != b[k]:
            return False
    return True


def _compare_samples(actual: list[DecodedSample], expected: list[dict]) -> list[str]:
    errs: list[str] = []
    if len(actual) != len(expected):
        errs.append(f"sample count: got {len(actual)}, want {len(expected)}")
        return errs
    for i, (s, exp) in enumerate(zip(actual, expected)):
        got = _sample_to_dict(s)
        if not _samples_close(got, exp):
            errs.append(f"sample[{i}]: got {got}, want {exp}")
    return errs


def _decode_line(
    decoder: FtcanDecoder,
    assembler: SegmentAssembler | None,
    row: dict,
) -> list[DecodedSample]:
    id29 = row["id29"]
    raw_id = int(id29, 16) if isinstance(id29, str) else int(id29)
    ftcan_id = parse_can_id(raw_id)
    data = bytes(row["data"])

    if ftcan_id.is_segmented:
        assert assembler is not None
        assembled = assembler.feed(data)
        if assembled is None:
            return []
        return decoder.decode_tuple_payload(assembled, ftcan_id)

    return decoder.decode_frame(ftcan_id, data)


def run_fixture(name: str) -> tuple[bool, list[str]]:
    inp_path = _FIXTURE_DIR / f"{name}.jsonl"
    exp_path = _EXPECTED_DIR / f"{name}.jsonl"
    lines = _load_jsonl(inp_path)
    expected_lines = _load_jsonl(exp_path)

    if len(lines) != len(expected_lines):
        return False, [
            f"line count mismatch: input {len(lines)} vs expected {len(expected_lines)}"
        ]

    decoder = FtcanDecoder()
    assembler: SegmentAssembler | None = None
    if name == "segmented_multi_measure":
        assembler = SegmentAssembler()

    errors: list[str] = []
    for i, (row, exp_row) in enumerate(zip(lines, expected_lines)):
        actual = _decode_line(decoder, assembler, row)
        exp_samples = exp_row.get("samples", [])
        line_errs = _compare_samples(actual, exp_samples)
        for e in line_errs:
            errors.append(f"line {i + 1}: {e}")

    return len(errors) == 0, errors


def main() -> int:
    all_ok = True
    for name in _FIXTURES:
        ok, errs = run_fixture(name)
        if ok:
            print(f"PASS  {name}")
        else:
            all_ok = False
            print(f"FAIL  {name}")
            for e in errs:
                print(f"       {e}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
