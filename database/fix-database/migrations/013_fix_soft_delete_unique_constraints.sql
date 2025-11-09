-- ============================================================================
-- Migration 013: Fix Soft Delete Unique Constraints
-- Description: Allow reuse of names after soft delete (playlists, tags, contents)
-- Created: 2025-01-09
-- Priority: CRITICAL
-- ============================================================================

BEGIN;

-- ============================================================================
-- ISSUE SUMMARY
-- ============================================================================
-- Problem: UNIQUE constraints include deleted_at column, preventing name reuse
-- Example: UNIQUE (organization_id, name, deleted_at)
--
-- Scenario:
--   1. Create playlist "Morning News" (org 1)
--   2. Soft delete it (deleted_at = NOW())
--   3. Try to create new playlist "Morning News" (org 1)
--   4. ERROR: duplicate key value violates unique constraint
--
-- Solution: Use partial unique index (WHERE deleted_at IS NULL)
-- ============================================================================

-- ============================================================================
-- 1. FIX PLAYLISTS TABLE
-- ============================================================================

-- Drop old constraint
ALTER TABLE playlists
    DROP CONSTRAINT IF EXISTS unique_playlist_name_per_org;

-- Create partial unique index (only for non-deleted rows)
CREATE UNIQUE INDEX IF NOT EXISTS unique_playlist_name_per_org_active
    ON playlists (organization_id, name)
    WHERE deleted_at IS NULL;

COMMENT ON INDEX unique_playlist_name_per_org_active IS
    'Allows same playlist name to be reused after soft delete';

-- ============================================================================
-- 2. FIX TAGS TABLE (if it has similar constraint)
-- ============================================================================

-- Check if tags has soft delete + unique constraint
-- Drop old constraint if exists
ALTER TABLE tags
    DROP CONSTRAINT IF EXISTS unique_tag_name_per_org;

-- Create partial unique index (only for non-deleted rows)
CREATE UNIQUE INDEX IF NOT EXISTS unique_tag_name_per_org_active
    ON tags (organization_id, name)
    WHERE deleted_at IS NULL;

COMMENT ON INDEX unique_tag_name_per_org_active IS
    'Allows same tag name to be reused after soft delete';

-- ============================================================================
-- 3. FIX CONTENTS TABLE (if applicable)
-- ============================================================================

-- Contents don't have unique name constraint, but if they did:
-- Note: Contents are identified by storage_key (already unique), not name
-- No action needed for contents table

-- ============================================================================
-- 4. ADD ASSIGNMENT TRACKING (Bonus Fix)
-- ============================================================================

-- Add missing assigned_by tracking to playlist_assignments
-- (As mentioned in DATABASE_SCHEMA_REVIEW.md)

DO $$
BEGIN
    -- Check if column doesn't exist
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'playlist_assignments'
          AND column_name = 'assigned_by'
    ) THEN
        ALTER TABLE playlist_assignments
            ADD COLUMN assigned_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
            ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE;

        CREATE INDEX idx_playlist_assignments_assigned_by
            ON playlist_assignments(assigned_by);

        COMMENT ON COLUMN playlist_assignments.assigned_by IS
            'User who created this assignment';
    END IF;
END $$;

-- ============================================================================
-- 5. VERIFICATION QUERY
-- ============================================================================

-- Verify partial unique indexes created
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE indexname IN (
    'unique_playlist_name_per_org_active',
    'unique_tag_name_per_org_active'
)
ORDER BY tablename;

-- Test soft delete + recreate scenario (example)
/*
-- Should work now:
INSERT INTO playlists (name, organization_id) VALUES ('Test Playlist', 1);
-- Soft delete
UPDATE playlists SET deleted_at = NOW() WHERE name = 'Test Playlist' AND organization_id = 1;
-- Create again with same name (should succeed)
INSERT INTO playlists (name, organization_id) VALUES ('Test Playlist', 1);
*/

-- Count duplicates (should be 0 for active playlists)
SELECT
    organization_id,
    name,
    count(*) as duplicate_count
FROM playlists
WHERE deleted_at IS NULL
GROUP BY organization_id, name
HAVING count(*) > 1;

-- Count duplicates for tags
SELECT
    organization_id,
    name,
    count(*) as duplicate_count
FROM tags
WHERE deleted_at IS NULL
GROUP BY organization_id, name
HAVING count(*) > 1;

COMMIT;

-- ============================================================================
-- ROLLBACK SCRIPT (if needed)
-- ============================================================================

-- To rollback this migration:
/*
BEGIN;

-- Drop partial unique indexes
DROP INDEX IF EXISTS unique_playlist_name_per_org_active;
DROP INDEX IF EXISTS unique_tag_name_per_org_active;

-- Restore old constraints (WARNING: May fail if duplicates exist)
ALTER TABLE playlists
    ADD CONSTRAINT unique_playlist_name_per_org
    UNIQUE (organization_id, name, deleted_at);

ALTER TABLE tags
    ADD CONSTRAINT unique_tag_name_per_org
    UNIQUE (organization_id, name);

-- Remove assignment tracking columns
ALTER TABLE playlist_assignments DROP COLUMN IF EXISTS assigned_by;
ALTER TABLE playlist_assignments DROP COLUMN IF EXISTS updated_at;
DROP INDEX IF EXISTS idx_playlist_assignments_assigned_by;

COMMIT;
*/

-- ============================================================================
-- Migration Complete
-- ============================================================================

-- To run this migration on server:
-- docker exec -i signage-postgres psql -U signage_user -d signage_db < database/fix-database/migrations/013_fix_soft_delete_unique_constraints.sql
