-- Migration: Add device information columns to devices table
-- Created: 2025-10-23
-- Description: Add columns to store viewer display information (screen resolution, viewport, DPR, user agent, connection)

-- Add device information columns
ALTER TABLE devices
ADD COLUMN screen_width INTEGER,
ADD COLUMN screen_height INTEGER,
ADD COLUMN viewport_width INTEGER,
ADD COLUMN viewport_height INTEGER,
ADD COLUMN device_pixel_ratio FLOAT,
ADD COLUMN user_agent TEXT,
ADD COLUMN connection_type VARCHAR(50),
ADD COLUMN connection_speed FLOAT;

-- Add comment for documentation
COMMENT ON COLUMN devices.screen_width IS 'Display screen width in pixels (e.g., 1920)';
COMMENT ON COLUMN devices.screen_height IS 'Display screen height in pixels (e.g., 1080)';
COMMENT ON COLUMN devices.viewport_width IS 'Browser viewport width in pixels';
COMMENT ON COLUMN devices.viewport_height IS 'Browser viewport height in pixels';
COMMENT ON COLUMN devices.device_pixel_ratio IS 'Device pixel ratio (e.g., 1.0, 2.0)';
COMMENT ON COLUMN devices.user_agent IS 'Browser user agent string';
COMMENT ON COLUMN devices.connection_type IS 'Network connection type (e.g., 4g, wifi)';
COMMENT ON COLUMN devices.connection_speed IS 'Network connection speed in Mbps';
