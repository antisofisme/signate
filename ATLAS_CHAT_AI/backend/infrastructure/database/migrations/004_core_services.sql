-- Migration: 004_core_services
-- Description: Create users, API keys, and audit log tables
-- Created: 2026-01-25
-- Complies: CHAT-LAW-004 (Multi-tenant), CHAT-LAW-006 (Append-only audit)

-- =============================================================================
-- USERS
-- =============================================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(100) NOT NULL REFERENCES tenants(id),
    external_user_id VARCHAR(200) NOT NULL,

    -- Profile
    email VARCHAR(255),
    display_name VARCHAR(200) NOT NULL,
    avatar_url TEXT,
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en',

    -- Role and permissions
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('admin', 'user', 'readonly')),
    custom_permissions JSONB DEFAULT '[]',

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    last_seen_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (tenant_id, external_user_id)
);

CREATE INDEX idx_users_tenant ON users(tenant_id);
CREATE INDEX idx_users_email ON users(tenant_id, email) WHERE email IS NOT NULL;
CREATE INDEX idx_users_active ON users(tenant_id, is_active) WHERE is_active = TRUE;

COMMENT ON TABLE users IS 'Chat users linked to external auth systems';

-- =============================================================================
-- API KEYS
-- =============================================================================

CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(100) NOT NULL REFERENCES tenants(id),

    -- Key identification
    name VARCHAR(200) NOT NULL,
    key_prefix VARCHAR(12) NOT NULL,  -- First 12 chars for display: "chat_abc123..."
    key_hash VARCHAR(64) NOT NULL,    -- SHA256 hash of full key

    -- Permissions
    permissions JSONB DEFAULT '["chat.read", "chat.write"]',
    rate_limit_per_minute INTEGER DEFAULT 100,

    -- Lifecycle
    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,

    -- Audit
    created_by VARCHAR(200) NOT NULL,
    revoked_at TIMESTAMPTZ,
    revoked_by VARCHAR(200),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_api_keys_tenant ON api_keys(tenant_id);
CREATE INDEX idx_api_keys_prefix ON api_keys(key_prefix);
CREATE INDEX idx_api_keys_active ON api_keys(tenant_id, is_active) WHERE is_active = TRUE;

COMMENT ON TABLE api_keys IS 'API keys for programmatic access';
COMMENT ON COLUMN api_keys.key_hash IS 'SHA256 hash of the full API key - key itself is never stored';

-- =============================================================================
-- AUDIT LOGS (APPEND-ONLY per CHAT-LAW-006)
-- =============================================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(100) NOT NULL,

    -- Actor
    actor_type VARCHAR(20) NOT NULL CHECK (actor_type IN ('user', 'api_key', 'system')),
    actor_id VARCHAR(200) NOT NULL,

    -- Action
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(200),

    -- Request context
    request_id VARCHAR(100),
    ip_address VARCHAR(45),  -- IPv6 max length

    -- Details
    details JSONB,
    status VARCHAR(20) DEFAULT 'success' CHECK (status IN ('success', 'failure', 'error')),

    -- Timestamp (NO updated_at - immutable!)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Partitioning by month for large audit tables
-- CREATE TABLE audit_logs (...) PARTITION BY RANGE (created_at);

CREATE INDEX idx_audit_tenant ON audit_logs(tenant_id, created_at DESC);
CREATE INDEX idx_audit_actor ON audit_logs(tenant_id, actor_id, created_at DESC);
CREATE INDEX idx_audit_action ON audit_logs(tenant_id, action, created_at DESC);
CREATE INDEX idx_audit_resource ON audit_logs(tenant_id, resource_type, resource_id);
CREATE INDEX idx_audit_request ON audit_logs(request_id) WHERE request_id IS NOT NULL;

COMMENT ON TABLE audit_logs IS 'Audit log - APPEND ONLY per CHAT-LAW-006';

-- =============================================================================
-- AUDIT LOG IMMUTABILITY (CHAT-LAW-006)
-- =============================================================================

-- Prevent UPDATE on audit_logs
CREATE OR REPLACE FUNCTION prevent_audit_update()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Cannot update audit logs. Audit records are immutable per CHAT-LAW-006.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_audit_immutability
    BEFORE UPDATE ON audit_logs
    FOR EACH ROW
    EXECUTE FUNCTION prevent_audit_update();

-- Prevent DELETE on audit_logs
CREATE OR REPLACE FUNCTION prevent_audit_delete()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Cannot delete audit logs. Audit records are immutable per CHAT-LAW-006.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_audit_no_delete
    BEFORE DELETE ON audit_logs
    FOR EACH ROW
    EXECUTE FUNCTION prevent_audit_delete();

-- =============================================================================
-- UPDATE TRIGGERS
-- =============================================================================

CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
