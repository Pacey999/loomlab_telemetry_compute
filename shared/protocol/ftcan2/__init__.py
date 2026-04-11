"""
FTCAN 2.0 gateway core — generic ID/datafield pipeline (no FT600 product-band gate).

Host/replay and future firmware codegen should import from here, not from
narrow mini-debug paths.
"""

from shared.protocol.ftcan2.classify import DecodeStage
from shared.protocol.ftcan2.id_parser import FtcanEnvelopeHeader, parse_envelope_header
from shared.protocol.ftcan2.model import RawCanFrame
from shared.protocol.ftcan2.pipeline import FtcanPipeline

__all__ = [
    "DecodeStage",
    "FtcanEnvelopeHeader",
    "RawCanFrame",
    "FtcanPipeline",
    "parse_envelope_header",
]
