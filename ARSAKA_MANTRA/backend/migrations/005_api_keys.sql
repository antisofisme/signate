-- Migration: 005
-- Description: API Keys management for MCP Server authentication
-- Date: 2025-01-26

BEGIN;

-- ============================================================================
-- API Keys Table
-- For managing MCP Server authentication keys
-- ============================================================================

CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Key metadata
    name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Key storage (NEVER store raw key)
    key_prefix VARCHAR(20) NOT NULL,      -- "mk_A1b2...O5p6" (for display)
    key_hash VARCHAR(64) NOT NULL,         -- SHA-256 hash of full key

    -- Permissions
    permissions JSONB DEFAULT '["read"]',

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,

    -- Audit
    created_by VARCHAR(200) NOT NULL,

    -- Constraints
    CONSTRAINT unique_key_hash UNIQUE (key_hash),
    CONSTRAINT unique_key_prefix UNIQUE (key_prefix)
);

-- Indexes for efficient lookup
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_is_active ON api_keys(is_active);
CREATE INDEX idx_api_keys_created_at ON api_keys(created_at);

-- Comments
COMMENT ON TABLE api_keys IS 'API keys for MCP Server authentication';
COMMENT ON COLUMN api_keys.key_prefix IS 'Masked prefix for display: mk_A1b2...O5p6';
COMMENT ON COLUMN api_keys.key_hash IS 'SHA-256 hash of the full API key';
COMMENT ON COLUMN api_keys.permissions IS 'Array of permissions: read, write, propose, admin';

COMMIT;
