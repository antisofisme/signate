-- ============================================================================
-- Migration: 015_security_audit_log.sql
-- Description: Security audit log for compliance and incident response
-- Date: 2026-01-28
-- ============================================================================

-- Security audit log table
CREATE TABLE IF NOT EXISTS security_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Event classification
    event_type VARCHAR(50) NOT NULL,  -- login_success, login_failure, permission_denied, etc.
    event_category VARCHAR(30) NOT NULL,  -- authentication, authorization, data_access, admin_action
    severity VARCHAR(10) NOT NULL DEFAULT 'info',  -- debug, info, warning, error, critical

    -- Actor information
    user_id UUID,
    user_email VARCHAR(255),
    tenant_id UUID,

    -- Request context
    ip_address VARCHAR(45),
    user_agent TEXT,
    request_id VARCHAR(50),
    session_id VARCHAR(100),

    -- Resource being accessed
    resource_type VARCHAR(50),  -- user, tenant, decision, api_key, etc.
    resource_id UUID,
    action VARCHAR(30),  -- create, read, update, delete, login, logout, etc.

    -- Outcome
    status VARCHAR(20) NOT NULL,  -- success, failure, blocked, denied
    error_code VARCHAR(50),
    error_message TEXT,

    -- Additional context (flexible JSON)
    details JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    -- Constraints
    CONSTRAINT valid_severity CHECK (severity IN ('debug', 'info', 'warning', 'error', 'critical')),
    CONSTRAINT valid_status CHECK (status IN ('success', 'failure', 'blocked', 'denied', 'pending'))
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_security_audit_user_time
    ON security_audit_log(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_security_audit_tenant_time
    ON security_audit_log(tenant_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_security_audit_event_type
    ON security_audit_log(event_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_security_audit_event_category
    ON security_audit_log(event_category, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_security_audit_ip
    ON security_audit_log(ip_address, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_security_audit_severity
    ON security_audit_log(severity, created_at DESC)
    WHERE severity IN ('warning', 'error', 'critical');

CREATE INDEX IF NOT EXISTS idx_security_audit_status
    ON security_audit_log(status, created_at DESC)
    WHERE status != 'success';

CREATE INDEX IF NOT EXISTS idx_security_audit_resource
    ON security_audit_log(resource_type, resource_id);

-- Comments
COMMENT ON TABLE security_audit_log IS 'Security-focused audit log for compliance, monitoring, and incident response';
COMMENT ON COLUMN security_audit_log.event_type IS 'Specific event type (login_success, permission_denied, etc.)';
COMMENT ON COLUMN security_audit_log.event_category IS 'Category of event (authentication, authorization, data_access, admin_action)';
COMMENT ON COLUMN security_audit_log.severity IS 'Log severity level (debug, info, warning, error, critical)';
COMMENT ON COLUMN security_audit_log.details IS 'Additional context as JSON (geolocation, device info, etc.)';

-- ============================================================================
-- Event Types Reference
-- ============================================================================
-- Authentication:
--   login_success, login_failure, logout, token_refresh, mfa_success, mfa_failure
--   password_change, password_reset_request, password_reset_complete
--   account_locked, account_unlocked
--
-- Authorization:
--   permission_denied, role_change, scope_exceeded
--
-- Data Access:
--   data_export, bulk_read, sensitive_access
--
-- Admin Actions:
--   user_created, user_deleted, user_suspended
--   api_key_created, api_key_revoked
--   tenant_created, tenant_deleted, member_invited, member_removed
--
-- Security Events:
--   suspicious_activity, rate_limit_exceeded, invalid_token
--   session_hijack_suspected, impossible_travel_detected
-- ============================================================================

-- Function to log security event (for use in other migrations/code)
CREATE OR REPLACE FUNCTION log_security_event(
    p_event_type VARCHAR(50),
    p_event_category VARCHAR(30),
    p_user_id UUID DEFAULT NULL,
    p_tenant_id UUID DEFAULT NULL,
    p_ip_address VARCHAR(45) DEFAULT NULL,
    p_resource_type VARCHAR(50) DEFAULT NULL,
    p_resource_id UUID DEFAULT NULL,
    p_action VARCHAR(30) DEFAULT NULL,
    p_status VARCHAR(20) DEFAULT 'success',
    p_severity VARCHAR(10) DEFAULT 'info',
    p_details JSONB DEFAULT '{}'
)
RETURNS UUID AS $$
DECLARE
    v_log_id UUID;
BEGIN
    INSERT INTO security_audit_log (
        event_type,
        event_category,
        user_id,
        tenant_id,
        ip_address,
        resource_type,
        resource_id,
        action,
        status,
        severity,
        details
    ) VALUES (
        p_event_type,
        p_event_category,
        p_user_id,
        p_tenant_id,
        p_ip_address,
        p_resource_type,
        p_resource_id,
        p_action,
        p_status,
        p_severity,
        p_details
    )
    RETURNING id INTO v_log_id;

    RETURN v_log_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Data Retention Policy
-- ============================================================================
-- Security audit logs should be retained for compliance:
-- - GDPR: No specific requirement, but 7 years recommended
-- - SOC 2: 1 year minimum
-- - PCI DSS: 1 year online, 1 year archived
--
-- Recommendation: 7 years retention with archival after 1 year

-- Create partition for efficient retention (optional - for high volume)
-- Note: This is a template. Implement if log volume requires it.
-- CREATE TABLE security_audit_log_2026_01 PARTITION OF security_audit_log
--     FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
