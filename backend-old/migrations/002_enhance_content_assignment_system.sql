-- Migration: Enhance Content Assignment System
-- Date: 2025-10-26
-- Description: Add content assignment enhancements, tag priority, and playlist scheduling features
-- Phase: 1 - Database Schema (Core Features)

-- ===========================================================================
-- PART 1: Enhance content_assignments table
-- ===========================================================================

-- Add new columns to content_assignments
ALTER TABLE content_assignments
ADD COLUMN IF NOT EXISTS display_order INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS start_date TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS end_date TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS notes TEXT,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Create indexes for content_assignments
CREATE INDEX IF NOT EXISTS idx_content_assignments_display_order ON content_assignments(display_order);
CREATE INDEX IF NOT EXISTS idx_content_assignments_is_active ON content_assignments(is_active);
CREATE INDEX IF NOT EXISTS idx_content_assignments_dates ON content_assignments(start_date, end_date);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_content_assignment_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_content_assignment_updated_at
BEFORE UPDATE ON content_assignments
FOR EACH ROW
EXECUTE FUNCTION update_content_assignment_updated_at();

-- Comment on columns for documentation
COMMENT ON COLUMN content_assignments.display_order IS 'Order of content within the same assignment group (0-indexed)';
COMMENT ON COLUMN content_assignments.is_active IS 'Whether this assignment is currently active (soft delete)';
COMMENT ON COLUMN content_assignments.start_date IS 'Optional start date for scheduled content';
COMMENT ON COLUMN content_assignments.end_date IS 'Optional end date for scheduled content';
COMMENT ON COLUMN content_assignments.notes IS 'Admin notes about this assignment';

-- ===========================================================================
-- PART 2: Enhance tags table
-- ===========================================================================

-- Add tag_priority column to tags
ALTER TABLE tags
ADD COLUMN IF NOT EXISTS tag_priority INTEGER DEFAULT 0;

-- Create index for tag_priority
CREATE INDEX IF NOT EXISTS idx_tags_priority ON tags(tag_priority);

-- Comment on column
COMMENT ON COLUMN tags.tag_priority IS 'Priority among tags (higher number = higher priority in content resolution)';

-- ===========================================================================
-- PART 3: Enhance playlists table for scheduling
-- ===========================================================================

-- Add scheduling columns to playlists
ALTER TABLE playlists
ADD COLUMN IF NOT EXISTS schedule_mode VARCHAR(20) DEFAULT 'inclusive' CHECK (schedule_mode IN ('inclusive', 'exclusive')),
ADD COLUMN IF NOT EXISTS schedule_start TIME,
ADD COLUMN IF NOT EXISTS schedule_end TIME,
ADD COLUMN IF NOT EXISTS schedule_days VARCHAR(50),
ADD COLUMN IF NOT EXISTS schedule_timezone VARCHAR(50) DEFAULT 'Asia/Jakarta';

-- Create index for schedule queries
CREATE INDEX IF NOT EXISTS idx_playlists_schedule ON playlists(schedule_mode, schedule_start, schedule_end) WHERE schedule_start IS NOT NULL;

-- Comment on columns
COMMENT ON COLUMN playlists.schedule_mode IS 'inclusive: add to rotation, exclusive: replace all other content during schedule';
COMMENT ON COLUMN playlists.schedule_start IS 'Time when playlist should start (e.g., 06:00:00)';
COMMENT ON COLUMN playlists.schedule_end IS 'Time when playlist should end (e.g., 12:00:00)';
COMMENT ON COLUMN playlists.schedule_days IS 'JSON array of active days: ["mon","tue","wed","thu","fri","sat","sun"]';
COMMENT ON COLUMN playlists.schedule_timezone IS 'Timezone for schedule times (e.g., Asia/Jakarta, UTC)';

-- ===========================================================================
-- MIGRATION DATA: Set default values for existing data
-- ===========================================================================

-- Set default display_order for existing content_assignments (based on creation order)
UPDATE content_assignments
SET display_order = sub.row_num
FROM (
    SELECT id,
           ROW_NUMBER() OVER (
               PARTITION BY COALESCE(device_id::TEXT, '') || COALESCE(tag_id::TEXT, '')
               ORDER BY created_at
           ) - 1 AS row_num
    FROM content_assignments
) sub
WHERE content_assignments.id = sub.id
AND content_assignments.display_order = 0;

-- Set default tag_priority for existing tags (alphabetical order)
UPDATE tags
SET tag_priority = sub.row_num
FROM (
    SELECT id, ROW_NUMBER() OVER (ORDER BY tag_name) AS row_num
    FROM tags
) sub
WHERE tags.id = sub.id
AND tags.tag_priority = 0;

-- ===========================================================================
-- VERIFICATION QUERIES (for testing)
-- ===========================================================================

-- Uncomment these to verify the migration worked correctly
-- SELECT column_name, data_type, column_default, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'content_assignments'
-- ORDER BY ordinal_position;

-- SELECT column_name, data_type, column_default, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'tags'
-- ORDER BY ordinal_position;

-- SELECT column_name, data_type, column_default, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'playlists'
-- ORDER BY ordinal_position;

COMMIT;
