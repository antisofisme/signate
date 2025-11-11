-- ============================================================================
-- Migration 021: Device Commands (Remote Control) - PHASE 4
-- ============================================================================
-- Purpose: Enable remote command execution on devices for Phase 4
-- Impact: New table for command queue and tracking
-- Risk: Low - Only adds new table, no changes to existing schema
-- Phase: 4 - Device Management
-- Created: 2025-11-10
-- ============================================================================

BEGIN;

-- ============================================================================
-- Step 1: Device Commands Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS device_commands (
  id SERIAL PRIMARY KEY,
  device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
  organization_id INTEGER NOT NULL REFERENCES organizations(id),

  -- Command details
  command_type VARCHAR(50) NOT NULL, -- 'reboot', 'screenshot', 'update_content', 'clear_cache', 'refresh_playlist'
  payload JSONB, -- Command-specific parameters

  -- Status tracking
  status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'sent', 'executed', 'failed'
  result JSONB, -- Execution result

  -- User tracking
  created_by INTEGER REFERENCES users(id),

  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),
  sent_at TIMESTAMP,
  executed_at TIMESTAMP,
  failed_at TIMESTAMP,

  -- Error handling
  error_message TEXT,
  retry_count INTEGER DEFAULT 0,
  max_retries INTEGER DEFAULT 3
);

-- ============================================================================
-- Step 2: Indexes for Performance
-- ============================================================================

CREATE INDEX idx_device_commands_device ON device_commands(device_id);
CREATE INDEX idx_device_commands_org ON device_commands(organization_id);
CREATE INDEX idx_device_commands_status ON device_commands(status);
CREATE INDEX idx_device_commands_created ON device_commands(created_at DESC);
CREATE INDEX idx_device_commands_type ON device_commands(command_type);

-- Composite index for pending commands query
CREATE INDEX idx_device_commands_device_status ON device_commands(device_id, status) WHERE status IN ('pending', 'sent');

-- ============================================================================
-- Step 3: Helper Functions
-- ============================================================================

-- Function to get pending commands for a device
CREATE OR REPLACE FUNCTION get_pending_device_commands(p_device_id INTEGER)
RETURNS TABLE (
  command_id INTEGER,
  command_type VARCHAR,
  payload JSONB,
  created_at TIMESTAMP
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    id,
    dc.command_type,
    dc.payload,
    dc.created_at
  FROM device_commands dc
  WHERE dc.device_id = p_device_id
    AND dc.status IN ('pending', 'sent')
  ORDER BY dc.created_at ASC;
END;
$$ LANGUAGE plpgsql;

-- Function to mark command as executed
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
    result = p_result
  WHERE id = p_command_id
    AND status IN ('pending', 'sent');

  RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Function to mark command as failed
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
      error_message = p_error_message,
      retry_count = v_retry_count
    WHERE id = p_command_id;
  ELSE
    -- Otherwise, reset to pending for retry
    UPDATE device_commands
    SET
      status = 'pending',
      error_message = p_error_message,
      retry_count = v_retry_count,
      sent_at = NULL
    WHERE id = p_command_id;
  END IF;

  RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up old commands (older than 30 days)
CREATE OR REPLACE FUNCTION cleanup_old_device_commands()
RETURNS INTEGER AS $$
DECLARE
  v_deleted_count INTEGER;
BEGIN
  DELETE FROM device_commands
  WHERE created_at < NOW() - INTERVAL '30 days'
    AND status IN ('executed', 'failed');

  GET DIAGNOSTICS v_deleted_count = ROW_COUNT;

  RETURN v_deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMIT;

-- ============================================================================
-- ROLLBACK PROCEDURE
-- ============================================================================
-- To rollback this migration:
-- BEGIN;
-- DROP TABLE IF EXISTS device_commands CASCADE;
-- DROP FUNCTION IF EXISTS get_pending_device_commands(INTEGER);
-- DROP FUNCTION IF EXISTS mark_command_executed(INTEGER, JSONB);
-- DROP FUNCTION IF EXISTS mark_command_failed(INTEGER, TEXT);
-- DROP FUNCTION IF EXISTS cleanup_old_device_commands();
-- COMMIT;
-- ============================================================================
