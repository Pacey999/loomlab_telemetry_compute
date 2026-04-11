"""
Layers 1–3 wiring: raw frame → header → datafield classification.

Layer 4+ (message family + measure decode) plug in later via registry-driven
decoders — not hard-coded FT600 gates.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shared.protocol.ftcan2.classify import DecodeStage
from shared.protocol.ftcan2.datafield import classify_datafield_payload, datafield_to_jsonable
from shared.protocol.ftcan2.id_parser import FtcanEnvelopeHeader, parse_envelope_header
from shared.protocol.ftcan2.model import RawCanFrame


@dataclass(frozen=True, slots=True)
class PipelineResult:
    stage: DecodeStage
    header: dict[str, Any]
    datafield: dict[str, Any] | None
    error: str | None = None


def header_to_jsonable(header: FtcanEnvelopeHeader) -> dict[str, Any]:
    return {
        "id29": f"0x{header.raw:08X}",
        "product_id": f"0x{header.product_id:04X}",
        "product_type_id": f"0x{header.product_type_id:03X}",
        "unique_id": f"0x{header.unique_id:02X}",
        "data_field_id": header.data_field_id,
        "message_id": f"0x{header.message_id:03X}",
        "is_response": header.is_response,
        "likely_ft600_ecu": header.likely_ft600_ecu(),
    }


class FtcanPipeline:
    """Host-side processor; replay and tools use this."""

    def process(self, frame: RawCanFrame) -> PipelineResult:
        if not frame.is_extended:
            return PipelineResult(
                stage=DecodeStage.RAW_ONLY,
                header={},
                datafield=None,
                error="not_extended",
            )

        try:
            env = parse_envelope_header(frame.id29)
        except ValueError as e:
            return PipelineResult(
                stage=DecodeStage.RAW_ONLY,
                header={},
                datafield=None,
                error=str(e),
            )

        h = header_to_jsonable(env)
        df = classify_datafield_payload(env, frame.data[: frame.dlc])
        return PipelineResult(
            stage=DecodeStage.PAYLOAD_PARSED,
            header=h,
            datafield=datafield_to_jsonable(df),
            error=None,
        )
