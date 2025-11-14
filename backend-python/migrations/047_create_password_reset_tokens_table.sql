-- Migration: 047
-- Description: Create password_reset_tokens table for database-backed password reset
-- Date: 2025-01-14
-- CRITICAL FIX: Replace in-memory token storage that fails in multi-worker production

BEGIN;

-- Create password reset tokens table
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    consumed_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_password_reset_tokens_hash ON password_reset_tokens(token_hash);
CREATE INDEX idx_password_reset_tokens_expires ON password_reset_tokens(expires_at);
CREATE INDEX idx_password_reset_tokens_user ON password_reset_tokens(user_id);

-- Comments
COMMENT ON TABLE password_reset_tokens IS 'Database-backed password reset tokens (Fix P0-7)';
COMMENT ON COLUMN password_reset_tokens.token_hash IS 'SHA256 hash of reset token';
COMMENT ON COLUMN password_reset_tokens.consumed_at IS 'Timestamp when token was used (prevents reuse)';

COMMIT;
