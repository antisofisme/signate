-- Migration: 073
-- Description: Remove tag_id column from content_assignments table
-- Reason: Tag-based content assignment now uses content_tags table (single source of truth)
--         content_assignments.tag_id was duplicate/redundant
-- Date: 2024-12-03

BEGIN;

-- 1. Delete any existing rows with tag_id (these should be migrated to content_tags if needed)
-- First, let's log what we're deleting
DO $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM content_assignments WHERE tag_id IS NOT NULL;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RAISE NOTICE 'Deleted % rows with tag_id from content_assignments', deleted_count;
END $$;

-- 2. Drop the check constraint that requires either device_id OR tag_id
ALTER TABLE content_assignments DROP CONSTRAINT IF EXISTS content_assignments_target_check;

-- 3. Drop indexes related to tag_id
DROP INDEX IF EXISTS idx_content_assignments_tag;
DROP INDEX IF EXISTS idx_content_assignments_org_tag;

-- 4. Drop unique constraint for tag-based assignments
ALTER TABLE content_assignments DROP CONSTRAINT IF EXISTS unique_org_tag_content;

-- 5. Drop the foreign key constraint
ALTER TABLE content_assignments DROP CONSTRAINT IF EXISTS content_assignments_tag_id_fkey;

-- 6. Finally, drop the tag_id column
ALTER TABLE content_assignments DROP COLUMN IF EXISTS tag_id;

-- 7. Add new constraint: device_id is now REQUIRED (not nullable)
-- Since tag_id is removed, all assignments must have device_id
ALTER TABLE content_assignments ALTER COLUMN device_id SET NOT NULL;

-- 8. Add comment to clarify the table purpose
COMMENT ON TABLE content_assignments IS 'Direct content-to-device assignments. For tag-based assignments, use content_tags table instead.';

COMMIT;
