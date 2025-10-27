-- Migration: Create Activity Logs System
-- Date: 2025-10-26
-- Description: Add activity logging for tracking system events and user actions
-- Phase: Dashboard Improvement - FASE 3.1

-- ===========================================================================
-- PART 1: Create activity_logs table
-- ===========================================================================

CREATE TABLE IF NOT EXISTS activity_logs (
    id SERIAL PRIMARY KEY,

    -- Timestamp
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- User who performed the action (nullable for system/device actions)
    user_id INTEGER,

    -- Action classification
    action_type VARCHAR(50) NOT NULL,

    -- Entity information
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER,
    entity_name VARCHAR(255),

    -- Additional details as JSON
    details JSONB,

    -- Request metadata
    ip_address VARCHAR(45),
    user_agent TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- ===========================================================================
-- PART 2: Create indexes for performance
-- ===========================================================================

-- Primary query indexes
CREATE INDEX IF NOT EXISTS idx_activity_logs_timestamp
ON activity_logs(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_activity_logs_user
ON activity_logs(user_id)
WHERE user_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_activity_logs_action_type
ON activity_logs(action_type);

CREATE INDEX IF NOT EXISTS idx_activity_logs_entity
ON activity_logs(entity_type, entity_id);

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_timestamp
ON activity_logs(user_id, timestamp DESC)
WHERE user_id IS NOT NULL;

-- JSONB index for details queries (GIN index)
CREATE INDEX IF NOT EXISTS idx_activity_logs_details
ON activity_logs USING GIN (details);

-- ===========================================================================
-- PART 3: Add comments for documentation
-- ===========================================================================

COMMENT ON TABLE activity_logs IS 'System activity and audit log for tracking user actions and system events';

COMMENT ON COLUMN activity_logs.timestamp IS 'When the action occurred';
COMMENT ON COLUMN activity_logs.user_id IS 'User who performed the action (NULL for system/device actions)';
COMMENT ON COLUMN activity_logs.action_type IS 'Type of action (e.g., DEVICE_REGISTERED, CONTENT_UPLOADED)';
COMMENT ON COLUMN activity_logs.entity_type IS 'Type of entity affected (e.g., device, content, playlist)';
COMMENT ON COLUMN activity_logs.entity_id IS 'ID of the affected entity';
COMMENT ON COLUMN activity_logs.entity_name IS 'Name/title of the affected entity for quick reference';
COMMENT ON COLUMN activity_logs.details IS 'Additional metadata as JSON (e.g., old/new values, error messages)';
COMMENT ON COLUMN activity_logs.ip_address IS 'IP address of the request (IPv4 or IPv6)';
COMMENT ON COLUMN activity_logs.user_agent IS 'User agent string from request';

-- ===========================================================================
-- PART 4: Create helper function for automatic log cleanup
-- ===========================================================================

-- Function to delete old activity logs (retention policy)
CREATE OR REPLACE FUNCTION cleanup_old_activity_logs(retention_days INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM activity_logs
    WHERE timestamp < NOW() - (retention_days || ' days')::INTERVAL;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_old_activity_logs IS 'Cleanup activity logs older than specified days (default: 90 days)';

-- ===========================================================================
-- VERIFICATION QUERIES (for testing)
-- ===========================================================================

-- Uncomment these to verify the migration worked correctly

-- Check table structure
-- SELECT column_name, data_type, column_default, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'activity_logs'
-- ORDER BY ordinal_position;

-- Check indexes
-- SELECT indexname, indexdef
-- FROM pg_indexes
-- WHERE tablename = 'activity_logs';

-- Test cleanup function
-- SELECT cleanup_old_activity_logs(90);
