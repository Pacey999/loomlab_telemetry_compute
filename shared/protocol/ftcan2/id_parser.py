"""
FTCAN 2.0 — 29-bit extended CAN identifier → envelope header.

Parses **every** valid id29; no product-band gate. Optional helpers
(`likely_ft600_ecu`, etc.) are hints only — never used to drop traffic.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FtcanEnvelopeHeader:
    raw: int
    product_id: int
    product_type_id: int
    unique_id: int
    data_field_id: int
    message_id: int
    is_response: bool

    def likely_ft600_ecu(self) -> bool:
        """True if ProductID falls in documented FT600 ECU range (hint only)."""
        return 0x5020 <= self.product_id <= 0x503F


def parse_envelope_header(id29: int, *, is_response: bool | None = None) -> FtcanEnvelopeHeader:
    """Decompose 29-bit extended ID per FTCAN 2.0 bit layout.

    `is_response` is not derivable from the public ID layout in all FuelTech
    docs; pass it when known from transport context, else defaults False.
    """
    if not (0 <= id29 <= 0x1FFFFFFF):
        raise ValueError(f"ID out of 29-bit range: 0x{id29:08X}")

    product_id = (id29 >> 14) & 0x7FFF
    data_field_id = (id29 >> 11) & 0x07
    message_id = id29 & 0x7FF
    product_type_id = (product_id >> 5) & 0x3FF
    unique_id = product_id & 0x1F

    return FtcanEnvelopeHeader(
        raw=id29,
        product_id=product_id,
        product_type_id=product_type_id,
        unique_id=unique_id,
        data_field_id=data_field_id,
        message_id=message_id,
        is_response=bool(is_response) if is_response is not None else False,
    )


def build_can_id(product_id: int, data_field_id: int, message_id: int) -> int:
    """Construct a 29-bit CAN ID from components (fixtures / tests)."""
    return ((product_id & 0x7FFF) << 14) | ((data_field_id & 0x07) << 11) | (message_id & 0x7FF)
