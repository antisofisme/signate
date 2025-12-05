-- Migration: 084
-- Description: Add behavioral metrics columns to device_health_metrics table
-- Purpose: Track playback stalls, buffer underruns, quality switches, etc. (Phase 3)
-- Date: 2025-12-05

BEGIN;

-- Add behavioral metrics columns to device_health_metrics table
ALTER TABLE device_health_metrics
ADD COLUMN IF NOT EXISTS playback_stalls_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS buffer_underruns_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS time_to_first_playback_ms INTEGER,
ADD COLUMN IF NOT EXISTS content_play_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS quality_switches_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS content_load_failures_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS error_rate_percent NUMERIC(5, 2);

-- Add comments for documentation
COMMENT ON COLUMN device_health_metrics.playback_stalls_count IS 'Video stall events (stalled) since device startup';
COMMENT ON COLUMN device_health_metrics.buffer_underruns_count IS 'Buffer underrun events (waiting) since device startup';
COMMENT ON COLUMN device_health_metrics.time_to_first_playback_ms IS 'Time from content load to first frame display (milliseconds)';
COMMENT ON COLUMN device_health_metrics.content_play_count IS 'Total content plays in current session';
COMMENT ON COLUMN device_health_metrics.quality_switches_count IS 'HLS/DASH quality switches in current session';
COMMENT ON COLUMN device_health_metrics.content_load_failures_count IS 'Content load failures in current session';
COMMENT ON COLUMN device_health_metrics.error_rate_percent IS 'Error rate percentage (failed/total operations * 100)';

COMMIT;
