"""Monotonic and wall-clock timestamp helpers for the gateway."""
import time
from datetime import datetime, timezone


def mono_ns() -> int:
    return time.monotonic_ns()


def wall_rfc3339() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def timestamp_pair() -> tuple[int, str]:
    return mono_ns(), wall_rfc3339()
