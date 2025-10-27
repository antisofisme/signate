-- ============================================================================
-- Rollback Migration 007: Rename contents back to content
-- ============================================================================
-- Author: Database Architect
-- Date: 2025-10-27
-- Purpose: Rollback migration to restore the original 'content' table name
--          if the rename to 'contents' needs to be reversed
--
-- IMPORTANT: This rollback handles 4 foreign key constraints:
-- 1. content_assignments.content_id → content.id
-- 2. playlist_content.content_id → content.id
-- 3. schedules.content_id → content.id
-- 4. content.fallback_content_id → content.id (self-referential)
-- ============================================================================

BEGIN;

-- ============================================================================
-- Step 1: Drop all dependent foreign key constraints
-- ============================================================================
-- We must drop all foreign keys that reference the contents table before renaming back

-- Drop foreign key from content_assignments table
ALTER TABLE content_assignments
    DROP CONSTRAINT IF EXISTS content_assignments_content_id_fkey;

-- Drop foreign key from playlist_content table
ALTER TABLE playlist_content
    DROP CONSTRAINT IF EXISTS playlist_content_content_id_fkey;

-- Drop foreign key from schedules table
ALTER TABLE schedules
    DROP CONSTRAINT IF EXISTS schedules_content_id_fkey;

-- Drop self-referential foreign key from contents table
ALTER TABLE contents
    DROP CONSTRAINT IF EXISTS contents_fallback_content_id_fkey;

-- ============================================================================
-- Step 2: Rename the table back from 'contents' to 'content'
-- ============================================================================
ALTER TABLE contents RENAME TO content;

-- ============================================================================
-- Step 3: Restore the original sequence name (if it was renamed)
-- ============================================================================
-- Check if the sequence exists and rename it back
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relkind = 'S' AND relname = 'contents_id_seq') THEN
        ALTER SEQUENCE contents_id_seq RENAME TO content_id_seq;
    END IF;
END $$;

-- ============================================================================
-- Step 4: Recreate all foreign key constraints with the original table name
-- ============================================================================

-- Recreate foreign key from content_assignments to content
ALTER TABLE content_assignments
    ADD CONSTRAINT content_assignments_content_id_fkey
    FOREIGN KEY (content_id)
    REFERENCES content(id)
    ON DELETE CASCADE;

-- Recreate foreign key from playlist_content to content
ALTER TABLE playlist_content
    ADD CONSTRAINT playlist_content_content_id_fkey
    FOREIGN KEY (content_id)
    REFERENCES content(id)
    ON DELETE CASCADE;

-- Recreate foreign key from schedules to content
ALTER TABLE schedules
    ADD CONSTRAINT schedules_content_id_fkey
    FOREIGN KEY (content_id)
    REFERENCES content(id)
    ON DELETE CASCADE;

-- Recreate self-referential foreign key for fallback_content_id
ALTER TABLE content
    ADD CONSTRAINT content_fallback_content_id_fkey
    FOREIGN KEY (fallback_content_id)
    REFERENCES content(id)
    ON DELETE SET NULL;

-- ============================================================================
-- Step 5: Restore original column comments
-- ============================================================================
COMMENT ON TABLE content IS 'Stores all content items (images, videos, HTML templates, etc.) for the digital signage system';
COMMENT ON COLUMN content.fallback_content_id IS 'Fallback content if template fails';

-- ============================================================================
-- Step 6: Update any views that might reference the table
-- ============================================================================
-- Note: If there are any views that were updated in the forward migration,
-- they would need to be restored here. Currently, no views are defined.

COMMIT;

-- ============================================================================
-- Verification Queries (Run these after rollback to ensure success)
-- ============================================================================

-- 1. Verify table was renamed back successfully
SELECT
    'Table Rollback Check' as check_type,
    EXISTS (SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'content') as content_exists,
    NOT EXISTS (SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'contents') as contents_not_exists;

-- 2. Verify record count (should match pre-rollback count)
SELECT
    'Record Count' as check_type,
    COUNT(*) as total_records
FROM content;

-- 3. Verify all foreign key constraints were restored correctly
SELECT
    conname as constraint_name,
    conrelid::regclass as table_name,
    confrelid::regclass as referenced_table,
    pg_get_constraintdef(oid) as constraint_definition
FROM pg_constraint
WHERE confrelid = 'content'::regclass
   OR (conrelid = 'content'::regclass AND contype = 'f')
ORDER BY conname;

-- 4. Verify indexes are still intact
SELECT
    indexname,
    tablename,
    indexdef
FROM pg_indexes
WHERE tablename = 'content'
ORDER BY indexname;

-- 5. Verify self-referential foreign key works
SELECT
    c1.id,
    c1.title as content_title,
    c2.title as fallback_title
FROM content c1
LEFT JOIN content c2 ON c1.fallback_content_id = c2.id
WHERE c1.fallback_content_id IS NOT NULL
LIMIT 5;

-- 6. Verify foreign keys from other tables work
SELECT
    'content_assignments' as source_table,
    COUNT(*) as fk_references
FROM content_assignments ca
INNER JOIN content c ON ca.content_id = c.id
UNION ALL
SELECT
    'playlist_content' as source_table,
    COUNT(*) as fk_references
FROM playlist_content pc
INNER JOIN content c ON pc.content_id = c.id
UNION ALL
SELECT
    'schedules' as source_table,
    COUNT(*) as fk_references
FROM schedules s
INNER JOIN content c ON s.content_id = c.id;

-- ============================================================================
-- Rollback Summary
-- ============================================================================
-- This rollback successfully:
-- 1. Restored the original 'content' table name
-- 2. Restored all foreign key constraints (4 total)
-- 3. Preserved all data integrity
-- 4. Maintained all indexes
-- 5. Restored original comments
--
-- Use this rollback if:
-- - The forward migration causes issues
-- - Application code updates fail
-- - Performance problems occur
-- - Business decision to revert
-- ============================================================================