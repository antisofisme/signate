-- ============================================================================
-- Migration: 014_account_lockout.sql
-- Description: Add account lockout fields for brute force protection
-- Date: 2026-01-28
-- ============================================================================

-- Add lockout fields to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_failed_login_at TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_failed_login_ip VARCHAR(45);

-- Add comments
COMMENT ON COLUMN users.failed_login_attempts IS 'Number of consecutive failed login attempts';
COMMENT ON COLUMN users.locked_until IS 'Account locked until this timestamp (NULL = not locked)';
COMMENT ON COLUMN users.last_failed_login_at IS 'Timestamp of last failed login attempt';
COMMENT ON COLUMN users.last_failed_login_ip IS 'IP address of last failed login attempt';

-- Create index for efficient lockout queries
CREATE INDEX IF NOT EXISTS idx_users_locked_until ON users(locked_until)
WHERE locked_until IS NOT NULL;

-- ============================================================================
-- Account Lockout Policy
-- ============================================================================
-- 5 failures  -> 15 minutes lock
-- 10 failures -> 1 hour lock
-- 15 failures -> 24 hours lock
-- 20 failures -> Permanent lock (requires support)
--
-- Successful login resets the counter
-- Lock expires automatically based on locked_until timestamp
-- ============================================================================

-- Function to check if account is locked
CREATE OR REPLACE FUNCTION is_account_locked(p_user_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    v_locked_until TIMESTAMPTZ;
    v_failed_attempts INTEGER;
BEGIN
    SELECT locked_until, failed_login_attempts
    INTO v_locked_until, v_failed_attempts
    FROM users
    WHERE user_id = p_user_id;

    -- Not found
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;

    -- Permanent lock (20+ failures)
    IF v_failed_attempts >= 20 AND v_locked_until IS NOT NULL THEN
        RETURN TRUE;
    END IF;

    -- Time-based lock
    IF v_locked_until IS NOT NULL AND v_locked_until > NOW() THEN
        RETURN TRUE;
    END IF;

    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- Function to record failed login
CREATE OR REPLACE FUNCTION record_failed_login(
    p_user_id UUID,
    p_ip_address VARCHAR(45)
)
RETURNS TABLE(
    is_locked BOOLEAN,
    lock_duration_minutes INTEGER,
    attempts INTEGER
) AS $$
DECLARE
    v_current_attempts INTEGER;
    v_lock_duration INTERVAL;
BEGIN
    -- Increment failed attempts
    UPDATE users
    SET
        failed_login_attempts = COALESCE(failed_login_attempts, 0) + 1,
        last_failed_login_at = NOW(),
        last_failed_login_ip = p_ip_address
    WHERE user_id = p_user_id
    RETURNING failed_login_attempts INTO v_current_attempts;

    -- Determine lock duration based on attempts
    v_lock_duration := CASE
        WHEN v_current_attempts >= 20 THEN INTERVAL '100 years'  -- Permanent
        WHEN v_current_attempts >= 15 THEN INTERVAL '24 hours'
        WHEN v_current_attempts >= 10 THEN INTERVAL '1 hour'
        WHEN v_current_attempts >= 5 THEN INTERVAL '15 minutes'
        ELSE NULL
    END;

    -- Apply lock if needed
    IF v_lock_duration IS NOT NULL THEN
        UPDATE users
        SET locked_until = NOW() + v_lock_duration
        WHERE user_id = p_user_id;

        RETURN QUERY SELECT
            TRUE,
            EXTRACT(EPOCH FROM v_lock_duration)::INTEGER / 60,
            v_current_attempts;
    ELSE
        RETURN QUERY SELECT FALSE, 0, v_current_attempts;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to reset failed login counter (on successful login)
CREATE OR REPLACE FUNCTION reset_failed_logins(p_user_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE users
    SET
        failed_login_attempts = 0,
        locked_until = NULL,
        last_failed_login_at = NULL,
        last_failed_login_ip = NULL
    WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Function to manually unlock account (for admin/support)
CREATE OR REPLACE FUNCTION admin_unlock_account(p_user_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE users
    SET
        failed_login_attempts = 0,
        locked_until = NULL
    WHERE user_id = p_user_id;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;
