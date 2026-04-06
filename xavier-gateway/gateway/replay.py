"""Deterministic replay engine for raw FTCAN session logs.

Reads a raw session JSONL file, replays each frame through the canonical
decoder, and writes a normalized output JSONL. Replay is deterministic:
the same raw input always produces byte-identical normalized output,
because timestamps are derived from the source frames (not wall clock).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from gateway.decoder import GatewayDecoder

# Fixed epoch for deterministic wall timestamps (RFC3339 Z, matches gateway.timestamps style).
_WALL_EPOCH_UTC = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


def wall_rfc3339_from_ts_ms(ts_ms: int) -> str:
    """RFC3339 UTC string from offset milliseconds after 2026-01-01T00:00:00Z."""
    dt = _WALL_EPOCH_UTC + timedelta(milliseconds=ts_ms)
    return dt.isoformat().replace("+00:00", "Z")


def replay_session(
    raw_path: Path,
    output_path: Path,
    device_id: str = "gtm-ft600-bench",
    stream_id: str = "ftcan0",
    session_id: str | None = None,
) -> dict[str, int]:
    """Replay a raw session file through the canonical decoder.

    Returns stats dict: {frames_in, samples_out, errors}.

    DETERMINISM: Ordering and timestamps use each frame's ``ts_ms`` (and decoder
    state for segmentation). ``mono_ns = ts_ms * 1_000_000``. Wall time is
    epoch + ``ts_ms`` milliseconds. JSON lines use ``sort_keys=True`` and compact
    separators. No wall or monotonic clock reads during replay.
    """
    raw_path = Path(raw_path).resolve()
    output_path = Path(output_path).resolve()
    if session_id is None:
        session_id = f"replay_{raw_path.stem}"

    decoder = GatewayDecoder(device_id=device_id, stream_id=stream_id)

    stats: dict[str, int] = {"frames_in": 0, "samples_out": 0, "errors": 0}

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(raw_path, encoding="utf-8") as fin, open(
        output_path, "w", encoding="utf-8"
    ) as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            try:
                frame = json.loads(line)
            except json.JSONDecodeError:
                stats["errors"] += 1
                continue

            stats["frames_in"] += 1

            raw_ts = frame.get("ts_ms", 0)
            try:
                ts_ms = int(raw_ts)
            except (TypeError, ValueError):
                ts_ms = int(float(raw_ts))

            mono_ns_val = ts_ms * 1_000_000
            wall = wall_rfc3339_from_ts_ms(ts_ms)

            samples = decoder.decode_frame(frame, session_id, mono_ns_val, wall)

            for sample in samples:
                sample["provenance"]["mode"] = "replay"
                fout.write(
                    json.dumps(sample, separators=(",", ":"), sort_keys=True) + "\n"
                )
                stats["samples_out"] += 1

    return stats
