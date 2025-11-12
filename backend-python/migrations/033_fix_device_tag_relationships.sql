-- Migration 033: Fix Device-Tag Relationships
-- Adds proper constraints and indexes for device_tags table
-- This migration ensures the missing DeviceTagModel is properly supported

-- =======================
-- Fix device_tags table if missing proper constraints
-- =======================

-- Ensure the table exists (should already exist from previous migrations)
CREATE TABLE IF NOT EXISTS device_tags (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    assigned_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT uix_device_tag UNIQUE (device_id, tag_id)
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS ix_device_tags_device_id ON device_tags(device_id);
CREATE INDEX IF NOT EXISTS ix_device_tags_tag_id ON device_tags(tag_id);
CREATE INDEX IF NOT EXISTS ix_device_tags_assigned_at ON device_tags(assigned_at);

-- =======================
-- Update devices table to support playlist assignment  
-- =======================

-- Add assigned_playlist_id column if it doesn't exist
ALTER TABLE devices 
ADD COLUMN IF NOT EXISTS assigned_playlist_id INTEGER REFERENCES playlists(id) ON DELETE SET NULL;

-- Add index for performance
CREATE INDEX IF NOT EXISTS ix_devices_assigned_playlist_id ON devices(assigned_playlist_id);

-- =======================
-- Performance optimizations for organization isolation
-- =======================

-- Add composite indexes for organization-based queries
CREATE INDEX IF NOT EXISTS ix_devices_org_status ON devices(organization_id, status);
CREATE INDEX IF NOT EXISTS ix_devices_org_last_seen ON devices(organization_id, last_seen);

-- Add index for heartbeat queries
CREATE INDEX IF NOT EXISTS ix_devices_code_expires ON devices(unique_code, code_expires_at) 
WHERE unique_code IS NOT NULL;

-- =======================
-- Validation constraints
-- =======================

-- Ensure device_type is valid
ALTER TABLE devices 
DROP CONSTRAINT IF EXISTS chk_device_type,
ADD CONSTRAINT chk_device_type CHECK (device_type IN ('tv', 'monitor'));

-- Ensure device status is valid  
ALTER TABLE devices
DROP CONSTRAINT IF EXISTS chk_device_status,
ADD CONSTRAINT chk_device_status CHECK (status IN ('pending', 'active', 'inactive'));

-- Ensure privacy_mode is valid
ALTER TABLE devices
DROP CONSTRAINT IF EXISTS chk_privacy_mode,
ADD CONSTRAINT chk_privacy_mode CHECK (privacy_mode IN ('none', 'limited', 'full'));

-- Ensure location_type is valid
ALTER TABLE devices
DROP CONSTRAINT IF EXISTS chk_location_type, 
ADD CONSTRAINT chk_location_type CHECK (location_type IN ('lobby', 'guest_room', 'restaurant', 'meeting_room', 'elevator', 'other'));

-- =======================
-- Comments for documentation
-- =======================

COMMENT ON TABLE device_tags IS 'Many-to-many relationship between devices and tags with assignment tracking';
COMMENT ON COLUMN device_tags.assigned_at IS 'When the tag was assigned to the device';
COMMENT ON COLUMN device_tags.assigned_by IS 'User who assigned the tag to the device';

COMMENT ON COLUMN devices.assigned_playlist_id IS 'Direct playlist assignment for device (overrides tag-based assignment)';