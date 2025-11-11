-- Migration 021: Add Device Commands System
-- Phase 4: Remote Device Management
-- Purpose: Allow CMS to send commands to devices (reboot, update content, etc.)

-- ============================================================================
-- TABLE: device_commands
-- ============================================================================
CREATE TABLE IF NOT EXISTS device_commands (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Command details
    command_type VARCHAR(50) NOT NULL, -- 'reboot', 'refresh_content', 'update_settings', 'clear_cache', 'screenshot'
    command_data JSONB DEFAULT '{}', -- Additional command parameters

    -- Status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending', 'sent', 'executed', 'failed'
    priority INTEGER NOT NULL DEFAULT 5, -- 1 (highest) to 10 (lowest)

    -- Execution tracking
    sent_at TIMESTAMP WITH TIME ZONE,
    executed_at TIMESTAMP WITH TIME ZONE,
    failed_at TIMESTAMP WITH TIME ZONE,
    result JSONB, -- Command execution result
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,

    -- Audit tracking
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE, -- Command expires if not executed within time

    -- Indexes
    CONSTRAINT valid_command_type CHECK (command_type IN ('reboot', 'refresh_content', 'update_settings', 'clear_cache', 'screenshot', 'update_playlist')),
    CONSTRAINT valid_status CHECK (status IN ('pending', 'sent', 'executed', 'failed', 'expired')),
    CONSTRAINT valid_priority CHECK (priority BETWEEN 1 AND 10)
);

-- Create indexes for performance
CREATE INDEX idx_device_commands_device_id ON device_commands(device_id);
CREATE INDEX idx_device_commands_organization_id ON device_commands(organization_id);
CREATE INDEX idx_device_commands_status ON device_commands(status);
CREATE INDEX idx_device_commands_created_at ON device_commands(created_at);
CREATE INDEX idx_device_commands_priority ON device_commands(priority);

-- Composite index for getting pending commands
CREATE INDEX idx_device_commands_device_status_priority
ON device_commands(device_id, status, priority DESC, created_at ASC);

-- ============================================================================
-- STORED FUNCTIONS
-- ============================================================================

-- Function: Get pending commands for a device
CREATE OR REPLACE FUNCTION get_pending_device_commands(p_device_id INTEGER)
RETURNS TABLE (
    id INTEGER,
    command_type VARCHAR(50),
    command_data JSONB,
    priority INTEGER,
    created_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.id,
        dc.command_type,
        dc.command_data,
        dc.priority,
        dc.created_at,
        dc.expires_at
    FROM device_commands dc
    WHERE dc.device_id = p_device_id
      AND dc.status = 'pending'
      AND (dc.expires_at IS NULL OR dc.expires_at > NOW())
    ORDER BY dc.priority ASC, dc.created_at ASC
    LIMIT 10; -- Return max 10 commands at a time
END;
$$ LANGUAGE plpgsql;

-- Function: Mark command as executed
CREATE OR REPLACE FUNCTION mark_command_executed(
    p_command_id INTEGER,
    p_result JSONB DEFAULT NULL
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE device_commands
    SET
        status = 'executed',
        executed_at = NOW(),
        result = COALESCE(p_result, '{"status": "success"}'::jsonb),
        updated_at = NOW()
    WHERE id = p_command_id
      AND status IN ('pending', 'sent');

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Function: Mark command as failed
CREATE OR REPLACE FUNCTION mark_command_failed(
    p_command_id INTEGER,
    p_error_message TEXT
)
RETURNS BOOLEAN AS $$
DECLARE
    v_retry_count INTEGER;
    v_max_retries INTEGER;
BEGIN
    -- Get current retry count
    SELECT retry_count, max_retries
    INTO v_retry_count, v_max_retries
    FROM device_commands
    WHERE id = p_command_id;

    -- Increment retry count
    v_retry_count := v_retry_count + 1;

    -- If max retries reached, mark as failed permanently
    IF v_retry_count >= v_max_retries THEN
        UPDATE device_commands
        SET
            status = 'failed',
            failed_at = NOW(),
            retry_count = v_retry_count,
            error_message = p_error_message,
            updated_at = NOW()
        WHERE id = p_command_id;
    ELSE
        -- Otherwise, reset to pending for retry
        UPDATE device_commands
        SET
            status = 'pending',
            retry_count = v_retry_count,
            error_message = p_error_message,
            updated_at = NOW()
        WHERE id = p_command_id;
    END IF;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Function: Expire old pending commands
CREATE OR REPLACE FUNCTION expire_old_commands()
RETURNS INTEGER AS $$
DECLARE
    v_expired_count INTEGER;
BEGIN
    UPDATE device_commands
    SET
        status = 'expired',
        updated_at = NOW()
    WHERE status = 'pending'
      AND expires_at IS NOT NULL
      AND expires_at < NOW();

    GET DIAGNOSTICS v_expired_count = ROW_COUNT;
    RETURN v_expired_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGER: Auto-update updated_at timestamp
-- ============================================================================
CREATE OR REPLACE FUNCTION update_device_commands_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER device_commands_updated_at
    BEFORE UPDATE ON device_commands
    FOR EACH ROW
    EXECUTE FUNCTION update_device_commands_updated_at();

-- ============================================================================
-- COMMENTS
-- ============================================================================
COMMENT ON TABLE device_commands IS 'Commands sent from CMS to devices for remote management';
COMMENT ON COLUMN device_commands.command_type IS 'Type of command: reboot, refresh_content, update_settings, clear_cache, screenshot';
COMMENT ON COLUMN device_commands.command_data IS 'Additional command parameters in JSON format';
COMMENT ON COLUMN device_commands.priority IS 'Command priority: 1 (highest) to 10 (lowest)';
COMMENT ON COLUMN device_commands.retry_count IS 'Number of times command execution was retried';
COMMENT ON COLUMN device_commands.max_retries IS 'Maximum number of retries before marking as failed';
