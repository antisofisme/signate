-- Migration: 086
-- Description: Add dns_resolution_ms column to device_health_metrics table
-- Purpose: Track DNS resolution time for network diagnostics (Phase 5)
-- Date: 2025-12-05

BEGIN;

-- Add dns_resolution_ms column to device_health_metrics table
ALTER TABLE device_health_metrics
ADD COLUMN IF NOT EXISTS dns_resolution_ms INTEGER;

-- Add comment for documentation
COMMENT ON COLUMN device_health_metrics.dns_resolution_ms IS 'DNS resolution time in milliseconds (Resource Timing API)';

COMMIT;
