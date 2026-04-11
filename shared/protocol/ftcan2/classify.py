"""Decode / classification depth for every frame (unknown ≠ dropped)."""

from __future__ import annotations

from enum import IntEnum


class DecodeStage(IntEnum):
    RAW_ONLY = 0
    HEADER_PARSED = 1
    PAYLOAD_PARSED = 2
    SEMANTICALLY_DECODED = 3
