-- ============================================================================
-- Migration 011: Create User Sessions Table (Session Management)
-- Description: Server-side session tracking for JWT token management
-- Created: 2025-01-09
-- Priority: CRITICAL
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. CREATE USER_SESSIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_sessions (
    -- Identity
    id SERIAL PRIMARY KEY,

    -- User reference
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Session identification (SHA256 hash of JWT)
    session_token VARCHAR(64) NOT NULL UNIQUE,
    refresh_token VARCHAR(64) UNIQUE,

    -- Client metadata
    ip_address VARCHAR(45) NOT NULL, -- IPv6 support
    user_agent VARCHAR(500),
    device_info JSONB, -- Browser, OS, device type, etc.

    -- Session lifecycle
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked_at TIMESTAMP WITH TIME ZONE, -- Manual logout/revocation

    -- Session type
    session_type VARCHAR(20) DEFAULT 'web' NOT NULL
        CHECK (session_type IN ('web', 'api', 'mobile', 'device')),

    -- Security flags
    is_active BOOLEAN GENERATED ALWAYS AS (
        revoked_at IS NULL AND expires_at > NOW()
    ) STORED,

    -- Constraints
    CONSTRAINT check_refresh_token_expires CHECK (
        refresh_token IS NULL OR expires_at > created_at
    )
);

-- ============================================================================
-- 2. CREATE INDEXES
-- ============================================================================

-- User lookup (find all sessions for user)
CREATE INDEX idx_sessions_user ON user_sessions(user_id);

-- Organization lookup (multi-tenant isolation)
CREATE INDEX idx_sessions_organization ON user_sessions(organization_id);

-- Token lookup (verify session by token)
CREATE INDEX idx_sessions_token ON user_sessions(session_token);

-- Refresh token lookup
CREATE INDEX idx_sessions_refresh ON user_sessions(refresh_token) WHERE refresh_token IS NOT NULL;

-- Expiration cleanup (find expired sessions)
CREATE INDEX idx_sessions_expires ON user_sessions(expires_at)
    WHERE revoked_at IS NULL;

-- Active sessions lookup
CREATE INDEX idx_sessions_active ON user_sessions(user_id, created_at DESC)
    WHERE revoked_at IS NULL AND expires_at > NOW();

-- Last activity tracking
CREATE INDEX idx_sessions_last_activity ON user_sessions(last_activity DESC);

-- IP address tracking (security audit)
CREATE INDEX idx_sessions_ip ON user_sessions(ip_address);

-- ============================================================================
-- 3. CREATE HELPER FUNCTIONS
-- ============================================================================

-- Function: Auto-update last_activity on token verification
CREATE OR REPLACE FUNCTION update_session_activity()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_activity := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Update last_activity when session is accessed
-- (Application should UPDATE session record on each API call)
COMMENT ON FUNCTION update_session_activity() IS
    'Auto-update last_activity timestamp when session is verified';

-- Function: Revoke user session
CREATE OR REPLACE FUNCTION revoke_session(p_session_token VARCHAR)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE user_sessions
    SET revoked_at = NOW()
    WHERE session_token = p_session_token
      AND revoked_at IS NULL;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION revoke_session(VARCHAR) IS
    'Revoke session by token (manual logout)';

-- Function: Revoke all user sessions
CREATE OR REPLACE FUNCTION revoke_all_user_sessions(p_user_id INTEGER)
RETURNS INTEGER AS $$
DECLARE
    revoked_count INTEGER;
BEGIN
    UPDATE user_sessions
    SET revoked_at = NOW()
    WHERE user_id = p_user_id
      AND revoked_at IS NULL;

    GET DIAGNOSTICS revoked_count = ROW_COUNT;
    RETURN revoked_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION revoke_all_user_sessions(INTEGER) IS
    'Revoke all sessions for user (logout all devices)';

-- Function: Clean expired sessions (maintenance)
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM user_sessions
    WHERE expires_at < NOW() - INTERVAL '30 days'; -- Keep for 30 days after expiration for audit

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_expired_sessions() IS
    'Delete expired sessions older than 30 days (run as cron job)';

-- ============================================================================
-- 4. COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE user_sessions IS 'Active user sessions for server-side JWT token management and security';
COMMENT ON COLUMN user_sessions.session_token IS 'SHA256 hash of JWT access token for verification';
COMMENT ON COLUMN user_sessions.refresh_token IS 'SHA256 hash of refresh token (optional)';
COMMENT ON COLUMN user_sessions.device_info IS 'JSONB: {"browser": "Chrome", "os": "Windows 10", "device": "Desktop"}';
COMMENT ON COLUMN user_sessions.session_type IS 'Session type: web (browser), api (API client), mobile (app), device (TV)';
COMMENT ON COLUMN user_sessions.is_active IS 'Computed: TRUE if not revoked and not expired';
COMMENT ON COLUMN user_sessions.last_activity IS 'Last API request timestamp (updated on each token verification)';
COMMENT ON COLUMN user_sessions.revoked_at IS 'Manual logout timestamp (NULL = active)';

