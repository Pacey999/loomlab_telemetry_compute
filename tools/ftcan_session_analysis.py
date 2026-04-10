"""Parse esp32-mini-debug JSONL sessions (recorded serial) and compute stats."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


@dataclass
class SessionStats:
    lines: int = 0
    parse_errors: int = 0
    frame_lines: int = 0
    decoded_lines: int = 0
    health_lines: int = 0
    other_types: Counter[str] = field(default_factory=Counter)
    id29: set[str] = field(default_factory=set)
    decoded_channels: set[str] = field(default_factory=set)
    last_channel_value: dict[str, float] = field(default_factory=dict)
    bus_error_first: int | None = None
    bus_error_last: int | None = None
    bus_off_first: int | None = None
    bus_off_last: int | None = None


def iter_json_objects(path: Path) -> Iterator[tuple[int, dict | None, str | None]]:
    """Yield (line_no, parsed dict or None, raw line)."""
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield i, json.loads(line), line
            except json.JSONDecodeError:
                yield i, None, line


def analyze_session(path: Path) -> SessionStats:
    st = SessionStats()
    for line_no, obj, raw in iter_json_objects(path):
        st.lines += 1
        if obj is None:
            st.parse_errors += 1
            continue
        t = obj.get("type")
        if t in ("session_meta", "session_footer"):
            continue
        if t == "frame" and "id29" in obj:
            st.frame_lines += 1
            st.id29.add(str(obj["id29"]))
        elif t == "decoded" and "channel" in obj:
            st.decoded_lines += 1
            ch = str(obj["channel"])
            st.decoded_channels.add(ch)
            try:
                st.last_channel_value[ch] = float(obj.get("value", 0))
            except (TypeError, ValueError):
                pass
        elif t == "health":
            st.health_lines += 1
            be = obj.get("bus_error_count")
            bo = obj.get("bus_off_count")
            if isinstance(be, int):
                st.bus_error_last = be
                if st.bus_error_first is None:
                    st.bus_error_first = be
            if isinstance(bo, int):
                st.bus_off_last = bo
                if st.bus_off_first is None:
                    st.bus_off_first = bo
        else:
            st.other_types[str(t) if t is not None else "null"] += 1
    return st
