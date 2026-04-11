SSOT for FTCAN 2.0 gateway
---------------------------
Canonical measure/product tables remain in:
  shared/protocol/ftcan/registry/measure-registry.json

ftcan2 adds no duplicate tables. Future codegen should emit from that JSON (or
a merged ftcan2 registry) into Python + C++ from one source.

Embedded target (single tree — no duplicate gateway project):
  esp32-full/ — ftcan_registry.h + decoder + gateway_header (type=header JSON)
See esp32-full/README.txt.
