-- ============================================================================
-- Migration 006: Create Device Tags Table
-- Description: Many-to-many relationship between devices and tags
-- Created: 2025-01-07
-- ============================================================================

-- Create device_tags junction table
CREATE TABLE IF NOT EXISTS device_tags (
    -- Identity
    id SERIAL PRIMARY KEY,

    -- Foreign Keys
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,

    -- Audit
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    assigned_by INTEGER REFERENCES users(id) ON DELETE SET NULL,

    -- Unique constraint: prevent duplicate assignments
    CONSTRAINT unique_device_tag UNIQUE (device_id, tag_id)
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Find tags by device
CREATE INDEX idx_device_tags_device ON device_tags(device_id);

-- Find devices by tag
CREATE INDEX idx_device_tags_tag ON device_tags(tag_id);

-- Combined index for faster joins
CREATE INDEX idx_device_tags_both ON device_tags(device_id, tag_id);

-- Audit: Find assignments by user
CREATE INDEX idx_device_tags_assigned_by ON device_tags(assigned_by);

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON TABLE device_tags IS 'Many-to-many relationship between devices and tags for organization and content routing';
COMMENT ON COLUMN device_tags.device_id IS 'Reference to device';
COMMENT ON COLUMN device_tags.tag_id IS 'Reference to tag';
COMMENT ON COLUMN device_tags.assigned_at IS 'Timestamp when tag was assigned to device';
COMMENT ON COLUMN device_tags.assigned_by IS 'User who assigned the tag to device';

-- ============================================================================
-- Verification Query
-- ============================================================================

-- Verify table created
SELECT
    table_name,
    (SELECT count(*) FROM information_schema.columns WHERE table_name = 'device_tags') as column_count
FROM information_schema.tables
WHERE table_name = 'device_tags';

-- Verify indexes created
SELECT
    tablename,
    indexname
FROM pg_indexes
WHERE tablename = 'device_tags'
ORDER BY indexname;

-- ============================================================================
-- Example Usage
-- ============================================================================

-- Assign tag to device
-- INSERT INTO device_tags (device_id, tag_id, assigned_by)
-- VALUES (1, 1, 1);

-- Get all tags for a device
-- SELECT t.* FROM tags t
-- JOIN device_tags dt ON dt.tag_id = t.id
-- WHERE dt.device_id = 1;

-- Get all devices with a specific tag
-- SELECT d.* FROM devices d
-- JOIN device_tags dt ON dt.device_id = d.id
-- WHERE dt.tag_id = 1;

-- Remove tag from device
-- DELETE FROM device_tags WHERE device_id = 1 AND tag_id = 1;

-- ============================================================================
-- Migration Instructions
-- ============================================================================

-- To run this migration on server:
-- docker exec -i signage-postgres psql -U signage_user -d signage_db < backend-python/migrations/006_create_device_tags_table.sql
