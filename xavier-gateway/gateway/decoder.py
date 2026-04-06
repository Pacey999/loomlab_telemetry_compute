"""Canonical FTCAN decoder for the Xavier gateway.

Imports shared protocol truth — no duplicate decode logic here.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure shared protocol is importable
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from shared.protocol.ftcan.framing.segmentation import SegmentAssembler
from shared.protocol.ftcan.normalize.decoder import FtcanDecoder
from shared.protocol.ftcan.parsers.id_parser import parse_can_id


class GatewayDecoder:
    """Wraps the shared FtcanDecoder with segmentation support and
    conversion to TelemetryFrame dicts."""

    def __init__(self, device_id: str = "gtm-ft600-bench", stream_id: str = "ftcan0") -> None:
        self.ftcan = FtcanDecoder()
        self.device_id = device_id
        self.stream_id = stream_id
        # Keyed by (product_id, message_id) for segmented streams
        self._assemblers: dict[tuple[int, int], SegmentAssembler] = {}

    def decode_frame(
        self,
        frame: dict,
        session_id: str,
        mono_ns: int,
        wall_rfc3339: str,
    ) -> list[dict]:
        """Decode a raw frame dict into normalized TelemetryFrame dicts.

        frame format: {"id29": "0x...", "dlc": N, "data": [...], "ts_ms": N, "seq": N}
        Returns list of TelemetryFrame dicts.
        """
        id29_str = frame.get("id29", "0x0")
        id29 = int(id29_str, 16) if isinstance(id29_str, str) else int(id29_str)
        data = bytes(frame.get("data", []))
        seq = frame.get("seq", 0)

        ftcan_id = parse_can_id(id29)

        # Handle segmented frames
        if ftcan_id.is_segmented:
            key = (ftcan_id.product_id, ftcan_id.message_id)
            if key not in self._assemblers:
                self._assemblers[key] = SegmentAssembler()
            payload = self._assemblers[key].feed(data)
            if payload is None:
                return []
            samples = self.ftcan.decode_tuple_payload(payload, ftcan_id)
        else:
            samples = self.ftcan.decode_frame(ftcan_id, data)

        # Convert to TelemetryFrame format
        frames: list[dict] = []
        for s in samples:
            frames.append(
                {
                    "ts_mono_ns": mono_ns,
                    "ts_wall_rfc3339": wall_rfc3339,
                    "device_id": self.device_id,
                    "stream_id": self.stream_id,
                    "session_id": session_id,
                    "channel": s.channel,
                    "value": s.value,
                    "unit": s.unit,
                    "quality": s.quality,
                    "status_u16": s.raw_word if s.is_status else 0,
                    "provenance": {
                        "mode": "live",
                        "protocol": "ftcan",
                        "product_id": ftcan_id.product_id,
                        "message_id": ftcan_id.message_id,
                        "measure_id": s.measure_id,
                        "source_seq": seq,
                    },
                }
            )
        return frames
