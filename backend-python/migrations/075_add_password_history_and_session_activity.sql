-- Migration: 075
-- Description: Add password history table and session last activity tracking
-- Date: 2025-12-03
--
-- Changes:
-- 1. Create password_history table to prevent password reuse
-- 2. Add last_activity_at column to user_sessions table
--
-- Security Features:
-- - Password history prevents reuse of recent passwords
-- - Session activity tracking enables idle session detection

BEGIN;

-- ============================================================================
-- 1. Create password_history table
-- ============================================================================

CREATE TABLE IF NOT EXISTS password_history (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Index for efficient lookups by user
CREATE INDEX IF NOT EXISTS idx_password_history_user ON password_history(user_id);

-- Index for cleanup of old records (created_at)
CREATE INDEX IF NOT EXISTS idx_password_history_created ON password_history(created_at);

-- Comments
COMMENT ON TABLE password_history IS 'Stores hashed passwords to prevent reuse of recent passwords';
COMMENT ON COLUMN password_history.user_id IS 'Reference to the user';
COMMENT ON COLUMN password_history.password_hash IS 'Bcrypt hashed password (for reuse check only)';
COMMENT ON COLUMN password_history.created_at IS 'When this password was set';

-- ============================================================================
-- 2. Add last_activity_at to user_sessions
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_sessions' AND column_name = 'last_activity_at'
    ) THEN
        ALTER TABLE user_sessions ADD COLUMN last_activity_at TIMESTAMP WITH TIME ZONE;
        COMMENT ON COLUMN user_sessions.last_activity_at IS 'Last activity timestamp for idle session detection';
    END IF;
END $$;

-- Index for finding inactive sessions
CREATE INDEX IF NOT EXISTS idx_user_sessions_last_activity ON user_sessions(last_activity_at)
    WHERE last_activity_at IS NOT NULL;

-- ============================================================================
-- 3. Initialize last_activity_at for existing sessions
-- ============================================================================

-- Set last_activity_at to created_at for existing active sessions
UPDATE user_sessions
SET last_activity_at = created_at
WHERE last_activity_at IS NULL
  AND is_revoked = FALSE
  AND expires_at > NOW();

-- ============================================================================
-- 4. Migrate existing passwords to history (optional - first password)
-- ============================================================================

-- Insert current passwords into history for existing users (one-time migration)
-- This ensures the current password is checked against reuse
INSERT INTO password_history (user_id, password_hash, created_at)
SELECT id, password_hash, COALESCE(updated_at, created_at)
FROM users
WHERE password_hash IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM password_history ph WHERE ph.user_id = users.id
  );

COMMIT;

-- ============================================================================
-- Verification query (run after migration)
-- ============================================================================
-- SELECT
--     'password_history' as table_name,
--     COUNT(*) as records
-- FROM password_history
-- UNION ALL
-- SELECT
--     'user_sessions with activity' as table_name,
--     COUNT(*) as records
-- FROM user_sessions
-- WHERE last_activity_at IS NOT NULL;
