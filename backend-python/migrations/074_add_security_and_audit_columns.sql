-- Migration: 074
-- Description: Add security columns to users table and audit columns to roles table
-- Date: 2025-12-03
--
-- Changes:
-- 1. Add security columns to users table for account lockout:
--    - failed_login_attempts: Track consecutive failed login attempts
--    - locked_until: Timestamp when account lockout expires
--    - last_login_ip: Store last successful login IP address
--    - last_login_at: Track last successful login timestamp
--
-- 2. Add audit columns to roles table:
--    - created_by_id: User who created the role
--    - updated_by_id: User who last updated the role

BEGIN;

-- ============================================================================
-- 1. Add security columns to users table
-- ============================================================================

-- Check if columns already exist before adding
DO $$
BEGIN
    -- Add failed_login_attempts
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'failed_login_attempts'
    ) THEN
        ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0 NOT NULL;
        COMMENT ON COLUMN users.failed_login_attempts IS 'Number of consecutive failed login attempts';
    END IF;

    -- Add locked_until
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'locked_until'
    ) THEN
        ALTER TABLE users ADD COLUMN locked_until TIMESTAMP WITH TIME ZONE;
        COMMENT ON COLUMN users.locked_until IS 'Timestamp when account lockout expires (NULL if not locked)';
    END IF;

    -- Add last_login_ip
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'last_login_ip'
    ) THEN
        ALTER TABLE users ADD COLUMN last_login_ip VARCHAR(45);
        COMMENT ON COLUMN users.last_login_ip IS 'IP address of last successful login (IPv4 or IPv6)';
    END IF;

    -- Add last_login_at (if not exists)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'last_login_at'
    ) THEN
        ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP WITH TIME ZONE;
        COMMENT ON COLUMN users.last_login_at IS 'Timestamp of last successful login';
    END IF;
END $$;

-- ============================================================================
-- 2. Add audit columns to roles table
-- ============================================================================

DO $$
BEGIN
    -- Add created_by_id
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'roles' AND column_name = 'created_by_id'
    ) THEN
        ALTER TABLE roles ADD COLUMN created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;
        COMMENT ON COLUMN roles.created_by_id IS 'User who created this role';
    END IF;

    -- Add updated_by_id
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'roles' AND column_name = 'updated_by_id'
    ) THEN
        ALTER TABLE roles ADD COLUMN updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;
        COMMENT ON COLUMN roles.updated_by_id IS 'User who last updated this role';
    END IF;
END $$;

-- ============================================================================
-- 3. Add indexes for performance
-- ============================================================================

-- Index on locked_until for checking locked accounts
CREATE INDEX IF NOT EXISTS idx_users_locked_until ON users(locked_until) WHERE locked_until IS NOT NULL;

-- Index on last_login_at for recent login queries
CREATE INDEX IF NOT EXISTS idx_users_last_login_at ON users(last_login_at);

-- Indexes on roles audit columns
CREATE INDEX IF NOT EXISTS idx_roles_created_by ON roles(created_by_id);
CREATE INDEX IF NOT EXISTS idx_roles_updated_by ON roles(updated_by_id);

-- ============================================================================
-- 4. Add check constraints
-- ============================================================================

-- Ensure failed_login_attempts is non-negative
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'check_users_failed_login_attempts_non_negative'
    ) THEN
        ALTER TABLE users ADD CONSTRAINT check_users_failed_login_attempts_non_negative
            CHECK (failed_login_attempts >= 0);
    END IF;
END $$;

COMMIT;

-- ============================================================================
-- Verification query (run after migration)
-- ============================================================================
-- SELECT
--     column_name, data_type, is_nullable, column_default
-- FROM information_schema.columns
-- WHERE table_name IN ('users', 'roles')
-- AND column_name IN (
--     'failed_login_attempts', 'locked_until', 'last_login_ip', 'last_login_at',
--     'created_by_id', 'updated_by_id'
-- )
-- ORDER BY table_name, column_name;
