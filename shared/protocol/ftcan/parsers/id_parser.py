"""
FTCAN 2.0 — 29-bit CAN identifier decomposition.

Bit layout (per FTCAN 2.0 spec):
  bits 28..14  ProductID   (15 bits)
  bits 13..11  DataFieldID ( 3 bits)
  bits 10.. 0  MessageID   (11 bits)

ProductID is further split:
  bits 14..5   ProductTypeID (10 bits)
  bits  4..0   UniqueID      ( 5 bits)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FtcanId:
    raw: int
    product_id: int
    product_type_id: int
    unique_id: int
    data_field_id: int
    message_id: int

    @property
    def is_ft600(self) -> bool:
        return 0x5020 <= self.product_id <= 0x503F

    @property
    def is_ft500(self) -> bool:
        return 0x5000 <= self.product_id <= 0x501F

    @property
    def is_realtime_tuple(self) -> bool:
        return self.message_id in _REALTIME_TUPLE_MSG_IDS

    @property
    def is_simplified(self) -> bool:
        return 0x600 <= self.message_id <= 0x608

    @property
    def is_segmented(self) -> bool:
        return self.data_field_id in (0x02, 0x03)

    @property
    def is_standard(self) -> bool:
        return self.data_field_id in (0x00, 0x01)

    @property
    def priority_label(self) -> str:
        if self.product_id <= 0x1FFF:
            return "critical"
        if self.product_id <= 0x3FFF:
            return "high"
        if self.product_id <= 0x5FFF:
            return "medium"
        return "low"


_REALTIME_TUPLE_MSG_IDS = frozenset({0x0FF, 0x1FF, 0x2FF, 0x3FF})


def parse_can_id(id29: int) -> FtcanId:
    """Decompose a 29-bit extended CAN identifier into FTCAN fields."""
    if not (0 <= id29 <= 0x1FFFFFFF):
        raise ValueError(f"ID out of 29-bit range: 0x{id29:08X}")

    product_id = (id29 >> 14) & 0x7FFF
    data_field_id = (id29 >> 11) & 0x07
    message_id = id29 & 0x7FF

    product_type_id = (product_id >> 5) & 0x3FF
    unique_id = product_id & 0x1F

    return FtcanId(
        raw=id29,
        product_id=product_id,
        product_type_id=product_type_id,
        unique_id=unique_id,
        data_field_id=data_field_id,
        message_id=message_id,
    )


def build_can_id(product_id: int, data_field_id: int, message_id: int) -> int:
    """Construct a 29-bit CAN ID from components (useful for fixtures)."""
    return ((product_id & 0x7FFF) << 14) | ((data_field_id & 0x07) << 11) | (message_id & 0x7FF)
