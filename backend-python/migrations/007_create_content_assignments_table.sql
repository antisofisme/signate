-- ============================================================================
-- Migration 007: Create Content Assignments Table
-- Description: Direct content-to-device assignments (Priority 1)
-- Created: 2025-01-07
-- ============================================================================

-- Create content_assignments table
CREATE TABLE IF NOT EXISTS content_assignments (
    -- Identity
    id SERIAL PRIMARY KEY,

    -- Foreign Keys
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    content_id INTEGER NOT NULL REFERENCES contents(id) ON DELETE CASCADE,

    -- Assignment priority (higher = more important)
    priority INTEGER DEFAULT 1 NOT NULL,

    -- Schedule override (optional - NULL means always show)
    schedule JSONB,

    -- Audit
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    assigned_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    expires_at TIMESTAMP WITH TIME ZONE,  -- Optional expiration

    -- Unique constraint: prevent duplicate assignments
    CONSTRAINT unique_device_content UNIQUE (device_id, content_id)
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Find content by device (most common query)
CREATE INDEX idx_content_assignments_device ON content_assignments(device_id);

-- Find devices by content
CREATE INDEX idx_content_assignments_content ON content_assignments(content_id);

-- Combined index for faster joins
CREATE INDEX idx_content_assignments_both ON content_assignments(device_id, content_id);

-- Audit: Find assignments by user
CREATE INDEX idx_content_assignments_assigned_by ON content_assignments(assigned_by);

-- Priority-based queries
CREATE INDEX idx_content_assignments_priority ON content_assignments(device_id, priority DESC);

-- Expiration queries (find expired assignments)
CREATE INDEX idx_content_assignments_expires ON content_assignments(expires_at)
WHERE expires_at IS NOT NULL;

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON TABLE content_assignments IS 'Direct content-to-device assignments (Priority 1 - highest priority)';
COMMENT ON COLUMN content_assignments.device_id IS 'Reference to device';
COMMENT ON COLUMN content_assignments.content_id IS 'Reference to content';
COMMENT ON COLUMN content_assignments.priority IS 'Assignment priority within direct assignments (higher = more important)';
COMMENT ON COLUMN content_assignments.schedule IS 'JSONB schedule override (NULL = always show)';
COMMENT ON COLUMN content_assignments.assigned_at IS 'Timestamp when content was assigned to device';
COMMENT ON COLUMN content_assignments.assigned_by IS 'User who assigned the content to device';
COMMENT ON COLUMN content_assignments.expires_at IS 'Optional expiration timestamp (NULL = never expires)';

-- ============================================================================
-- Verification Query
-- ============================================================================

-- Verify table created
SELECT
    table_name,
    (SELECT count(*) FROM information_schema.columns WHERE table_name = 'content_assignments') as column_count
FROM information_schema.tables
WHERE table_name = 'content_assignments';

-- Verify indexes created
SELECT
    tablename,
    indexname
FROM pg_indexes
WHERE tablename = 'content_assignments'
ORDER BY indexname;

-- ============================================================================
-- Example Usage
-- ============================================================================

-- Assign content to device
-- INSERT INTO content_assignments (device_id, content_id, priority, assigned_by)
-- VALUES (1, 1, 10, 1);

-- Get all content for a device (ordered by priority)
-- SELECT c.*, ca.priority, ca.schedule, ca.expires_at
-- FROM contents c
-- JOIN content_assignments ca ON ca.content_id = c.id
-- WHERE ca.device_id = 1
--   AND (ca.expires_at IS NULL OR ca.expires_at > NOW())
-- ORDER BY ca.priority DESC;

-- Get all devices assigned to specific content
-- SELECT d.*, ca.assigned_at, ca.assigned_by
-- FROM devices d
-- JOIN content_assignments ca ON ca.device_id = d.id
-- WHERE ca.content_id = 1;

-- Remove content from device
-- DELETE FROM content_assignments WHERE device_id = 1 AND content_id = 1;

-- Clean up expired assignments
-- DELETE FROM content_assignments WHERE expires_at IS NOT NULL AND expires_at < NOW();

-- ============================================================================
-- Priority System
-- ============================================================================

-- Content routing priority levels:
-- Priority 1 (Highest): Direct device-content assignments (this table)
-- Priority 2 (Medium):  Tag-based assignments (via device_tags + content_tags)
-- Priority 3 (Low):     Playlist assignments (via playlist_assignments)

-- Within Priority 1 (direct assignments):
-- - Higher 'priority' value = shown first
-- - Same priority = random or round-robin

-- ============================================================================
-- Migration Instructions
-- ============================================================================

-- To run this migration on server:
-- docker exec -i signage-postgres psql -U signage_user -d signage_db < backend-python/migrations/007_create_content_assignments_table.sql
