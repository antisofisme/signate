-- Migration 012: Enhanced Command System with Security Controls
-- Phase 4.3: Device Command Extensions
-- Date: 2025-10-28

-- =============================================================================
-- ENHANCED DEVICE COMMANDS TABLE
-- =============================================================================

-- Drop existing table if upgrading from basic version
-- DROP TABLE IF EXISTS device_commands CASCADE;

-- Enhanced device commands table with full security features
CREATE TABLE IF NOT EXISTS device_commands_enhanced (
    -- Primary Key
    id SERIAL PRIMARY KEY,

    -- Device Reference
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,

    -- Command Information
    command_type VARCHAR(50) NOT NULL,
    parameters JSONB DEFAULT '{}'::jsonb,

    -- Status Tracking
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),

    -- Execution Timeline
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    scheduled_at TIMESTAMP,
    sent_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    expires_at TIMESTAMP,

    -- Results & Error Handling
    result JSONB,
    error_message TEXT,
    exit_code INTEGER,
    execution_time FLOAT,

    -- Retry Mechanism
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,

    -- Security & Audit
    created_by INTEGER REFERENCES users(id),
    risk_level VARCHAR(20) DEFAULT 'low',
    requires_2fa BOOLEAN DEFAULT false,
    requires_approval BOOLEAN DEFAULT false,
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMP,

    -- Request Context
    reason TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Indexes for performance
    CONSTRAINT valid_status CHECK (status IN (
        'pending', 'sent', 'running', 'completed', 'failed', 'cancelled', 'expired'
    )),
    CONSTRAINT valid_risk_level CHECK (risk_level IN (
        'low', 'medium', 'high', 'critical'
    ))
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_device_commands_enhanced_device ON device_commands_enhanced(device_id);
CREATE INDEX IF NOT EXISTS idx_device_commands_enhanced_status ON device_commands_enhanced(status);
CREATE INDEX IF NOT EXISTS idx_device_commands_enhanced_type ON device_commands_enhanced(command_type);
CREATE INDEX IF NOT EXISTS idx_device_commands_enhanced_created ON device_commands_enhanced(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_device_commands_enhanced_scheduled ON device_commands_enhanced(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_device_commands_enhanced_expires ON device_commands_enhanced(expires_at);
CREATE INDEX IF NOT EXISTS idx_device_commands_enhanced_created_by ON device_commands_enhanced(created_by);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_device_commands_enhanced_device_status
    ON device_commands_enhanced(device_id, status);
CREATE INDEX IF NOT EXISTS idx_device_commands_enhanced_device_created
    ON device_commands_enhanced(device_id, created_at DESC);

-- JSONB indexes for parameter searches
CREATE INDEX IF NOT EXISTS idx_device_commands_enhanced_parameters
    ON device_commands_enhanced USING gin(parameters);
CREATE INDEX IF NOT EXISTS idx_device_commands_enhanced_result
    ON device_commands_enhanced USING gin(result);


-- =============================================================================
-- COMMAND PERMISSIONS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS command_permissions (
    id SERIAL PRIMARY KEY,

    -- User/Role Reference
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50),

    -- Command Type
    command_type VARCHAR(50) NOT NULL,

    -- Permissions
    can_execute BOOLEAN DEFAULT true,
    requires_2fa BOOLEAN DEFAULT false,
    requires_approval BOOLEAN DEFAULT false,

    -- Rate Limiting (per user/role)
    rate_limit INTEGER DEFAULT 10,  -- requests per minute

    -- Metadata
    granted_by INTEGER REFERENCES users(id),
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,

    -- Constraints
    CONSTRAINT unique_user_command UNIQUE(user_id, command_type),
    CONSTRAINT unique_role_command UNIQUE(role, command_type),
    CONSTRAINT user_or_role CHECK (
        (user_id IS NOT NULL AND role IS NULL) OR
        (user_id IS NULL AND role IS NOT NULL)
    )
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_command_permissions_user ON command_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_command_permissions_role ON command_permissions(role);
CREATE INDEX IF NOT EXISTS idx_command_permissions_type ON command_permissions(command_type);


-- =============================================================================
-- COMMAND AUDIT LOG TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS command_audit_log (
    id SERIAL PRIMARY KEY,

    -- Command Reference
    command_id INTEGER REFERENCES device_commands_enhanced(id) ON DELETE CASCADE,

    -- Event Information
    event_type VARCHAR(50) NOT NULL,  -- created, sent, executed, failed, cancelled, retried
    event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    -- User Context
    user_id INTEGER REFERENCES users(id),
    username VARCHAR(100),

    -- Request Context
    ip_address VARCHAR(45),
    user_agent TEXT,

    -- Event Details
    details JSONB DEFAULT '{}'::jsonb,
    previous_status VARCHAR(20),
    new_status VARCHAR(20),

    -- Security Flags
    security_event BOOLEAN DEFAULT false,  -- Flag for security-relevant events

    CONSTRAINT valid_event_type CHECK (event_type IN (
        'created', 'sent', 'started', 'executed', 'failed', 'cancelled', 'expired', 'retried', 'approved', 'rejected'
    ))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_command_audit_log_command ON command_audit_log(command_id);
CREATE INDEX IF NOT EXISTS idx_command_audit_log_timestamp ON command_audit_log(event_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_command_audit_log_user ON command_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_command_audit_log_event_type ON command_audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_command_audit_log_security ON command_audit_log(security_event)
    WHERE security_event = true;

-- JSONB index for event details
CREATE INDEX IF NOT EXISTS idx_command_audit_log_details
    ON command_audit_log USING gin(details);


-- =============================================================================
-- COMMAND BATCHES TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS command_batches (
    id SERIAL PRIMARY KEY,

    -- Batch Information
    batch_id UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,
    batch_name VARCHAR(255),

    -- Command Configuration
    command_type VARCHAR(50) NOT NULL,
    parameters JSONB DEFAULT '{}'::jsonb,

    -- Target Devices
    target_devices INTEGER[] NOT NULL,

    -- Execution Configuration
    execution_mode VARCHAR(20) DEFAULT 'parallel' CHECK (execution_mode IN ('parallel', 'sequential')),
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),

    -- Status Tracking
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    scheduled_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- Results Summary
    total_devices INTEGER NOT NULL,
    successful_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    cancelled_count INTEGER DEFAULT 0,

    -- Command IDs (array of created command IDs)
    command_ids INTEGER[],

    -- User Context
    created_by INTEGER REFERENCES users(id),
    reason TEXT,

    CONSTRAINT valid_batch_status CHECK (status IN (
        'pending', 'running', 'completed', 'partial', 'failed', 'cancelled'
    ))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_command_batches_batch_id ON command_batches(batch_id);
CREATE INDEX IF NOT EXISTS idx_command_batches_created ON command_batches(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_command_batches_status ON command_batches(status);
CREATE INDEX IF NOT EXISTS idx_command_batches_created_by ON command_batches(created_by);

-- JSONB index for parameters
CREATE INDEX IF NOT EXISTS idx_command_batches_parameters
    ON command_batches USING gin(parameters);


-- =============================================================================
-- COMMAND SCHEDULES TABLE (Future Feature)
-- =============================================================================

CREATE TABLE IF NOT EXISTS command_schedules (
    id SERIAL PRIMARY KEY,

    -- Schedule Information
    schedule_name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Command Configuration
    command_type VARCHAR(50) NOT NULL,
    parameters JSONB DEFAULT '{}'::jsonb,

    -- Target Selection
    target_type VARCHAR(20) NOT NULL CHECK (target_type IN ('device', 'tag', 'all')),
    target_ids INTEGER[],  -- Device IDs or Tag IDs

    -- Schedule Configuration
    cron_expression VARCHAR(100),  -- e.g., '0 9 * * *' (daily at 9am)
    timezone VARCHAR(50) DEFAULT 'UTC',
    enabled BOOLEAN DEFAULT true,

    -- Execution History
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    total_runs INTEGER DEFAULT 0,
    successful_runs INTEGER DEFAULT 0,
    failed_runs INTEGER DEFAULT 0,

    -- Metadata
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_target_type_with_ids CHECK (
        (target_type = 'all' AND target_ids IS NULL) OR
        (target_type != 'all' AND target_ids IS NOT NULL)
    )
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_command_schedules_enabled ON command_schedules(enabled)
    WHERE enabled = true;
CREATE INDEX IF NOT EXISTS idx_command_schedules_next_run ON command_schedules(next_run_at)
    WHERE enabled = true;
CREATE INDEX IF NOT EXISTS idx_command_schedules_created_by ON command_schedules(created_by);


-- =============================================================================
-- VIEWS FOR REPORTING
-- =============================================================================

-- Active commands view (pending + sent + running)
CREATE OR REPLACE VIEW v_active_commands AS
SELECT
    c.*,
    d.device_name,
    d.device_type,
    d.status as device_status,
    u.username as created_by_username
FROM device_commands_enhanced c
LEFT JOIN devices d ON c.device_id = d.id
LEFT JOIN users u ON c.created_by = u.id
WHERE c.status IN ('pending', 'sent', 'running')
ORDER BY c.priority ASC, c.created_at ASC;

-- Command statistics by device
CREATE OR REPLACE VIEW v_command_stats_by_device AS
SELECT
    device_id,
    COUNT(*) as total_commands,
    COUNT(*) FILTER (WHERE status = 'pending') as pending_count,
    COUNT(*) FILTER (WHERE status = 'running') as running_count,
    COUNT(*) FILTER (WHERE status = 'completed') as completed_count,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_count,
    COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled_count,
    AVG(execution_time) FILTER (WHERE execution_time IS NOT NULL) as avg_execution_time,
    MAX(created_at) as last_command_at
FROM device_commands_enhanced
GROUP BY device_id;

-- Command statistics by type
CREATE OR REPLACE VIEW v_command_stats_by_type AS
SELECT
    command_type,
    risk_level,
    COUNT(*) as total_commands,
    COUNT(*) FILTER (WHERE status = 'completed') as success_count,
    COUNT(*) FILTER (WHERE status = 'failed') as failure_count,
    ROUND(
        COUNT(*) FILTER (WHERE status = 'completed')::numeric /
        NULLIF(COUNT(*), 0) * 100,
        2
    ) as success_rate,
    AVG(execution_time) FILTER (WHERE execution_time IS NOT NULL) as avg_execution_time,
    MAX(created_at) as last_executed_at
FROM device_commands_enhanced
GROUP BY command_type, risk_level;

-- Recent audit events
CREATE OR REPLACE VIEW v_recent_audit_events AS
SELECT
    a.*,
    c.command_type,
    c.device_id,
    d.device_name,
    u.username
FROM command_audit_log a
LEFT JOIN device_commands_enhanced c ON a.command_id = c.id
LEFT JOIN devices d ON c.device_id = d.id
LEFT JOIN users u ON a.user_id = u.id
ORDER BY a.event_timestamp DESC
LIMIT 1000;


-- =============================================================================
-- FUNCTIONS & TRIGGERS
-- =============================================================================

-- Function to auto-expire old commands
CREATE OR REPLACE FUNCTION expire_old_commands()
RETURNS INTEGER AS $$
DECLARE
    expired_count INTEGER;
BEGIN
    UPDATE device_commands_enhanced
    SET status = 'expired'
    WHERE status IN ('pending', 'sent')
        AND expires_at < CURRENT_TIMESTAMP
        AND expires_at IS NOT NULL;

    GET DIAGNOSTICS expired_count = ROW_COUNT;
    RETURN expired_count;
END;
$$ LANGUAGE plpgsql;

-- Function to create audit log entry on command status change
CREATE OR REPLACE FUNCTION log_command_status_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Only log if status changed
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO command_audit_log (
            command_id,
            event_type,
            previous_status,
            new_status,
            details,
            security_event
        ) VALUES (
            NEW.id,
            CASE
                WHEN NEW.status = 'sent' THEN 'sent'
                WHEN NEW.status = 'running' THEN 'started'
                WHEN NEW.status = 'completed' THEN 'executed'
                WHEN NEW.status = 'failed' THEN 'failed'
                WHEN NEW.status = 'cancelled' THEN 'cancelled'
                WHEN NEW.status = 'expired' THEN 'expired'
                ELSE 'status_changed'
            END,
            OLD.status,
            NEW.status,
            jsonb_build_object(
                'command_type', NEW.command_type,
                'device_id', NEW.device_id,
                'error_message', NEW.error_message
            ),
            NEW.risk_level = 'critical' OR NEW.risk_level = 'high'
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for audit logging
DROP TRIGGER IF EXISTS trg_command_status_change ON device_commands_enhanced;
CREATE TRIGGER trg_command_status_change
    AFTER UPDATE ON device_commands_enhanced
    FOR EACH ROW
    EXECUTE FUNCTION log_command_status_change();

-- Function to update batch statistics
CREATE OR REPLACE FUNCTION update_batch_statistics()
RETURNS TRIGGER AS $$
BEGIN
    -- Update batch counts when command status changes
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        UPDATE command_batches
        SET
            successful_count = (
                SELECT COUNT(*)
                FROM device_commands_enhanced
                WHERE id = ANY(command_ids)
                AND status = 'completed'
            ),
            failed_count = (
                SELECT COUNT(*)
                FROM device_commands_enhanced
                WHERE id = ANY(command_ids)
                AND status = 'failed'
            ),
            cancelled_count = (
                SELECT COUNT(*)
                FROM device_commands_enhanced
                WHERE id = ANY(command_ids)
                AND status = 'cancelled'
            ),
            status = CASE
                WHEN (
                    SELECT COUNT(*)
                    FROM device_commands_enhanced
                    WHERE id = ANY(command_ids)
                    AND status IN ('completed', 'failed', 'cancelled')
                ) = total_devices THEN 'completed'
                WHEN (
                    SELECT COUNT(*)
                    FROM device_commands_enhanced
                    WHERE id = ANY(command_ids)
                    AND status IN ('running', 'sent')
                ) > 0 THEN 'running'
                ELSE status
            END
        WHERE NEW.id = ANY(command_ids);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for batch statistics
DROP TRIGGER IF EXISTS trg_update_batch_stats ON device_commands_enhanced;
CREATE TRIGGER trg_update_batch_stats
    AFTER UPDATE ON device_commands_enhanced
    FOR EACH ROW
    EXECUTE FUNCTION update_batch_statistics();


-- =============================================================================
-- DEFAULT PERMISSIONS
-- =============================================================================

-- Insert default command permissions for admin role
INSERT INTO command_permissions (role, command_type, can_execute, requires_2fa, requires_approval, rate_limit)
VALUES
    ('admin', 'volume', true, false, false, 10),
    ('admin', 'brightness', true, false, false, 10),
    ('admin', 'screenshot', true, false, false, 5),
    ('admin', 'network_test', true, false, false, 5),
    ('admin', 'clear_cache', true, false, false, 5),
    ('admin', 'reload', true, false, false, 5),
    ('admin', 'refresh', true, false, false, 5),
    ('admin', 'reboot', true, false, false, 3),
    ('admin', 'update', true, true, false, 1),
    ('admin', 'shell', true, true, true, 1),
    ('admin', 'reset', true, false, false, 3)
ON CONFLICT (role, command_type) DO NOTHING;

-- Insert default permissions for operator role
INSERT INTO command_permissions (role, command_type, can_execute, requires_2fa, requires_approval, rate_limit)
VALUES
    ('operator', 'volume', true, false, false, 10),
    ('operator', 'brightness', true, false, false, 10),
    ('operator', 'screenshot', true, false, false, 5),
    ('operator', 'network_test', true, false, false, 5),
    ('operator', 'clear_cache', true, false, false, 5),
    ('operator', 'reload', true, false, false, 5),
    ('operator', 'refresh', true, false, false, 5),
    ('operator', 'reset', true, false, false, 3)
ON CONFLICT (role, command_type) DO NOTHING;

-- Insert default permissions for editor role
INSERT INTO command_permissions (role, command_type, can_execute, requires_2fa, requires_approval, rate_limit)
VALUES
    ('editor', 'volume', true, false, false, 10),
    ('editor', 'brightness', true, false, false, 10),
    ('editor', 'screenshot', true, false, false, 5)
ON CONFLICT (role, command_type) DO NOTHING;


-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE device_commands_enhanced IS 'Enhanced device command queue with security controls and audit logging';
COMMENT ON TABLE command_permissions IS 'Role-based command permissions with 2FA and approval requirements';
COMMENT ON TABLE command_audit_log IS 'Comprehensive audit trail for all command operations';
COMMENT ON TABLE command_batches IS 'Batch command execution tracking for multiple devices';
COMMENT ON TABLE command_schedules IS 'Scheduled/recurring command execution (cron-like)';

COMMENT ON COLUMN device_commands_enhanced.risk_level IS 'Security risk classification: low, medium, high, critical';
COMMENT ON COLUMN device_commands_enhanced.requires_2fa IS 'Whether this command requires 2FA verification';
COMMENT ON COLUMN device_commands_enhanced.requires_approval IS 'Whether this command requires manual approval';
COMMENT ON COLUMN command_audit_log.security_event IS 'Flag for security-relevant events requiring review';
