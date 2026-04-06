"""
FTCAN 2.0 — value vs status classification and quality flags.

MeasureID bit 0:
  0 → data value  (signed 16-bit)
  1 → data status (unsigned 16-bit)

Status word indicates the *quality* of the companion value channel
(measureId - 1).
"""

from __future__ import annotations

import struct
from enum import Enum


class QualityFlag(str, Enum):
    GOOD = "good"
    STALE = "stale"
    UNKNOWN = "unknown"
    ERROR = "error"


def is_status_id(measure_id: int) -> bool:
    return (measure_id & 1) == 1


def is_value_id(measure_id: int) -> bool:
    return (measure_id & 1) == 0


def companion_value_id(status_id: int) -> int:
    """Given a status MeasureID, return the corresponding value MeasureID."""
    return status_id & ~1


def companion_status_id(value_id: int) -> int:
    """Given a value MeasureID, return the corresponding status MeasureID."""
    return value_id | 1


def decode_value(raw_u16: int) -> int:
    """Interpret raw 16-bit word as signed value (big-endian already parsed)."""
    return struct.unpack(">h", struct.pack(">H", raw_u16 & 0xFFFF))[0]


def decode_status(raw_u16: int) -> int:
    """Interpret raw 16-bit word as unsigned status."""
    return raw_u16 & 0xFFFF


def classify_measure(measure_id: int, raw_word: int) -> tuple[bool, int]:
    """Return (is_value, decoded_word).

    If is_value is True, decoded_word is signed.
    If is_value is False, decoded_word is the unsigned status.
    """
    if is_value_id(measure_id):
        return True, decode_value(raw_word)
    return False, decode_status(raw_word)
