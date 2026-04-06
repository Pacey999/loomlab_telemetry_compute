"""Serial and file JSONL ingest (no protocol decode)."""
from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, AsyncIterator, TextIO

from gateway.timestamps import timestamp_pair

logger = logging.getLogger(__name__)


def _attach_gateway_ts(frame: dict[str, Any]) -> dict[str, Any]:
    mono, wall = timestamp_pair()
    return {
        **frame,
        "gateway_mono_ns": mono,
        "gateway_wall": wall,
    }


def _parse_line(line: str) -> dict[str, Any] | None:
    s = line.strip()
    if not s:
        return None
    try:
        obj = json.loads(s)
    except json.JSONDecodeError as e:
        logger.warning("JSON decode error: %s", e)
        return None
    if not isinstance(obj, dict):
        logger.warning("Expected JSON object per line, got %s", type(obj).__name__)
        return None
    return obj


class SerialIngest:
    """Read JSONL lines from a serial port (ESP32 telemetry)."""

    def __init__(self, port: str, baudrate: int = 115200) -> None:
        self.port = port
        self.baudrate = baudrate
        self._ser: Any = None

    def _open(self) -> None:
        import serial

        self._ser = serial.Serial(self.port, self.baudrate, timeout=0.5)

    def _close(self) -> None:
        if self._ser is not None and getattr(self._ser, "is_open", False):
            self._ser.close()
        self._ser = None

    def _readline_blocking(self) -> bytes | None:
        if self._ser is None:
            return None
        try:
            return self._ser.readline()
        except Exception as e:
            logger.error("Serial read error: %s", e)
            return b""

    async def frames(self) -> AsyncIterator[dict[str, Any]]:
        loop = asyncio.get_running_loop()
        try:
            self._open()
            while True:
                raw = await loop.run_in_executor(None, self._readline_blocking)
                if raw is None:
                    break
                if raw == b"":
                    await asyncio.sleep(0)
                    continue
                try:
                    text = raw.decode("utf-8", errors="replace")
                except Exception as e:
                    logger.error("Decode error: %s", e)
                    continue
                parsed = _parse_line(text)
                if parsed is None:
                    continue
                yield _attach_gateway_ts(parsed)
        finally:
            self._close()


class FileIngest:
    """Replay JSONL from a file (same logical frame shape as serial)."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def _readline_blocking(self, fp: TextIO) -> str | None:
        line = fp.readline()
        if line == "":
            return None
        return line

    async def frames(self) -> AsyncIterator[dict[str, Any]]:
        loop = asyncio.get_running_loop()

        def _open():
            return open(self.path, "r", encoding="utf-8")

        fp = await loop.run_in_executor(None, _open)
        try:
            while True:
                line = await loop.run_in_executor(None, self._readline_blocking, fp)
                if line is None:
                    break
                parsed = _parse_line(line)
                if parsed is None:
                    continue
                yield _attach_gateway_ts(parsed)
        finally:

            def _close():
                fp.close()

            await loop.run_in_executor(None, _close)
