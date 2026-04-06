/**
 * POST /api/telemetry/ingest
 *
 * Accepts a batch of normalized TelemetryFrames from the gateway.
 * No raw protocol parsing — only normalized frames accepted.
 *
 * Auth: Gateway identity token (Doppler-managed secret).
 *
 * This is a stub implementation for the first sprint.
 * Production version will use Supabase client with proper auth.
 */

import type { TelemetryFrame, TelemetryBatch } from '../contracts/telemetry_frame';

// Validation: ensure no raw protocol fields leak through
function validateFrame(frame: TelemetryFrame): string | null {
  if (!frame.channel || typeof frame.channel !== 'string') {
    return 'missing or invalid channel';
  }
  if (typeof frame.value !== 'number' || !isFinite(frame.value)) {
    return 'missing or invalid value';
  }
  if (!frame.ts_wall_rfc3339 || typeof frame.ts_wall_rfc3339 !== 'string') {
    return 'missing or invalid ts_wall_rfc3339';
  }
  if (!frame.device_id || typeof frame.device_id !== 'string') {
    return 'missing or invalid device_id';
  }
  if (!frame.session_id || typeof frame.session_id !== 'string') {
    return 'missing or invalid session_id';
  }
  // Provenance must exist but is treated as opaque JSONB
  if (!frame.provenance || typeof frame.provenance !== 'object') {
    return 'missing provenance';
  }
  return null;
}

// Stub handler — in production this becomes a Next.js API route or edge function
export async function handleIngest(batch: TelemetryBatch): Promise<{
  accepted: number;
  rejected: number;
  errors: string[];
}> {
  const errors: string[] = [];
  let accepted = 0;
  let rejected = 0;

  for (const frame of batch.frames) {
    const err = validateFrame(frame);
    if (err) {
      rejected++;
      errors.push(`${frame.channel || 'unknown'}: ${err}`);
      continue;
    }
    // In production: insert into telemetry_samples via Supabase client
    // For now: just count
    accepted++;
  }

  return { accepted, rejected, errors };
}

// Type guard for incoming JSON
export function isTelemetryBatch(obj: unknown): obj is TelemetryBatch {
  if (typeof obj !== 'object' || obj === null) return false;
  const o = obj as Record<string, unknown>;
  return Array.isArray(o.frames);
}
