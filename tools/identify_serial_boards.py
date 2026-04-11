#!/usr/bin/env python3
"""Read first JSON lines from each /dev/ttyUSB* at 921600 to tell sim vs mini-debug apart."""

from __future__ import annotations

import glob
import sys
import time

try:
    import serial
except ImportError:
    print("pip install pyserial", file=sys.stderr)
    sys.exit(2)


def sniff(port: str, baud: int = 921600, max_lines: int = 30) -> None:
    print(f"\n{'=' * 60}\n{port} @ {baud}\n{'=' * 60}")
    try:
        ser = serial.Serial(port, baud, timeout=0.25)
    except OSError as e:
        print(f"  (cannot open: {e})")
        return
    time.sleep(0.5)
    n = 0
    t0 = time.time()
    while n < max_lines and time.time() - t0 < 4.0:
        raw = ser.readline()
        if not raw:
            continue
        line = raw.decode("utf-8", errors="replace").strip()
        if line:
            print(line)
            n += 1
            if "startup" in line or "firmware" in line or "version" in line:
                if "esp32-can-sim" in line or "can-sim" in line:
                    print("  >>> LIKELY: esp32-can-sim (TX bench)")
                if "mini-debug" in line.lower() or '"firmware"' in line and "can-sim" not in line:
                    if "can-sim" not in line:
                        print("  >>> LIKELY: esp32-mini-debug (receiver firmware)")
    ser.close()


def main() -> int:
    ports = sorted(glob.glob("/dev/ttyUSB*")) + sorted(glob.glob("/dev/ttyACM*"))
    if not ports:
        print("No /dev/ttyUSB* or /dev/ttyACM* — plug ESP32 USB and re-run.")
        return 1
    for p in ports:
        sniff(p)
    print("\nTip: esp32-can-sim startup JSON contains firmware name can-sim;")
    print("mini-debug shows bench/listen mode in startup. Flash FT600 listen with:")
    print("  cd esp32-mini-debug && pio run -e esp32dev -t upload --upload-port <port>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
