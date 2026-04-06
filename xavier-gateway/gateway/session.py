"""Session lifecycle and raw/normalized JSONL log writers."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, TextIO

from gateway.timestamps import timestamp_pair

logger = logging.getLogger(__name__)


@dataclass
class Session:
    session_id: str
    start_time: str
    raw_log_path: Path
    normalized_log_path: Path
    status: Literal["active", "closed"] = "active"
    frame_count: int = 0
    _raw_fp: TextIO | None = field(default=None, repr=False)
    _norm_fp: TextIO | None = field(default=None, repr=False)


def _new_session_id() -> str:
    now = datetime.now(timezone.utc)
    return f"sess_{now.strftime('%Y%m%d_%H%M%S')}"


def open_session(log_dir: Path) -> Session:
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    session_id = _new_session_id()
    start_wall = timestamp_pair()[1]
    raw_path = log_dir / f"{session_id}_raw.jsonl"
    norm_path = log_dir / f"{session_id}_normalized.jsonl"
    raw_fp = open(raw_path, "a", encoding="utf-8")
    norm_fp = open(norm_path, "a", encoding="utf-8")
    session = Session(
        session_id=session_id,
        start_time=start_wall,
        raw_log_path=raw_path,
        normalized_log_path=norm_path,
        status="active",
        frame_count=0,
        _raw_fp=raw_fp,
        _norm_fp=norm_fp,
    )
    logger.info("Opened session %s", session_id)
    return session


def close_session(session: Session) -> None:
    if session.status == "closed":
        return
    if session._raw_fp is not None:
        session._raw_fp.flush()
        session._raw_fp.close()
        session._raw_fp = None
    if session._norm_fp is not None:
        session._norm_fp.flush()
        session._norm_fp.close()
        session._norm_fp = None
    session.status = "closed"
    logger.info("Closed session %s", session.session_id)


def write_raw_frame(session: Session, frame: dict[str, Any]) -> None:
    if session.status != "active" or session._raw_fp is None:
        raise RuntimeError("session is not active")
    if "gateway_mono_ns" not in frame or "gateway_wall" not in frame:
        mono, wall = timestamp_pair()
        out = {**frame, "gateway_mono_ns": mono, "gateway_wall": wall}
    else:
        out = dict(frame)
    session._raw_fp.write(json.dumps(out, separators=(",", ":")) + "\n")
    session._raw_fp.flush()
    session.frame_count += 1


def write_normalized_sample(session: Session, sample: dict[str, Any]) -> None:
    if session.status != "active" or session._norm_fp is None:
        raise RuntimeError("session is not active")
    mono, wall = timestamp_pair()
    out = {
        **sample,
        "gateway_mono_ns": mono,
        "gateway_wall": wall,
    }
    session._norm_fp.write(json.dumps(out, separators=(",", ":")) + "\n")
    session._norm_fp.flush()
