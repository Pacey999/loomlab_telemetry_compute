"""
FTCAN 2.0 — raw value scaling and normalization.

Takes a signed 16-bit decoded value and a scale factor from the registry
and produces the engineering-unit float.
"""

from __future__ import annotations


def apply_scaling(raw_signed: int, scale: float) -> float:
    """Convert raw signed integer to engineering units using registry scale."""
    return raw_signed * scale


def clamp_to_range(value: float, valid_range: list[float] | None) -> tuple[float, bool]:
    """Return (clamped_value, in_range).  If valid_range is None, always in range."""
    if valid_range is None or len(valid_range) < 2:
        return value, True
    lo, hi = valid_range[0], valid_range[1]
    return value, lo <= value <= hi
