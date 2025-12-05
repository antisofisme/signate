-- Migration: 087
-- Description: Add GeoIP columns to devices table
-- Purpose: Store geolocation data for devices (Phase 6: Server-Side Features)
-- Date: 2025-12-05

BEGIN;

-- Add GeoIP columns to devices table
ALTER TABLE devices
ADD COLUMN IF NOT EXISTS geo_city VARCHAR(100),
ADD COLUMN IF NOT EXISTS geo_country VARCHAR(100),
ADD COLUMN IF NOT EXISTS geo_country_code VARCHAR(10),
ADD COLUMN IF NOT EXISTS geo_region VARCHAR(100),
ADD COLUMN IF NOT EXISTS geo_isp VARCHAR(200),
ADD COLUMN IF NOT EXISTS geo_timezone VARCHAR(50),
ADD COLUMN IF NOT EXISTS geo_latitude DECIMAL(10, 6),
ADD COLUMN IF NOT EXISTS geo_longitude DECIMAL(10, 6),
ADD COLUMN IF NOT EXISTS geo_updated_at TIMESTAMP WITH TIME ZONE;

-- Add comments for documentation
COMMENT ON COLUMN devices.geo_city IS 'City name from GeoIP lookup';
COMMENT ON COLUMN devices.geo_country IS 'Country name from GeoIP lookup';
COMMENT ON COLUMN devices.geo_country_code IS 'ISO country code (e.g., US, ID, JP)';
COMMENT ON COLUMN devices.geo_region IS 'Region/State/Province from GeoIP';
COMMENT ON COLUMN devices.geo_isp IS 'Internet Service Provider name';
COMMENT ON COLUMN devices.geo_timezone IS 'Timezone identifier (e.g., Asia/Jakarta)';
COMMENT ON COLUMN devices.geo_latitude IS 'Latitude coordinate';
COMMENT ON COLUMN devices.geo_longitude IS 'Longitude coordinate';
COMMENT ON COLUMN devices.geo_updated_at IS 'When GeoIP data was last updated';

-- Create index for geographic queries
CREATE INDEX IF NOT EXISTS idx_devices_geo_country ON devices(geo_country);
CREATE INDEX IF NOT EXISTS idx_devices_geo_city ON devices(geo_city);

COMMIT;
