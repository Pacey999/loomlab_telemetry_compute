#!/usr/bin/env python3
"""Plausibility checker for decoded telemetry samples.

Validates that decoded values fall within engineering-reasonable ranges
as defined in the canonical measure registry.

Usage:
    python tools/plausibility_check.py <decoded_output.jsonl>
"""
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

REGISTRY_PATH = _ROOT / "shared" / "protocol" / "ftcan" / "registry" / "measure-registry.json"


def load_valid_ranges() -> dict[str, dict]:
    """Load validRange entries from the registry, keyed by channel."""
    with open(REGISTRY_PATH) as f:
        reg = json.load(f)

    ranges = {}
    for m in reg["measures"]:
        vr = m.get("validRange")
        if vr and len(vr) >= 2:
            ranges[m["channel"]] = {
                "min": vr[0], "max": vr[1],
                "unit": m.get("unit", "-"),
                "label": m.get("label", m["channel"]),
            }
    return ranges


def check_plausibility(decoded_path: Path) -> dict:
    """Check all samples in a decoded JSONL against registry ranges.

    Returns: {
        "total_samples": N,
        "checked": N,  (samples with a validRange defined)
        "in_range": N,
        "out_of_range": N,
        "violations": [{channel, value, min, max}],
        "unchecked_channels": [channels with no validRange]
    }
    """
    ranges = load_valid_ranges()

    result = {
        "total_samples": 0,
        "checked": 0,
        "in_range": 0,
        "out_of_range": 0,
        "violations": [],
        "unchecked_channels": set(),
    }

    with open(decoded_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                sample = json.loads(line)
            except json.JSONDecodeError:
                continue

            result["total_samples"] += 1
            channel = sample.get("channel", "")
            value = sample.get("value", 0)

            if channel in ranges:
                result["checked"] += 1
                r = ranges[channel]
                if r["min"] <= value <= r["max"]:
                    result["in_range"] += 1
                else:
                    result["out_of_range"] += 1
                    result["violations"].append({
                        "channel": channel,
                        "value": value,
                        "min": r["min"],
                        "max": r["max"],
                        "unit": r["unit"],
                    })
            else:
                result["unchecked_channels"].add(channel)

    result["unchecked_channels"] = sorted(result["unchecked_channels"])
    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: plausibility_check.py <decoded_output.jsonl>")
        sys.exit(1)

    path = Path(sys.argv[1])
    result = check_plausibility(path)

    print(f"Total samples:  {result['total_samples']}")
    print(f"Checked:        {result['checked']}")
    print(f"In range:       {result['in_range']}")
    print(f"Out of range:   {result['out_of_range']}")

    if result["violations"]:
        print("\nViolations:")
        for v in result["violations"][:20]:
            print(f"  {v['channel']}: {v['value']} {v['unit']} (range: {v['min']}..{v['max']})")

    if result["unchecked_channels"]:
        print(f"\nUnchecked channels (no validRange): {result['unchecked_channels']}")

    if result["out_of_range"] == 0:
        print("\nRESULT: PASS — all checked values in range")
        sys.exit(0)
    else:
        print(f"\nRESULT: WARN — {result['out_of_range']} out-of-range values")
        sys.exit(1)


if __name__ == "__main__":
    main()
