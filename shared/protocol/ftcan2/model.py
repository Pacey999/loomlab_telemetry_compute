"""Layer-1 ingress model (host-side; firmware mirrors structurally)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RawCanFrame:
    """CAN 2.0B extended frame at 1 Mbps (logical view)."""

    ts_ms: int
    id29: int
    dlc: int
    data: bytes
    is_extended: bool = True

    def __post_init__(self) -> None:
        if self.dlc < 0 or self.dlc > 8:
            raise ValueError("dlc must be 0..8")
        if len(self.data) > 8:
            raise ValueError("data length must be <= 8")
        if not self.is_extended:
            raise ValueError("FTCAN 2.0 requires extended IDs")
