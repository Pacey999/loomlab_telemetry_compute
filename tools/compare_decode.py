#!/usr/bin/env python3
"""Compare ESP32 full decoded output with Xavier canonical decoded output.

Reads two JSONL files (one from ESP32 full, one from Xavier/replay) and
compares them sample-by-sample.  Reports mismatches with details.

Usage:
    python tools/compare_decode.py esp32_decoded.jsonl xavier_decoded.jsonl
"""
import json
import math
import sys
from pathlib import Path


def load_samples(path: Path) -> list[dict]:
    """Load decoded samples from JSONL, keyed by (channel, seq/ts)."""
    samples = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                # Handle both ESP32 format {"type":"decoded","channel":...,"value":...}
                # and Xavier TelemetryFrame format {"channel":...,"value":...}
                if "channel" in obj:
                    samples.append(obj)
            except json.JSONDecodeError:
                continue
    return samples


def compare(esp32_path: Path, xavier_path: Path, tolerance: float = 1e-6) -> dict:
    """Compare two decoded output files.

    Returns: {
        "total_esp32": N, "total_xavier": N,
        "matched": N, "mismatched": N, "esp32_only": N, "xavier_only": N,
        "mismatches": [{"channel": ..., "esp32_value": ..., "xavier_value": ..., "diff": ...}]
    }
    """
    esp32_samples = load_samples(esp32_path)
    xavier_samples = load_samples(xavier_path)

    # Group by (channel, sequence position)
    # Since samples are in order, compare positionally within each channel
    esp32_by_channel: dict[str, list[dict]] = {}
    xavier_by_channel: dict[str, list[dict]] = {}

    for s in esp32_samples:
        ch = s.get("channel", "?")
        esp32_by_channel.setdefault(ch, []).append(s)

    for s in xavier_samples:
        ch = s.get("channel", "?")
        xavier_by_channel.setdefault(ch, []).append(s)

    all_channels = set(esp32_by_channel.keys()) | set(xavier_by_channel.keys())

    result = {
        "total_esp32": len(esp32_samples),
        "total_xavier": len(xavier_samples),
        "matched": 0,
        "mismatched": 0,
        "esp32_only_channels": [],
        "xavier_only_channels": [],
        "mismatches": [],
    }

    for ch in sorted(all_channels):
        e_list = esp32_by_channel.get(ch, [])
        x_list = xavier_by_channel.get(ch, [])

        if not e_list:
            result["xavier_only_channels"].append(ch)
            continue
        if not x_list:
            result["esp32_only_channels"].append(ch)
            continue

        # Compare pairwise up to the shorter list
        for i in range(min(len(e_list), len(x_list))):
            e_val = e_list[i].get("value", 0)
            x_val = x_list[i].get("value", 0)

            if math.isclose(e_val, x_val, abs_tol=tolerance):
                result["matched"] += 1
            else:
                result["mismatched"] += 1
                result["mismatches"].append({
                    "channel": ch,
                    "index": i,
                    "esp32_value": e_val,
                    "xavier_value": x_val,
                    "diff": abs(e_val - x_val),
                })

    return result


def main():
    if len(sys.argv) < 3:
        print("Usage: compare_decode.py <esp32_decoded.jsonl> <xavier_decoded.jsonl>")
        sys.exit(1)

    esp32_path = Path(sys.argv[1])
    xavier_path = Path(sys.argv[2])

    result = compare(esp32_path, xavier_path)

    print(f"ESP32 samples:  {result['total_esp32']}")
    print(f"Xavier samples: {result['total_xavier']}")
    print(f"Matched:        {result['matched']}")
    print(f"Mismatched:     {result['mismatched']}")

    if result["esp32_only_channels"]:
        print(f"ESP32-only channels: {result['esp32_only_channels']}")
    if result["xavier_only_channels"]:
        print(f"Xavier-only channels: {result['xavier_only_channels']}")

    if result["mismatches"]:
        print("\nMismatches:")
        for m in result["mismatches"][:20]:
            print(f"  {m['channel']}[{m['index']}]: esp32={m['esp32_value']} xavier={m['xavier_value']} diff={m['diff']}")

    if result["mismatched"] == 0:
        print("\nRESULT: PASS — zero mismatches")
        sys.exit(0)
    else:
        print(f"\nRESULT: FAIL — {result['mismatched']} mismatches")
        sys.exit(1)


if __name__ == "__main__":
    main()
