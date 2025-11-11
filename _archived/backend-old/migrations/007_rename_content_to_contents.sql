-- ============================================================================
-- Migration 007: Rename content table to contents for naming consistency
-- ============================================================================
-- Author: Database Architect
-- Date: 2025-10-27
-- Purpose: Rename singular 'content' table to plural 'contents' to maintain
--          consistency with other table naming conventions (devices, playlists,
--          tags, schedules, etc.)
--
-- IMPORTANT: This migration handles 4 foreign key constraints:
-- 1. content_assignments.content_id → contents.id
-- 2. playlist_content.content_id → contents.id
-- 3. schedules.content_id → contents.id
-- 4. contents.fallback_content_id → contents.id (self-referential)
-- ============================================================================

BEGIN;

-- ============================================================================
-- Step 1: Drop all dependent foreign key constraints
-- ============================================================================
-- We must drop all foreign keys that reference the content table before renaming
-- This includes both foreign keys FROM other tables and the self-referential FK

-- Drop foreign key from content_assignments table
ALTER TABLE content_assignments
    DROP CONSTRAINT IF EXISTS content_assignments_content_id_fkey;

-- Drop foreign key from playlist_content table
ALTER TABLE playlist_content
    DROP CONSTRAINT IF EXISTS playlist_content_content_id_fkey;

-- Drop foreign key from schedules table
ALTER TABLE schedules
    DROP CONSTRAINT IF EXISTS schedules_content_id_fkey;

-- Drop self-referential foreign key from content table itself
ALTER TABLE content
    DROP CONSTRAINT IF EXISTS content_fallback_content_id_fkey;

-- ============================================================================
-- Step 2: Rename the table from 'content' to 'contents'
-- ============================================================================
ALTER TABLE content RENAME TO contents;

-- ============================================================================
-- Step 3: Update the sequence name for consistency (if it exists)
-- ============================================================================
-- Check if the sequence exists and rename it
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relkind = 'S' AND relname = 'content_id_seq') THEN
        ALTER SEQUENCE content_id_seq RENAME TO contents_id_seq;
    END IF;
END $$;

-- ============================================================================
-- Step 4: Recreate all foreign key constraints with the new table name
-- ============================================================================

-- Recreate foreign key from content_assignments to contents
ALTER TABLE content_assignments
    ADD CONSTRAINT content_assignments_content_id_fkey
    FOREIGN KEY (content_id)
    REFERENCES contents(id)
    ON DELETE CASCADE;

-- Recreate foreign key from playlist_content to contents
ALTER TABLE playlist_content
    ADD CONSTRAINT playlist_content_content_id_fkey
    FOREIGN KEY (content_id)
    REFERENCES contents(id)
    ON DELETE CASCADE;

-- Recreate foreign key from schedules to contents
ALTER TABLE schedules
    ADD CONSTRAINT schedules_content_id_fkey
    FOREIGN KEY (content_id)
    REFERENCES contents(id)
    ON DELETE CASCADE;

-- Recreate self-referential foreign key for fallback_content_id
ALTER TABLE contents
    ADD CONSTRAINT contents_fallback_content_id_fkey
    FOREIGN KEY (fallback_content_id)
    REFERENCES contents(id)
    ON DELETE SET NULL;

-- ============================================================================
-- Step 5: Update column comments to reference the new table name
-- ============================================================================
COMMENT ON TABLE contents IS 'Stores all content items (images, videos, HTML templates, etc.) for the digital signage system';
COMMENT ON COLUMN contents.fallback_content_id IS 'Fallback content if template fails - references contents(id)';

-- ============================================================================
-- Step 6: Update any views that might reference the old table name
-- ============================================================================
-- Note: If there are any views referencing 'content' table, they would need
-- to be recreated here. Currently, no views are defined in the schema.

COMMIT;

-- ============================================================================
-- Verification Queries (Run these after migration to ensure success)
-- ============================================================================

-- 1. Verify table was renamed successfully
SELECT
    'Table Rename Check' as check_type,
    EXISTS (SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'contents') as contents_exists,
    NOT EXISTS (SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'content') as content_not_exists;

-- 2. Verify record count (should match pre-migration count)
SELECT
    'Record Count' as check_type,
    COUNT(*) as total_records
FROM contents;

-- 3. Verify all foreign key constraints were recreated correctly
SELECT
    conname as constraint_name,
    conrelid::regclass as table_name,
    confrelid::regclass as referenced_table,
    pg_get_constraintdef(oid) as constraint_definition
FROM pg_constraint
WHERE confrelid = 'contents'::regclass
   OR (conrelid = 'contents'::regclass AND contype = 'f')
ORDER BY conname;

-- 4. Verify indexes are still intact
SELECT
    indexname,
    tablename,
    indexdef
FROM pg_indexes
WHERE tablename = 'contents'
ORDER BY indexname;

-- 5. Verify self-referential foreign key works
SELECT
    c1.id,
    c1.title as content_title,
    c2.title as fallback_title
FROM contents c1
LEFT JOIN contents c2 ON c1.fallback_content_id = c2.id
WHERE c1.fallback_content_id IS NOT NULL
LIMIT 5;

-- 6. Verify foreign keys from other tables work
SELECT
    'content_assignments' as source_table,
    COUNT(*) as fk_references
FROM content_assignments ca
INNER JOIN contents c ON ca.content_id = c.id
UNION ALL
SELECT
    'playlist_content' as source_table,
    COUNT(*) as fk_references
FROM playlist_content pc
INNER JOIN contents c ON pc.content_id = c.id
UNION ALL
SELECT
    'schedules' as source_table,
    COUNT(*) as fk_references
FROM schedules s
INNER JOIN contents c ON s.content_id = c.id;

-- ============================================================================
-- Migration Summary
-- ============================================================================
-- This migration successfully:
-- 1. Renamed the 'content' table to 'contents'
-- 2. Updated all foreign key constraints (4 total)
-- 3. Preserved all data integrity
-- 4. Maintained all indexes
-- 5. Updated relevant comments
--
-- Rollback: Use 007_rollback_rename_contents_to_content.sql if needed
-- ============================================================================