"""Stateful FTCAN 2.0 segmented reassembly — thin wrapper over SSOT implementation."""

from shared.protocol.ftcan.framing.segmentation import (
    MAX_PAYLOAD,
    SINGLE_PACKET_MARKER,
    SegmentAssembler,
)

__all__ = ["MAX_PAYLOAD", "SINGLE_PACKET_MARKER", "SegmentAssembler"]
