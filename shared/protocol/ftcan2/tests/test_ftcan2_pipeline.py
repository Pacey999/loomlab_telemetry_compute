"""Unit tests for FTCAN 2.0 gateway core (no hardware)."""

from __future__ import annotations

import unittest

from shared.protocol.ftcan2.classify import DecodeStage
from shared.protocol.ftcan2.id_parser import build_can_id, parse_envelope_header
from shared.protocol.ftcan2.model import RawCanFrame
from shared.protocol.ftcan2.pipeline import FtcanPipeline
from shared.protocol.ftcan2.segmentation_reassembler import SINGLE_PACKET_MARKER, SegmentAssembler


class TestIdParser(unittest.TestCase):
    def test_parse_roundtrip(self) -> None:
        pid, df, mid = 0x5021, 0, 0x2EA
        id29 = build_can_id(pid, df, mid)
        h = parse_envelope_header(id29)
        self.assertEqual(h.product_id, pid)
        self.assertEqual(h.data_field_id, df)
        self.assertEqual(h.message_id, mid)
        self.assertTrue(h.likely_ft600_ecu())

    def test_non_ft600_still_parsed(self) -> None:
        h = parse_envelope_header(0x03FFC2FE)
        self.assertFalse(h.likely_ft600_ecu())
        self.assertEqual(h.product_id, 0xFFF)


class TestPipeline(unittest.TestCase):
    def test_pipeline_payload_parsed(self) -> None:
        p = FtcanPipeline()
        fr = RawCanFrame(ts_ms=0, id29=0x140842EA, dlc=2, data=bytes([80, 32]))
        r = p.process(fr)
        self.assertEqual(r.stage, DecodeStage.PAYLOAD_PARSED)
        self.assertIsNone(r.error)
        self.assertIn("product_id", r.header)
        self.assertEqual(r.header["data_field_id"], 0)
        self.assertIsNotNone(r.datafield)


class TestSegmentation(unittest.TestCase):
    def test_single_packet_ff(self) -> None:
        asm = SegmentAssembler()
        out = asm.feed(bytes([SINGLE_PACKET_MARKER, 1, 2, 3, 4, 5, 6, 7]))
        self.assertEqual(out, bytes([1, 2, 3, 4, 5, 6, 7]))


if __name__ == "__main__":
    unittest.main()
