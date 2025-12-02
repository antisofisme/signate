-- Migration: 069
-- Description: Consolidate network metrics - designate device_speed_tests as source of truth
-- Date: 2025-12-02
--
-- Network metrics were stored in 3 tables with inconsistent naming:
-- - device_speed_tests: latency, download_speed, upload_speed (SOURCE OF TRUTH)
-- - device_health_metrics: network_latency_ms, network_download_mbps, network_upload_mbps (DEPRECATED)
-- - device_connection_logs: latency_ms, download_speed_mbps, upload_speed_mbps (REMOVED)

BEGIN;

-- 1. Add organization_id to device_speed_tests for multi-tenancy support (if missing)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'device_speed_tests' AND column_name = 'organization_id'
    ) THEN
        ALTER TABLE device_speed_tests
        ADD COLUMN organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE;

        -- Create index for organization queries
        CREATE INDEX IF NOT EXISTS idx_device_speed_tests_organization
        ON device_speed_tests(organization_id);
    END IF;
END $$;

-- 2. Backfill organization_id from devices table
UPDATE device_speed_tests dst
SET organization_id = d.organization_id
FROM devices d
WHERE dst.device_id = d.id
  AND dst.organization_id IS NULL;

-- 3. Mark duplicate network columns in device_health_metrics as deprecated
-- (Keep columns for backward compatibility, but document they should not be used)
COMMENT ON COLUMN device_health_metrics.network_latency_ms IS
'DEPRECATED: Use device_speed_tests.latency as source of truth for network metrics';

COMMENT ON COLUMN device_health_metrics.network_download_mbps IS
'DEPRECATED: Use device_speed_tests.download_speed as source of truth for network metrics';

COMMENT ON COLUMN device_health_metrics.network_upload_mbps IS
'DEPRECATED: Use device_speed_tests.upload_speed as source of truth for network metrics';

-- 4. Remove speed metrics from device_connection_logs (if they exist)
-- These columns store redundant data and should be in device_speed_tests
DO $$
BEGIN
    -- Remove latency_ms if exists
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'device_connection_logs' AND column_name = 'latency_ms'
    ) THEN
        ALTER TABLE device_connection_logs DROP COLUMN latency_ms;
    END IF;

    -- Remove download_speed_mbps if exists
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'device_connection_logs' AND column_name = 'download_speed_mbps'
    ) THEN
        ALTER TABLE device_connection_logs DROP COLUMN download_speed_mbps;
    END IF;

    -- Remove upload_speed_mbps if exists
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'device_connection_logs' AND column_name = 'upload_speed_mbps'
    ) THEN
        ALTER TABLE device_connection_logs DROP COLUMN upload_speed_mbps;
    END IF;
END $$;

-- 5. Update table comments to document source of truth
COMMENT ON TABLE device_speed_tests IS
'SOURCE OF TRUTH for network performance metrics (latency, download/upload speeds).
Records network speed test results from device players.';

COMMENT ON TABLE device_health_metrics IS
'System health metrics (CPU, Memory, Disk).
NOTE: network_* columns are DEPRECATED - use device_speed_tests for network metrics.';

COMMENT ON TABLE device_connection_logs IS
'Device connection event logs (status changes, connects/disconnects).
Not for metrics storage - use device_speed_tests for network metrics.';

COMMIT;
