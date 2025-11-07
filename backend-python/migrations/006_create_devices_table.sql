-- Migration 006: Create Devices Table
-- Created: 2025-01-07
-- Description: Device registration, monitoring, and management with multi-tenancy

-- ============================================================================
-- 1. DEVICES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS devices (
    id SERIAL PRIMARY KEY,

    -- Device identification
    device_type VARCHAR(20) NOT NULL CHECK (device_type IN ('tv', 'monitor')),
    device_name VARCHAR(200) NOT NULL,
    device_uuid VARCHAR(100) UNIQUE,  -- For WebOS devices

    -- Multi-tenancy
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Activation system
    unique_code VARCHAR(6) UNIQUE,  -- 6-digit activation code
    code_expires_at TIMESTAMP WITH TIME ZONE,

    -- Status & monitoring
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'inactive')),
    last_seen TIMESTAMP WITH TIME ZONE,

    -- Network information
    ip_address VARCHAR(45),  -- IPv6 support
    platform VARCHAR(50),  -- 'webOS', 'browser', 'tizen', etc.
    user_agent VARCHAR(500),
    connection_type VARCHAR(50),  -- 'wifi', 'ethernet', '4g', etc.
    connection_speed REAL,  -- Mbps

    -- Display specifications
    screen_width INTEGER,
    screen_height INTEGER,
    viewport_width INTEGER,
    viewport_height INTEGER,
    device_pixel_ratio REAL,

    -- Display settings
    rotation INTEGER DEFAULT 0 NOT NULL CHECK (rotation IN (0, 90, 180, 270)),
    volume_enabled BOOLEAN DEFAULT TRUE NOT NULL,

    -- WebOS specific fields
    model_name VARCHAR(100),
    firmware_version VARCHAR(50),

    -- Hotel-specific features
    room_number VARCHAR(50),
    location_type VARCHAR(50) DEFAULT 'guest_room' NOT NULL,
    supports_personalization BOOLEAN DEFAULT TRUE NOT NULL,
    privacy_mode VARCHAR(20) DEFAULT 'limited' NOT NULL CHECK (privacy_mode IN ('none', 'limited', 'full')),

    -- Audit tracking
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE,
    released_at TIMESTAMP WITH TIME ZONE  -- When device was released/deactivated
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_devices_organization ON devices(organization_id);
CREATE INDEX IF NOT EXISTS idx_devices_status ON devices(status);
CREATE INDEX IF NOT EXISTS idx_devices_unique_code ON devices(unique_code);
CREATE INDEX IF NOT EXISTS idx_devices_device_uuid ON devices(device_uuid);
CREATE INDEX IF NOT EXISTS idx_devices_room_number ON devices(room_number);
CREATE INDEX IF NOT EXISTS idx_devices_last_seen ON devices(last_seen);
CREATE INDEX IF NOT EXISTS idx_devices_created_by ON devices(created_by);

-- ============================================================================
-- COMMENTS (Documentation)
-- ============================================================================

COMMENT ON TABLE devices IS 'Device registration and monitoring with multi-tenant support';
COMMENT ON COLUMN devices.device_type IS 'Device type: tv (WebOS/native app) or monitor (browser-based)';
COMMENT ON COLUMN devices.device_uuid IS 'Unique device identifier for WebOS devices';
COMMENT ON COLUMN devices.unique_code IS '6-digit activation code (expires in 10 minutes)';
COMMENT ON COLUMN devices.status IS 'Device status: pending (awaiting activation), active (operational), inactive (released)';
COMMENT ON COLUMN devices.last_seen IS 'Last heartbeat timestamp (for online/offline detection)';
COMMENT ON COLUMN devices.rotation IS 'Screen rotation in degrees (0, 90, 180, 270)';
COMMENT ON COLUMN devices.room_number IS 'Hotel room number (for hotel deployments)';
COMMENT ON COLUMN devices.location_type IS 'Device location type in hotel (guest_room, lobby, restaurant, etc.)';
COMMENT ON COLUMN devices.privacy_mode IS 'Privacy level: none (full access), limited (restricted), full (maximum privacy)';
COMMENT ON COLUMN devices.created_by IS 'User who registered/created the device';
COMMENT ON COLUMN devices.updated_by IS 'User who last updated device settings';
COMMENT ON COLUMN devices.released_at IS 'Timestamp when device was released (moved to inactive)';

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify table created
SELECT
    table_name,
    (SELECT count(*) FROM information_schema.columns WHERE table_name = 'devices') as column_count
FROM information_schema.tables
WHERE table_name = 'devices';

-- Verify indexes created
SELECT
    tablename,
    indexname
FROM pg_indexes
WHERE tablename = 'devices'
ORDER BY indexname;

-- Verify constraints
SELECT
    conname as constraint_name,
    contype as constraint_type
FROM pg_constraint
WHERE conrelid = 'devices'::regclass
ORDER BY conname;
