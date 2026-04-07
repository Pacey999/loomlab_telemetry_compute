#!/usr/bin/env python3
"""One-shot serial capture for ESP32 mini/debug (921600)."""
import serial
import sys
import time

port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"
baud = int(sys.argv[2]) if len(sys.argv) > 2 else 921600
duration = float(sys.argv[3]) if len(sys.argv) > 3 else 12.0

ser = serial.Serial(port, baud, timeout=2)
ser.reset_input_buffer()
start = time.time()
count = frames = decoded = 0
while time.time() - start < duration and count < 200:
    line = ser.readline()
    if not line:
        continue
    text = line.decode("utf-8", errors="replace").strip()
    if not text:
        continue
    t = time.time() - start
    if '"type":"frame"' in text:
        frames += 1
        if frames <= 12:
            print(f"[{t:6.2f}s] {text}")
        elif frames == 13:
            print(f"[{t:6.2f}s] ... (more frames)")
    elif '"type":"decoded"' in text:
        decoded += 1
        if decoded <= 5:
            print(f"[{t:6.2f}s] {text}")
    else:
        print(f"[{t:6.2f}s] {text}")
    count += 1
ser.close()
print()
print("=== Summary ===")
print(f"lines={count} frames={frames} decoded={decoded}")
