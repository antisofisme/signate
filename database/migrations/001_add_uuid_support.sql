-- =============================================================================
-- MIGRATION: Add UUID and metadata support for devices
-- Version: 001
-- Date: 2025-10-23
-- Purpose: Add device_uuid, platform, and device metadata columns
-- =============================================================================

-- Add new columns for UUID-based device identity
ALTER TABLE devices ADD COLUMN IF NOT EXISTS device_uuid VARCHAR(36) UNIQUE;
ALTER TABLE devices ADD COLUMN IF NOT EXISTS platform VARCHAR(50);

-- Add device metadata columns
ALTER TABLE devices ADD COLUMN IF NOT EXISTS model VARCHAR(100);
ALTER TABLE devices ADD COLUMN IF NOT EXISTS manufacturer VARCHAR(100);
ALTER TABLE devices ADD COLUMN IF NOT EXISTS os_version VARCHAR(50);
ALTER TABLE devices ADD COLUMN IF NOT EXISTS screen_resolution VARCHAR(20);

-- Create indexes for new columns
CREATE INDEX IF NOT EXISTS idx_devices_device_uuid ON devices(device_uuid);
CREATE INDEX IF NOT EXISTS idx_devices_platform ON devices(platform);

-- Add comments for new columns
COMMENT ON COLUMN devices.device_uuid IS 'UUID v4 untuk WebOS devices (persistent identifier)';
COMMENT ON COLUMN devices.platform IS 'Platform info: webOS, browser, etc.';
COMMENT ON COLUMN devices.model IS 'Device model (e.g., LG 43UN7300)';
COMMENT ON COLUMN devices.manufacturer IS 'Manufacturer (e.g., LG)';
COMMENT ON COLUMN devices.os_version IS 'OS version (e.g., webOS 6.0)';
COMMENT ON COLUMN devices.screen_resolution IS 'Screen resolution (e.g., 1920x1080)';

-- Update existing devices to set platform based on unique_code presence
UPDATE devices
SET platform = CASE
    WHEN unique_code IS NOT NULL THEN 'browser'
    WHEN ip_address IS NOT NULL THEN 'tv'
    ELSE 'unknown'
END
WHERE platform IS NULL;

-- Verification queries
SELECT
    COUNT(*) as total_devices,
    COUNT(device_uuid) as devices_with_uuid,
    COUNT(unique_code) as devices_with_code,
    COUNT(CASE WHEN platform = 'browser' THEN 1 END) as browser_devices,
    COUNT(CASE WHEN platform = 'webOS' THEN 1 END) as webos_devices,
    COUNT(CASE WHEN platform = 'tv' THEN 1 END) as tv_devices
FROM devices;

-- =============================================================================
-- END OF MIGRATION
-- =============================================================================
