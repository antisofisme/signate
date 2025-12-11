-- Migration: 088
-- Description: Add local_ip column to devices table
-- Date: 2025-12-07
-- Purpose: Store device's local network IP (from WebRTC) for device identification

BEGIN;

-- Add local_ip column to devices table
ALTER TABLE devices ADD COLUMN IF NOT EXISTS local_ip VARCHAR(45);

-- Add comment
COMMENT ON COLUMN devices.local_ip IS 'Local network IP address (e.g., 192.168.1.100) from WebRTC detection';

-- Create index for quick lookups
CREATE INDEX IF NOT EXISTS idx_devices_local_ip ON devices(local_ip) WHERE local_ip IS NOT NULL;

COMMIT;
