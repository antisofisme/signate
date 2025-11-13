-- Migration: Remove Duplicate Role Column from Users Table
-- Date: 2025-11-13
-- Purpose: Eliminate data redundancy - keep only role_id FK, remove role string column
-- Related Issue: users table has BOTH role (string) AND role_id (FK) causing redundancy

-- ============================================================================
-- PHASE 1: Verify role_id is populated for all users
-- ============================================================================

DO $$
DECLARE
    users_without_role_id INTEGER;
BEGIN
    -- Count users with NULL role_id
    SELECT COUNT(*) INTO users_without_role_id
    FROM users
    WHERE role_id IS NULL;

    IF users_without_role_id > 0 THEN
        RAISE NOTICE '⚠️  Found % users with NULL role_id', users_without_role_id;

        -- Try to populate role_id based on role string
        -- Map old role strings to role IDs
        UPDATE users u
        SET role_id = r.id
        FROM roles r
        WHERE u.role_id IS NULL
          AND LOWER(u.role) = LOWER(r.name)
          AND r.is_system_role = true;

        -- Check again
        SELECT COUNT(*) INTO users_without_role_id
        FROM users
        WHERE role_id IS NULL;

        IF users_without_role_id > 0 THEN
            RAISE EXCEPTION 'Cannot drop role column: % users still have NULL role_id', users_without_role_id;
        END IF;

        RAISE NOTICE '✅ Successfully populated role_id for all users';
    ELSE
        RAISE NOTICE '✅ All users already have role_id populated';
    END IF;
END $$;

-- ============================================================================
-- PHASE 2: Backup role data (for safety)
-- ============================================================================

-- Create temporary table to backup role data (just in case)
CREATE TEMP TABLE users_role_backup AS
SELECT id, username, role, role_id
FROM users;

RAISE NOTICE '✅ Created backup of role data in temp table users_role_backup';

-- ============================================================================
-- PHASE 3: Drop the duplicate role column
-- ============================================================================

ALTER TABLE users
    DROP COLUMN IF EXISTS role;

COMMENT ON COLUMN users.role_id IS 'User role (FK to roles.id) - SINGLE source of truth for user role';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
BEGIN
    -- Verify column dropped
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'role') THEN
        RAISE EXCEPTION 'Migration failed: role column still exists';
    END IF;

    -- Verify role_id column still exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'role_id') THEN
        RAISE EXCEPTION 'Migration failed: role_id column missing!';
    END IF;

    RAISE NOTICE '✅ Migration successful: Duplicate role column removed, role_id retained';
END $$;

-- ============================================================================
-- ROLLBACK INSTRUCTIONS (if needed)
-- ============================================================================

-- If you need to rollback, run this:
-- ALTER TABLE users ADD COLUMN role VARCHAR(20);
-- UPDATE users u SET role = r.name FROM roles r WHERE u.role_id = r.id;