-- ============================================================================
-- 5. VERIFICATION QUERY
-- ============================================================================

-- Verify table created
SELECT
    table_name,
    (SELECT count(*) FROM information_schema.columns WHERE table_name = 'user_sessions') as column_count
FROM information_schema.tables
WHERE table_name = 'user_sessions';

-- Verify indexes created
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'user_sessions'
ORDER BY indexname;

-- Verify functions created
SELECT
    proname as function_name,
    pg_get_functiondef(oid) as definition
FROM pg_proc
WHERE proname IN ('update_session_activity', 'revoke_session', 'revoke_all_user_sessions', 'cleanup_expired_sessions');

COMMIT;

-- ============================================================================
-- ROLLBACK SCRIPT (if needed)
-- ============================================================================

-- To rollback this migration:
/*
BEGIN;

-- Drop functions
DROP FUNCTION IF EXISTS update_session_activity();
DROP FUNCTION IF EXISTS revoke_session(VARCHAR);
DROP FUNCTION IF EXISTS revoke_all_user_sessions(INTEGER);
DROP FUNCTION IF EXISTS cleanup_expired_sessions();

-- Drop indexes
DROP INDEX IF EXISTS idx_sessions_user;
DROP INDEX IF EXISTS idx_sessions_organization;
DROP INDEX IF EXISTS idx_sessions_token;
DROP INDEX IF EXISTS idx_sessions_refresh;
DROP INDEX IF EXISTS idx_sessions_expires;
DROP INDEX IF EXISTS idx_sessions_active;
DROP INDEX IF EXISTS idx_sessions_last_activity;
DROP INDEX IF EXISTS idx_sessions_ip;

-- Drop table
DROP TABLE IF EXISTS user_sessions;

COMMIT;
*/

-- ============================================================================
-- USAGE EXAMPLES
-- ============================================================================

-- Create new session (on login)
/*
INSERT INTO user_sessions (
    user_id, organization_id, session_token, ip_address, user_agent,
    device_info, expires_at, session_type
) VALUES (
    123,  -- user_id
    1,    -- organization_id
    'abc123...', -- SHA256(JWT token)
    '192.168.1.100',
    'Mozilla/5.0...',
    '{"browser": "Chrome", "os": "Windows 10"}'::jsonb,
    NOW() + INTERVAL '24 hours',
    'web'
);
*/

-- Verify session (on API request)
/*
SELECT
    s.*,
    u.username,
    u.role,
    o.name as organization_name
FROM user_sessions s
JOIN users u ON u.id = s.user_id
JOIN organizations o ON o.id = s.organization_id
WHERE s.session_token = 'abc123...'
  AND s.revoked_at IS NULL
  AND s.expires_at > NOW();
*/

-- Update last activity
/*
UPDATE user_sessions
SET last_activity = NOW()
WHERE session_token = 'abc123...';
*/

-- Revoke session (logout)
/*
SELECT revoke_session('abc123...');
*/

-- Revoke all user sessions (logout all devices)
/*
SELECT revoke_all_user_sessions(123);
*/

-- Get active sessions for user
/*
SELECT
    id,
    ip_address,
    user_agent,
    device_info->>'browser' as browser,
    device_info->>'os' as os,
    session_type,
    created_at,
    last_activity,
    expires_at
FROM user_sessions
WHERE user_id = 123
  AND revoked_at IS NULL
  AND expires_at > NOW()
ORDER BY last_activity DESC;
*/

-- Clean expired sessions (run as cron job)
/*
SELECT cleanup_expired_sessions();
*/

-- Session statistics
/*
SELECT
    session_type,
    count(*) as total_sessions,
    count(*) FILTER (WHERE revoked_at IS NULL AND expires_at > NOW()) as active_sessions,
    count(*) FILTER (WHERE revoked_at IS NOT NULL) as revoked_sessions,
    count(*) FILTER (WHERE expires_at <= NOW()) as expired_sessions
FROM user_sessions
GROUP BY session_type;
*/

-- ============================================================================
-- CRON JOB SETUP (Cleanup expired sessions daily)
-- ============================================================================

-- Add to cron (run daily at 2 AM):
-- 0 2 * * * docker exec signage-postgres psql -U signage_user -d signage_db -c "SELECT cleanup_expired_sessions();"

-- Or use pg_cron extension (if installed):
/*
SELECT cron.schedule(
    'cleanup-expired-sessions',
    '0 2 * * *', -- Daily at 2 AM
    $$SELECT cleanup_expired_sessions();$$
);
*/

-- ============================================================================
-- Migration Complete
-- ============================================================================

-- To run this migration on server:
-- docker exec -i signage-postgres psql -U signage_user -d signage_db < database/fix-database/migrations/011_create_user_sessions_table.sql
