-- Migration: 081
-- Description: Data integrity cleanup and orphan record handling
-- Date: 2025-12-04
-- Impact: Cleans up orphaned records and adds helper function

BEGIN;

-- ============================================================================
-- 1. CLEAN ORPHANED PLAYLIST CONTENTS
-- Records pointing to soft-deleted content
-- ============================================================================

DELETE FROM playlist_contents
WHERE content_id IN (
    SELECT id FROM contents WHERE deleted_at IS NOT NULL
);

-- ============================================================================
-- 2. CLEAN ORPHANED CONTENT ASSIGNMENTS
-- Records pointing to soft-deleted content
-- ============================================================================

DELETE FROM content_assignments
WHERE content_id IN (
    SELECT id FROM contents WHERE deleted_at IS NOT NULL
);

-- ============================================================================
-- 3. CREATE CLEANUP FUNCTION FOR PERIODIC MAINTENANCE
-- ============================================================================

CREATE OR REPLACE FUNCTION cleanup_soft_deleted_content()
RETURNS TABLE(
    playlist_contents_deleted INTEGER,
    content_assignments_deleted INTEGER,
    schedule_targets_deleted INTEGER
) AS $$
DECLARE
    pc_count INTEGER;
    ca_count INTEGER;
    st_count INTEGER;
BEGIN
    -- Remove playlist references to soft-deleted content (>30 days old)
    DELETE FROM playlist_contents
    WHERE content_id IN (
        SELECT id FROM contents
        WHERE deleted_at < NOW() - INTERVAL '30 days'
    );
    GET DIAGNOSTICS pc_count = ROW_COUNT;

    -- Remove content assignment references to soft-deleted content
    DELETE FROM content_assignments
    WHERE content_id IN (
        SELECT id FROM contents
        WHERE deleted_at < NOW() - INTERVAL '30 days'
    );
    GET DIAGNOSTICS ca_count = ROW_COUNT;

    -- Remove schedule device targeting for soft-deleted devices (>30 days old)
    DELETE FROM schedule_device_targeting
    WHERE device_id IN (
        SELECT id FROM devices
        WHERE deleted_at < NOW() - INTERVAL '30 days'
    );
    GET DIAGNOSTICS st_count = ROW_COUNT;

    RETURN QUERY SELECT pc_count, ca_count, st_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_soft_deleted_content() IS
    'Cleans up references to soft-deleted content and devices older than 30 days. Run periodically for maintenance.';

-- ============================================================================
-- 4. ADD ORGANIZATION_ID TO PASSWORD_HISTORY (Multi-tenancy)
-- ============================================================================

-- Add column if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'password_history'
        AND column_name = 'organization_id'
    ) THEN
        ALTER TABLE password_history
            ADD COLUMN organization_id INTEGER
            REFERENCES organizations(id) ON DELETE CASCADE;

        -- Backfill from users table
        UPDATE password_history ph
        SET organization_id = u.organization_id
        FROM users u
        WHERE ph.user_id = u.id AND ph.organization_id IS NULL;

        -- Create index for multi-tenant queries
        CREATE INDEX IF NOT EXISTS idx_password_history_org
            ON password_history(organization_id);
    END IF;
END $$;

COMMIT;

-- ============================================================================
-- USAGE:
-- To run cleanup manually: SELECT * FROM cleanup_soft_deleted_content();
-- Schedule this to run weekly via pg_cron or external job scheduler
-- ============================================================================

-- ============================================================================
-- ROLLBACK (if needed):
-- DROP FUNCTION IF EXISTS cleanup_soft_deleted_content();
-- ALTER TABLE password_history DROP COLUMN IF EXISTS organization_id;
-- ============================================================================
