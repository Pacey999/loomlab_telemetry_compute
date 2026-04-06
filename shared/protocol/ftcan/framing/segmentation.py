"""
FTCAN 2.0 segmented packet reassembly.

DataFieldID 0x02 / 0x03 use the first byte of the DATA FIELD as a segment
index.  0xFF means "single packet" (7-byte payload).  0x00..0xFE identify
ordered segments, with segment 0 carrying 2 bytes of segmentation metadata
(total payload length) followed by 5 bytes of payload.  Continuation
segments carry 7 bytes each.

Max payload: 5 + (0xFD * 7) = 1776 bytes.

Per the FTCAN flowchart: discard on unexpected sequence, re-start on new
segment-0 if one arrives mid-stream.
"""

from __future__ import annotations

from dataclasses import dataclass, field

SINGLE_PACKET_MARKER = 0xFF
MAX_PAYLOAD = 1776
PAYLOAD_LENGTH_MASK = 0x07FF


@dataclass
class SegmentAssembler:
    """Stateful reassembler for one (product_id, message_id) stream."""

    _expected_index: int = 0
    _total_length: int = 0
    _buffer: bytearray = field(default_factory=bytearray)
    _active: bool = False

    # counters
    completed: int = 0
    discarded: int = 0

    def feed(self, data: bytes) -> bytes | None:
        """Feed one CAN frame's data field (up to 8 bytes).

        Returns the reassembled payload when complete, or None if
        accumulating / discarding.
        """
        if len(data) < 1:
            return None

        seg_index = data[0]

        if seg_index == SINGLE_PACKET_MARKER:
            self._reset()
            self.completed += 1
            return bytes(data[1:])

        if seg_index == 0x00:
            self._start_new(data)
            return self._check_complete()

        if not self._active or seg_index != self._expected_index:
            self._discard()
            return None

        self._buffer.extend(data[1:])
        self._expected_index = seg_index + 1
        return self._check_complete()

    def _start_new(self, data: bytes) -> None:
        if len(data) < 3:
            self._discard()
            return
        seg_meta = (data[1] << 8) | data[2]
        self._total_length = seg_meta & PAYLOAD_LENGTH_MASK
        if self._total_length == 0 or self._total_length > MAX_PAYLOAD:
            self._discard()
            return
        self._buffer = bytearray(data[3:])
        self._expected_index = 1
        self._active = True

    def _check_complete(self) -> bytes | None:
        if len(self._buffer) >= self._total_length:
            payload = bytes(self._buffer[: self._total_length])
            self._reset()
            self.completed += 1
            return payload
        return None

    def _discard(self) -> None:
        self.discarded += 1
        self._reset()

    def _reset(self) -> None:
        self._expected_index = 0
        self._total_length = 0
        self._buffer = bytearray()
        self._active = False
