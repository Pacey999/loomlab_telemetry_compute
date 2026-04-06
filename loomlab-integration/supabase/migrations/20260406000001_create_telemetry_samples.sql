-- Telemetry samples table for normalized gateway frames.
-- SSOT-safe: this migration only adds new tables, does not alter existing schema.

CREATE TABLE IF NOT EXISTS telemetry_samples (
  id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  ts_mono_ns    BIGINT NOT NULL,
  ts_wall       TIMESTAMPTZ NOT NULL,
  device_id     TEXT NOT NULL,
  stream_id     TEXT NOT NULL,
  session_id    TEXT NOT NULL,
  channel       TEXT NOT NULL,
  value         DOUBLE PRECISION NOT NULL,
  unit          TEXT NOT NULL DEFAULT '-',
  quality       TEXT NOT NULL DEFAULT 'good',
  status_u16    INTEGER NOT NULL DEFAULT 0,
  provenance    JSONB NOT NULL DEFAULT '{}',
  ingested_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index for session-based queries (most common access pattern)
CREATE INDEX IF NOT EXISTS idx_telemetry_samples_session
  ON telemetry_samples (session_id, channel, ts_mono_ns);

-- Index for latest-value lookups per device/stream/channel
CREATE INDEX IF NOT EXISTS idx_telemetry_samples_latest
  ON telemetry_samples (device_id, stream_id, channel, ts_mono_ns DESC);

-- Index for time-range queries
CREATE INDEX IF NOT EXISTS idx_telemetry_samples_time
  ON telemetry_samples (ts_wall);

-- Enable RLS (Row Level Security) for future multi-tenant support
ALTER TABLE telemetry_samples ENABLE ROW LEVEL SECURITY;

-- Basic policy: allow authenticated users to read/write their own device data
-- (This is a placeholder — real policies will be defined when auth is integrated)
CREATE POLICY telemetry_samples_all ON telemetry_samples
  FOR ALL
  USING (true)
  WITH CHECK (true);

COMMENT ON TABLE telemetry_samples IS
  'Normalized telemetry samples from the GTM gateway. No raw CAN protocol data.';
COMMENT ON COLUMN telemetry_samples.provenance IS
  'Protocol-opaque provenance metadata as JSONB. Contains mode, protocol, product_id, message_id, measure_id, source_seq.';
