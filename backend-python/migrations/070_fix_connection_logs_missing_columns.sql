-- Migration: 070
-- Description: Add missing columns to device_connection_logs table
-- Date: 2025-12-02
-- Purpose: Fix missing latency_ms, download_speed_mbps, upload_speed_mbps columns
--
-- These columns were defined in migration 046 but somehow missing from production table

BEGIN;

-- Add missing columns if they don't exist
DO $$
BEGIN
    -- Add latency_ms column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'device_connection_logs' AND column_name = 'latency_ms'
    ) THEN
        ALTER TABLE device_connection_logs
        ADD COLUMN latency_ms INTEGER CHECK (latency_ms >= 0);

        COMMENT ON COLUMN device_connection_logs.latency_ms IS
        'Network latency in milliseconds (for server and speed_test events)';

        RAISE NOTICE 'Added latency_ms column';
    END IF;

    -- Add download_speed_mbps column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'device_connection_logs' AND column_name = 'download_speed_mbps'
    ) THEN
        ALTER TABLE device_connection_logs
        ADD COLUMN download_speed_mbps NUMERIC(10, 2) CHECK (download_speed_mbps >= 0);

        COMMENT ON COLUMN device_connection_logs.download_speed_mbps IS
        'Download speed in Mbps (for speed_test events only)';

        RAISE NOTICE 'Added download_speed_mbps column';
    END IF;

    -- Add upload_speed_mbps column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'device_connection_logs' AND column_name = 'upload_speed_mbps'
    ) THEN
        ALTER TABLE device_connection_logs
        ADD COLUMN upload_speed_mbps NUMERIC(10, 2) CHECK (upload_speed_mbps >= 0);

        COMMENT ON COLUMN device_connection_logs.upload_speed_mbps IS
        'Upload speed in Mbps (for speed_test events only)';

        RAISE NOTICE 'Added upload_speed_mbps column';
    END IF;
END $$;

-- Create indexes for the new columns (if they don't exist)
CREATE INDEX IF NOT EXISTS idx_device_logs_latency
ON device_connection_logs(latency_ms) WHERE latency_ms IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_device_logs_download_speed
ON device_connection_logs(download_speed_mbps) WHERE download_speed_mbps IS NOT NULL;

COMMIT;
