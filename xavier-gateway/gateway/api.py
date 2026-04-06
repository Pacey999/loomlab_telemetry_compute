"""FastAPI control plane for the GTM telemetry gateway."""
from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from gateway.decoder import GatewayDecoder
from gateway.replay import replay_session
from gateway.ingest import SerialIngest
from gateway.session import (
    Session,
    close_session,
    open_session,
    write_normalized_sample,
    write_raw_frame,
)
from gateway.timestamps import mono_ns, wall_rfc3339

logger = logging.getLogger(__name__)


class GatewayState:
    """Module-level gateway runtime state."""

    def __init__(self) -> None:
        self.start_mono_ns: int = 0
        self.active_session: Session | None = None
        self.total_frames: int = 0
        self.total_normalized_samples: int = 0
        self.ingest_task: asyncio.Task[None] | None = None
        self.lock: asyncio.Lock | None = None
        self.log_dir: Path = Path("./sessions")
        self.serial_port: str = "/dev/ttyUSB0"
        self.serial_baud: int = 115200
        self.decoder: GatewayDecoder | None = None
        # channel -> {value, unit, quality, ts_wall, ts_mono_ns} (ts_mono_ns internal for age_ms)
        self.latest_signals: dict[str, dict[str, Any]] = {}


state = GatewayState()


class ReplayRequest(BaseModel):
    raw_session_path: str
    output_path: str
    speed_factor: float = Field(default=1.0, ge=0.0)


def _load_config_from_env() -> None:
    state.log_dir = Path(os.environ.get("GTM_LOG_DIR", "./sessions"))
    state.serial_port = os.environ.get("GTM_SERIAL_PORT", "/dev/ttyUSB0")
    state.serial_baud = int(os.environ.get("GTM_SERIAL_BAUD", "115200"))


def _ingest_mono_wall(frame: dict[str, Any]) -> tuple[int, str]:
    mono = frame.get("gateway_mono_ns")
    wall = frame.get("gateway_wall")
    if isinstance(mono, int) and isinstance(wall, str):
        return mono, wall
    return mono_ns(), wall_rfc3339()


def _apply_decoded_samples(sess: Session, telemetry_frames: list[dict[str, Any]]) -> None:
    for t in telemetry_frames:
        write_normalized_sample(sess, t)
        state.total_normalized_samples += 1
        ch = t["channel"]
        state.latest_signals[ch] = {
            "value": t["value"],
            "unit": t["unit"],
            "quality": t["quality"],
            "ts_wall": t["ts_wall_rfc3339"],
            "ts_mono_ns": t["ts_mono_ns"],
        }


INACTIVITY_TIMEOUT_S = int(os.environ.get("GTM_INACTIVITY_TIMEOUT_S", "300"))


async def _serial_ingest_loop() -> None:
    ingest = SerialIngest(state.serial_port, state.serial_baud)
    last_frame_mono = mono_ns()
    try:
        async for frame in ingest.frames():
            last_frame_mono = mono_ns()
            async with state.lock:  # type: ignore[union-attr]
                sess = state.active_session
                if sess is None or sess.status != "active":
                    break
                write_raw_frame(sess, frame)
                state.total_frames += 1
                dec = state.decoder
                if dec is not None:
                    m, wall = _ingest_mono_wall(frame)
                    try:
                        telemetry = dec.decode_frame(frame, sess.session_id, m, wall)
                        if telemetry:
                            _apply_decoded_samples(sess, telemetry)
                    except Exception:
                        logger.exception("Decode error for frame seq=%s", frame.get("seq"))
            idle_s = (mono_ns() - last_frame_mono) / 1e9
            if idle_s > INACTIVITY_TIMEOUT_S:
                logger.warning("Inactivity timeout (%ds) — auto-closing session", INACTIVITY_TIMEOUT_S)
                async with state.lock:  # type: ignore[union-attr]
                    if state.active_session is not None:
                        close_session(state.active_session)
                        state.active_session = None
                break
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("Ingest loop error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _load_config_from_env()
    state.lock = asyncio.Lock()
    state.start_mono_ns = mono_ns()
    logger.info(
        "Gateway starting (log_dir=%s, serial=%s @ %s)",
        state.log_dir,
        state.serial_port,
        state.serial_baud,
    )
    yield
    if state.ingest_task and not state.ingest_task.done():
        state.ingest_task.cancel()
        try:
            await state.ingest_task
        except asyncio.CancelledError:
            pass
    state.ingest_task = None
    if state.active_session is not None:
        close_session(state.active_session)
        state.active_session = None


app = FastAPI(title="GTM Telemetry Gateway", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, Any]:
    uptime_s = (mono_ns() - state.start_mono_ns) / 1e9 if state.start_mono_ns else 0.0
    async with state.lock:  # type: ignore[union-attr]
        active_id = state.active_session.session_id if state.active_session else None
        total = state.total_frames
        norm_n = state.total_normalized_samples
        sig_n = len(state.latest_signals)
    return {
        "status": "ok",
        "uptime_s": round(uptime_s, 3),
        "active_session": active_id,
        "total_frames": total,
        "total_normalized_samples": norm_n,
        "latest_signal_channels": sig_n,
    }


@app.post("/session/start")
async def session_start() -> dict[str, str]:
    async with state.lock:  # type: ignore[union-attr]
        if state.active_session is not None and state.active_session.status == "active":
            raise HTTPException(status_code=409, detail="session already active")
        if state.ingest_task is not None and state.ingest_task.done():
            state.ingest_task = None
        if state.ingest_task is not None:
            raise HTTPException(status_code=409, detail="ingest already running")
        sess = open_session(state.log_dir)
        state.active_session = sess
        state.decoder = GatewayDecoder()
        state.latest_signals = {}
        state.total_normalized_samples = 0
        state.ingest_task = asyncio.create_task(_serial_ingest_loop())
    return {"session_id": sess.session_id}


@app.post("/session/stop")
async def session_stop() -> dict[str, str]:
    async with state.lock:  # type: ignore[union-attr]
        if state.active_session is None or state.active_session.status != "active":
            raise HTTPException(status_code=400, detail="no active session")
        sid = state.active_session.session_id
        task = state.ingest_task
        state.ingest_task = None
    if task is not None and not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    async with state.lock:  # type: ignore[union-attr]
        if state.active_session is not None:
            close_session(state.active_session)
            state.active_session = None
    return {"session_id": sid, "status": "stopped"}


@app.post("/replay")
async def replay(req: ReplayRequest) -> dict[str, Any]:
    """Replay a raw JSONL session through the canonical decoder (synchronous).

    ``speed_factor`` is accepted for API compatibility; replay is currently
    immediate (no simulated pacing).
    """
    _ = req.speed_factor
    raw_p = Path(req.raw_session_path)
    out_p = Path(req.output_path)
    if not raw_p.is_file():
        raise HTTPException(status_code=400, detail=f"raw_session_path not found: {raw_p}")
    try:
        stats = replay_session(raw_p, out_p)
    except OSError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return stats


@app.get("/signals/latest")
async def signals_latest() -> dict[str, Any]:
    """Latest decoded value per channel (updated during active ingest)."""
    now = mono_ns()
    async with state.lock:  # type: ignore[union-attr]
        out: dict[str, Any] = {}
        for ch, row in state.latest_signals.items():
            mono_sample = row.get("ts_mono_ns", now)
            age_ms = max(0, int((now - int(mono_sample)) / 1e6))
            out[ch] = {
                "value": row["value"],
                "unit": row["unit"],
                "quality": row["quality"],
                "ts_wall": row["ts_wall"],
                "age_ms": age_ms,
            }
        return out
