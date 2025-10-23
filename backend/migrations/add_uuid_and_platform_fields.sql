-- Migration: Add UUID and Platform fields to devices table
-- Date: 2025-10-23
-- Description: Adds permanent device UUID and WebOS platform metadata fields

-- Add UUID column (permanent device identifier)
ALTER TABLE devices ADD COLUMN IF NOT EXISTS device_uuid VARCHAR(36);

-- Add platform information columns
ALTER TABLE devices ADD COLUMN IF NOT EXISTS platform VARCHAR(20);
ALTER TABLE devices ADD COLUMN IF NOT EXISTS model_name VARCHAR(100);
ALTER TABLE devices ADD COLUMN IF NOT EXISTS firmware_version VARCHAR(50);

-- Add unique index on device_uuid (allow NULL for existing devices)
CREATE UNIQUE INDEX IF NOT EXISTS idx_devices_device_uuid ON devices(device_uuid) WHERE device_uuid IS NOT NULL;

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_devices_platform ON devices(platform);

-- Add comments
COMMENT ON COLUMN devices.device_uuid IS 'Permanent UUID for device identity (survives IP changes)';
COMMENT ON COLUMN devices.platform IS 'Platform type: webOS, browser, etc.';
COMMENT ON COLUMN devices.model_name IS 'Device model name (e.g., LG OLED55C1PUB)';
COMMENT ON COLUMN devices.firmware_version IS 'WebOS firmware version';
