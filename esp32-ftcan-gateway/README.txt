esp32-ftcan-gateway
-------------------
Full FTCAN 2.0 receiver firmware target (sprint bootstrap).

Outputs per extended frame:
  - type=header   — parsed ProductID / DataFieldID / MessageID (no decode gate)
  - type=frame    — raw id29, dlc, data bytes

Plus type=health / warn as in mini-debug.

Flash: pio run -e esp32dev -t upload --upload-port /dev/ttyUSB0

Do not use this folder for narrow bench-only validation; extend with Layer 3–6
per FTCAN2_FULL_RECEIVER_SPRINT.txt.
