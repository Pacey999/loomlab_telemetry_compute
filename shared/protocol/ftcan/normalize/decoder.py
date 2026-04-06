"""
FTCAN 2.0 — canonical frame decoder.

Handles two broadcast styles:
  1. Realtime tuple (MessageID 0x0FF / 0x1FF / 0x2FF / 0x3FF):
     payload is N × 4-byte tuples of (MeasureID u16, Value/Status u16).
  2. Simplified broadcast (MessageID 0x600..0x608):
     payload is 4 × signed-16 values at fixed slot positions.

Both emit the same DecodedSample output.
"""

from __future__ import annotations

import json
import struct
from dataclasses import dataclass, field
from pathlib import Path

from shared.protocol.ftcan.parsers.id_parser import FtcanId
from shared.protocol.ftcan.quality.quality import (
    classify_measure,
    is_status_id,
    companion_value_id,
)
from shared.protocol.ftcan.normalize.normalize import apply_scaling, clamp_to_range

_REGISTRY_PATH = Path(__file__).resolve().parent.parent / "registry" / "measure-registry.json"

_REALTIME_TUPLE_MSG_IDS = frozenset({0x0FF, 0x1FF, 0x2FF, 0x3FF})


@dataclass(frozen=True, slots=True)
class DecodedSample:
    channel: str
    value: float
    unit: str
    quality: str
    measure_id: int
    is_status: bool
    raw_word: int


@dataclass
class FtcanDecoder:
    """Stateless decoder driven by the canonical measure registry."""

    _measures_by_id: dict[int, dict] = field(default_factory=dict, repr=False)
    _simplified: dict[int, list[dict]] = field(default_factory=dict, repr=False)
    _fallback_measures: dict[str, dict] = field(default_factory=dict, repr=False)

    unknown_ids: int = 0

    def __post_init__(self) -> None:
        self._load_registry()

    def _load_registry(self) -> None:
        with open(_REGISTRY_PATH) as f:
            reg = json.load(f)

        for m in reg["measures"]:
            self._measures_by_id[m["measureId"]] = m
            status_id = m["measureId"] | 1
            if status_id != m["measureId"]:
                self._measures_by_id[status_id] = {
                    **m,
                    "measureId": status_id,
                    "_is_status_entry": True,
                }

        for msg_id_str, pkt in reg.get("simplifiedPackets", {}).items():
            msg_id = int(msg_id_str, 16)
            self._simplified[msg_id] = pkt["slots"]

    def decode_tuple_payload(self, payload: bytes, ftcan_id: FtcanId) -> list[DecodedSample]:
        """Decode a realtime tuple payload (one or more 4-byte measure+value pairs)."""
        samples: list[DecodedSample] = []
        offset = 0
        while offset + 4 <= len(payload):
            measure_id = struct.unpack_from(">H", payload, offset)[0]
            raw_word = struct.unpack_from(">H", payload, offset + 2)[0]
            offset += 4

            sample = self._decode_measure(measure_id, raw_word)
            if sample is not None:
                samples.append(sample)
        return samples

    def decode_simplified_payload(self, data: bytes, ftcan_id: FtcanId) -> list[DecodedSample]:
        """Decode a simplified broadcast payload (4 × 16-bit values at fixed slots)."""
        msg_id = ftcan_id.message_id
        slots = self._simplified.get(msg_id)
        if slots is None:
            self.unknown_ids += 1
            return []

        samples: list[DecodedSample] = []
        for slot in slots:
            pos = slot["position"]
            byte_offset = pos * 2
            if byte_offset + 2 > len(data):
                break
            raw_word = struct.unpack_from(">H", data, byte_offset)[0]
            mid = slot.get("measureId")
            if mid is not None:
                sample = self._decode_measure(mid, raw_word)
            else:
                sample = self._decode_by_channel(slot["channel"], raw_word)

            if sample is not None:
                samples.append(sample)
        return samples

    def decode_frame(self, ftcan_id: FtcanId, payload: bytes) -> list[DecodedSample]:
        """Top-level decode dispatch for a single frame's payload."""
        if ftcan_id.is_realtime_tuple:
            return self.decode_tuple_payload(payload, ftcan_id)
        if ftcan_id.is_simplified:
            return self.decode_simplified_payload(payload, ftcan_id)
        return []

    def _decode_measure(self, measure_id: int, raw_word: int) -> DecodedSample | None:
        is_value, decoded = classify_measure(measure_id, raw_word)
        meta = self._measures_by_id.get(measure_id)

        if meta is None:
            lookup_id = companion_value_id(measure_id) if is_status_id(measure_id) else measure_id
            meta = self._measures_by_id.get(lookup_id)

        if meta is None:
            self.unknown_ids += 1
            return DecodedSample(
                channel=f"unknown.0x{measure_id:04X}",
                value=float(decoded),
                unit="-",
                quality="unknown",
                measure_id=measure_id,
                is_status=not is_value,
                raw_word=raw_word,
            )

        if is_value:
            scaled = apply_scaling(decoded, meta.get("scale", 1))
            vr = meta.get("validRange")
            _, in_range = clamp_to_range(scaled, vr)
            quality = "good" if in_range else "suspect"
        else:
            scaled = float(decoded)
            quality = "status"

        return DecodedSample(
            channel=meta["channel"],
            value=scaled,
            unit=meta.get("unit", "-"),
            quality=quality,
            measure_id=measure_id,
            is_status=not is_value,
            raw_word=raw_word,
        )

    def _decode_by_channel(self, channel: str, raw_word: int) -> DecodedSample | None:
        """Fallback for simplified slots that only specify a channel name (no measureId)."""
        is_value, decoded = classify_measure(0, raw_word)
        return DecodedSample(
            channel=channel,
            value=apply_scaling(decoded, 1),
            unit="-",
            quality="good",
            measure_id=0,
            is_status=False,
            raw_word=raw_word,
        )
