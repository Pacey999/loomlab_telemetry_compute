/**
 * TelemetryFrame — Normalized telemetry sample from the gateway.
 *
 * This is the canonical contract between the telemetry gateway and LoomLab.
 * LoomLab receives ONLY normalized frames — no raw CAN protocol data.
 */

export interface TelemetryProvenance {
  /** "live" | "replay" | "synthetic" */
  mode: string;
  /** Source protocol identifier (e.g., "ftcan") */
  protocol: string;
  /** Source product ID (numeric) */
  product_id: number;
  /** Source message ID (numeric) */
  message_id: number;
  /** Source measure ID (numeric) */
  measure_id: number;
  /** Source sequence number from the capture node */
  source_seq: number;
}

export interface TelemetryFrame {
  /** Monotonic timestamp in nanoseconds (from gateway) */
  ts_mono_ns: number;
  /** Wall-clock timestamp in RFC3339 format */
  ts_wall_rfc3339: string;
  /** Device identifier (e.g., "gtm-ft600-bench") */
  device_id: string;
  /** Stream identifier (e.g., "ftcan0") */
  stream_id: string;
  /** Session identifier */
  session_id: string;
  /** Normalized channel name (e.g., "engine.rpm") */
  channel: string;
  /** Engineering-unit value */
  value: number;
  /** Unit string (e.g., "rpm", "bar", "°C") */
  unit: string;
  /** Quality flag: "good" | "suspect" | "stale" | "status" | "unknown" */
  quality: string;
  /** Raw status word (0 if this is a value, not a status) */
  status_u16: number;
  /** Provenance metadata — protocol-opaque to LoomLab */
  provenance: TelemetryProvenance;
}

export interface TelemetryBatch {
  /** Array of telemetry frames in this batch */
  frames: TelemetryFrame[];
  /** Batch metadata */
  batch_id?: string;
  /** ISO timestamp of batch creation */
  batch_ts?: string;
}
