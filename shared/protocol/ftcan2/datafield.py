"""
Layer 3 — data field interpretation by DataFieldID (FTCAN 2.0).

Delegates segmented reassembly to `segmentation_reassembler` (same semantics
as `shared.protocol.ftcan.framing.segmentation`).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any

from shared.protocol.ftcan2.id_parser import FtcanEnvelopeHeader


class DataFieldMode(IntEnum):
    STANDARD_CAN = 0x00
    STANDARD_CAN_BRIDGE = 0x01
    FTCAN_2 = 0x02
    FTCAN_2_BRIDGE = 0x03


@dataclass(frozen=True, slots=True)
class DatafieldParseResult:
    mode: DataFieldMode
    """Raw CAN payload bytes (0..8) as received on the wire."""
    raw_bytes: bytes
    """True if DataFieldID is 0x02/0x03 and first byte is 0xFF (single-packet FTCAN body)."""
    is_single_packet_ftcan: bool
    """True if segmented FTCAN stream (first byte 0x00..0xFE)."""
    is_segment_stream: bool
    note: str


def classify_datafield_payload(header: FtcanEnvelopeHeader, data: bytes) -> DatafieldParseResult:
    """Structural classification only — no measure decode."""
    dlc = len(data)
    try:
        mode = DataFieldMode(header.data_field_id)
    except ValueError:
        return DatafieldParseResult(
            mode=DataFieldMode.STANDARD_CAN,
            raw_bytes=data,
            is_single_packet_ftcan=False,
            is_segment_stream=False,
            note=f"reserved_data_field_id_{header.data_field_id}",
        )
    if mode in (DataFieldMode.STANDARD_CAN, DataFieldMode.STANDARD_CAN_BRIDGE):
        return DatafieldParseResult(
            mode=mode,
            raw_bytes=data,
            is_single_packet_ftcan=False,
            is_segment_stream=False,
            note="standard_can_payload",
        )

    if dlc < 1:
        return DatafieldParseResult(
            mode=mode,
            raw_bytes=data,
            is_single_packet_ftcan=False,
            is_segment_stream=False,
            note="empty_datafield",
        )

    seg = data[0]
    if seg == 0xFF:
        return DatafieldParseResult(
            mode=mode,
            raw_bytes=data,
            is_single_packet_ftcan=True,
            is_segment_stream=False,
            note="ftcan_single_packet",
        )

    return DatafieldParseResult(
        mode=mode,
        raw_bytes=data,
        is_single_packet_ftcan=False,
        is_segment_stream=True,
        note="ftcan_segmented_stream",
    )


def datafield_to_jsonable(result: DatafieldParseResult) -> dict[str, Any]:
    return {
        "mode": result.mode.name,
        "mode_id": int(result.mode),
        "raw_hex": result.raw_bytes.hex(),
        "is_single_packet_ftcan": result.is_single_packet_ftcan,
        "is_segment_stream": result.is_segment_stream,
        "note": result.note,
    }
