-- ============================================================================
-- Migration 012: API Keys for Service Account Authentication
-- ============================================================================
-- Source: SDK_INTEGRATION_GUIDE.md - Service Account Authentication
--
-- This migration creates:
-- 1. api_keys - Service account credentials for machine-to-machine auth
--
-- Key Format:
-- - Production: pk_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
-- - Test: pk_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
-- ============================================================================

-- ============================================================================
-- 1. API KEYS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS api_keys (
    key_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    created_by_user_id UUID NOT NULL REFERENCES users(user_id),

    -- Key data (hashed for security)
    key_prefix VARCHAR(12) NOT NULL,  -- First 12 chars for display (e.g., "pk_live_a1b2")
    key_hash VARCHAR(64) NOT NULL,    -- SHA-256 hash of full key

    -- Metadata
    name VARCHAR(100) NOT NULL,
    description TEXT,
    environment VARCHAR(10) NOT NULL DEFAULT 'live',

    -- Permissions/Scopes
    scopes TEXT[] NOT NULL DEFAULT '{}',  -- e.g., ['read:tenants', 'write:decisions']

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    revoked_at TIMESTAMPTZ,
    revoked_by_user_id UUID REFERENCES users(user_id),

    -- Expiration
    expires_at TIMESTAMPTZ,  -- NULL = never expires

    -- Usage tracking
    last_used_at TIMESTAMPTZ,
    last_used_ip VARCHAR(45),  -- IPv6 can be up to 45 chars
    usage_count INTEGER NOT NULL DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT api_keys_hash_unique UNIQUE (key_hash),
    CONSTRAINT api_keys_prefix_unique UNIQUE (key_prefix),
    CONSTRAINT api_keys_check_environment CHECK (
        environment IN ('live', 'test')
    ),
    CONSTRAINT api_keys_check_status CHECK (
        status IN ('active', 'revoked', 'expired')
    ),
    CONSTRAINT api_keys_check_prefix_format CHECK (
        key_prefix ~ '^pk_(live|test)_[a-f0-9]+$'
    )
);

-- Indexes for fast lookups
CREATE INDEX idx_api_keys_tenant ON api_keys(tenant_id);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_prefix ON api_keys(key_prefix);
CREATE INDEX idx_api_keys_user ON api_keys(created_by_user_id);
CREATE INDEX idx_api_keys_status ON api_keys(tenant_id, status);
CREATE INDEX idx_api_keys_environment ON api_keys(tenant_id, environment);

-- Partial index for active keys (most common query)
CREATE INDEX idx_api_keys_active ON api_keys(key_hash)
    WHERE status = 'active';

COMMENT ON TABLE api_keys IS 'Service account credentials for machine-to-machine authentication';
COMMENT ON COLUMN api_keys.key_prefix IS 'First 12 chars for display (e.g., pk_live_a1b2). Full key only shown once at creation.';
COMMENT ON COLUMN api_keys.key_hash IS 'SHA-256 hash of full API key for secure validation';
COMMENT ON COLUMN api_keys.scopes IS 'Permission scopes. Empty array = full access. Format: {action}:{resource}';
COMMENT ON COLUMN api_keys.environment IS 'live = production, test = development/testing';

-- ============================================================================
-- 2. TRIGGER FOR UPDATED_AT
-- ============================================================================

DROP TRIGGER IF EXISTS trigger_update_api_keys_updated_at ON api_keys;
CREATE TRIGGER trigger_update_api_keys_updated_at
    BEFORE UPDATE ON api_keys
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 3. GRANTS (for app_runtime_role)
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_runtime_role') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON api_keys TO app_runtime_role;
    END IF;
END $$;

-- ============================================================================
-- 4. DEFAULT SCOPES REFERENCE (for documentation)
-- ============================================================================

COMMENT ON TABLE api_keys IS E'Service account credentials for machine-to-machine authentication.\n\nAvailable Scopes:\n- read:* - Read access to all resources\n- write:* - Write access to all resources\n- read:tenants - Read tenant information\n- write:tenants - Modify tenant settings\n- read:decisions - Read decisions\n- write:decisions - Create/modify decisions\n- read:rules - Read rules\n- write:rules - Create/modify rules\n- read:workflows - Read workflows\n- write:workflows - Modify workflows\n- admin:* - Full administrative access';

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

COMMENT ON SCHEMA public IS 'ARSAKA_PUGUH SaaS Platform - Migration 012: API Keys for service account authentication';
