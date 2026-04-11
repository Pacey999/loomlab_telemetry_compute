esp32-full — full FTCAN measure map (embedded)
-----------------------------------------------
This target already carries the SSOT-generated registry:

  src/ftcan_registry.h   ← python -m shared.protocol.ftcan.generators.gen_cpp
                           (source: shared/protocol/ftcan/registry/measure-registry.json)

decoder.cpp applies tuple, simplified (0x600–0x608), and segmented FTCAN paths
using ftcan_find_measure() — broader than esp32-mini-debug; no FT600 product
gate in the decode dispatch.

Serial defaults: 115200 in main.cpp (change to 921600 if matching bench tools).

For new “gateway” work: align esp32-ftcan-gateway with patterns here + host
pipeline in shared/protocol/ftcan2/ rather than extending mini_decode.
