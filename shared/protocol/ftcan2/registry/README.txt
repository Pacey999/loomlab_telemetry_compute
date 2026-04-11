SSOT for FTCAN 2.0 gateway
---------------------------
Canonical measure/product tables remain in:
  shared/protocol/ftcan/registry/measure-registry.json

ftcan2 adds no duplicate tables. Future codegen should emit from that JSON (or
a merged ftcan2 registry) into Python + C++ from one source.
