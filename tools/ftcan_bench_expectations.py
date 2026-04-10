"""Shared expectations for FTCAN bench smoke tests (live serial + golden fixtures)."""

from __future__ import annotations

from dataclasses import dataclass

# ProductID 0x5020, DataFieldID 0x02, MessageIDs per simulator v1.2.0 pattern.
WANT_IDS = frozenset(
    {
        "0x140801FF",
        "0x140812FF",
        "0x140810FF",
        "0x14080600",
        "0x14080608",
        "0x140813FF",
        "0x14084600",
    }
)

WANT_CHANNELS = frozenset(
    {
        "engine.tps_pct",
        "engine.map_bar",
        "vehicle.wheel_speed_fr_kmh",
        "engine.trans_temp_c",
    }
)

MIN_FRAMES = 10


def accumulate_line(obj: dict, frames: int, ids: set[str], decoded: set[str]) -> tuple[int, set[str], set[str]]:
    """Update counters/sets from one parsed JSON object (mini-debug serial line)."""
    if obj.get("type") == "frame" and "id29" in obj:
        frames += 1
        ids.add(str(obj["id29"]))
    if obj.get("type") == "decoded" and "channel" in obj:
        decoded.add(str(obj["channel"]))
    return frames, ids, decoded


def _int_field(x: object) -> int | None:
    if isinstance(x, bool):
        return None
    if isinstance(x, int):
        return x
    if isinstance(x, float):
        return int(x)
    return None


@dataclass
class BenchHealthState:
    """Tracks first/last TWAI health snapshot from type=health lines."""

    bus_error_first: int | None = None
    bus_error_last: int | None = None
    bus_off_first: int | None = None
    bus_off_last: int | None = None
    health_lines: int = 0


def accumulate_health(obj: dict, h: BenchHealthState) -> None:
    """Update health state from one JSON object (esp32-mini-debug emit_health_json)."""
    if obj.get("type") != "health":
        return
    h.health_lines += 1
    be = _int_field(obj.get("bus_error_count"))
    bo = _int_field(obj.get("bus_off_count"))
    if be is not None:
        h.bus_error_last = be
        if h.bus_error_first is None:
            h.bus_error_first = be
    if bo is not None:
        h.bus_off_last = bo
        if h.bus_off_first is None:
            h.bus_off_first = bo


def check_bench(frames: int, ids: set[str], decoded: set[str]) -> tuple[bool, list[str]]:
    """Return (ok, human-readable failure reasons)."""
    errs: list[str] = []
    if frames < MIN_FRAMES:
        errs.append(f"frames {frames} < {MIN_FRAMES}")
    if not WANT_CHANNELS.issubset(decoded):
        errs.append(f"missing channels: {sorted(WANT_CHANNELS - decoded)}")
    if not (ids & WANT_IDS):
        errs.append(f"no expected id29 overlap (want any of {sorted(WANT_IDS)})")
    return (len(errs) == 0, errs)


def check_health(
    h: BenchHealthState,
    *,
    max_bus_error_delta: int | None,
    allow_bus_off_increase: bool,
) -> tuple[bool, list[str]]:
    """If no health lines, pass. Otherwise enforce bus_error growth and optional bus_off."""
    if h.health_lines == 0:
        return True, []
    errs: list[str] = []
    if max_bus_error_delta is not None and h.bus_error_first is not None and h.bus_error_last is not None:
        delta = h.bus_error_last - h.bus_error_first
        if delta > max_bus_error_delta:
            errs.append(
                f"bus_error_count grew by {delta} ({h.bus_error_first}->{h.bus_error_last}); max allowed {max_bus_error_delta}"
            )
    if not allow_bus_off_increase and h.bus_off_first is not None and h.bus_off_last is not None:
        if h.bus_off_last > h.bus_off_first:
            errs.append(f"bus_off_count increased {h.bus_off_first}->{h.bus_off_last}")
    return (len(errs) == 0, errs)
