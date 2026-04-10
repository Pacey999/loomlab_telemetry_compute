#!/usr/bin/env python3
"""
Generate C++ constexpr tables from the canonical FTCAN measure registry.

Output: a header file with MeasureEntry structs and simplified-packet slot
tables consumable by ESP32 firmware.

Usage:
    python3 shared/protocol/ftcan/generators/gen_cpp.py [--out esp32-mini-debug/src/ftcan_registry.h]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REGISTRY_PATH = Path(__file__).resolve().parent.parent / "registry" / "measure-registry.json"


def _escape_cpp_str(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')

HEADER_TEMPLATE = '''\
#pragma once
// AUTO-GENERATED from measure-registry.json — do not edit by hand.
// Regenerate: python3 shared/protocol/ftcan/generators/gen_cpp.py --out esp32-mini-debug/src/ftcan_registry.h

#include <cstdint>

struct MeasureEntry {{
    uint16_t measure_id;
    const char* channel;
    const char* unit;
    float scale;
    bool is_signed;
}};

static constexpr MeasureEntry FTCAN_MEASURES[] = {{
{measure_entries}
}};

static constexpr uint16_t FTCAN_MEASURES_COUNT = {measure_count};

// Simplified packet slot: maps (message_id, slot_position) -> measure_id
struct SimplifiedSlot {{
    uint16_t message_id;
    uint8_t  position;
    uint16_t measure_id;
    const char* channel;
}};

static constexpr SimplifiedSlot FTCAN_SIMPLIFIED_SLOTS[] = {{
{simplified_entries}
}};

static constexpr uint16_t FTCAN_SIMPLIFIED_SLOTS_COUNT = {simplified_count};

// Lookup helpers
inline const MeasureEntry* ftcan_find_measure(uint16_t measure_id) {{
    for (uint16_t i = 0; i < FTCAN_MEASURES_COUNT; i++) {{
        if (FTCAN_MEASURES[i].measure_id == measure_id) return &FTCAN_MEASURES[i];
    }}
    return nullptr;
}}
'''


def generate(registry_path: Path, output_path: Path) -> None:
    with open(registry_path) as f:
        reg = json.load(f)

    by_id: dict[int, dict] = {}
    for m in reg["measures"]:
        by_id[int(m["measureId"])] = m
    base_ids = set(by_id.keys())

    measure_lines: list[str] = []
    seen_ids: set[int] = set()
    for mid in sorted(by_id.keys()):
        m = by_id[mid]
        ch = _escape_cpp_str(m["channel"])
        unit = _escape_cpp_str(str(m.get("unit", "-")))
        scale = float(m.get("scale", 1))
        signed = "true" if m.get("signed", True) else "false"
        measure_lines.append(
            f'    {{0x{mid:04X}, "{ch}", "{unit}", {scale}f, {signed}}},'
        )
        seen_ids.add(mid)
        # Mirror Python FtcanDecoder: companion status row (odd id) shares channel/unit; skip if odd id exists in JSON.
        sid = mid | 1
        if sid != mid and sid not in base_ids and sid not in seen_ids:
            measure_lines.append(
                f'    {{0x{sid:04X}, "{ch}", "{unit}", 1.0f, false}},'
            )
            seen_ids.add(sid)

    simplified_lines: list[str] = []
    for msg_str, pkt in reg.get("simplifiedPackets", {}).items():
        msg_id = int(msg_str, 16)
        for slot in pkt["slots"]:
            pos = slot["position"]
            mid = slot.get("measureId", 0)
            ch = _escape_cpp_str(slot["channel"])
            simplified_lines.append(
                f'    {{0x{msg_id:03X}, {pos}, 0x{mid:04X}, "{ch}"}},'
            )

    header = HEADER_TEMPLATE.format(
        measure_entries="\n".join(measure_lines),
        measure_count=len(measure_lines),
        simplified_entries="\n".join(simplified_lines),
        simplified_count=len(simplified_lines),
    )

    output_path.write_text(header)
    print(f"Generated {output_path}  ({len(measure_lines)} measures, {len(simplified_lines)} simplified slots)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate C++ FTCAN registry header")
    parser.add_argument("--out", type=Path, default=Path("ftcan_registry.h"))
    args = parser.parse_args()
    generate(REGISTRY_PATH, args.out)


if __name__ == "__main__":
    main()
