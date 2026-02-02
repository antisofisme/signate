-- Migration: 006
-- Description: Add outbox pattern columns to event_log for reliable event publishing
-- Date: 2026-01-24
-- Phase: 3
-- Source: Phase 3 Requirements - EVENT BUS INFRASTRUCTURE
--
-- CRITICAL: This migration ONLY adds columns for outbox pattern.
-- It DOES NOT change any existing behavior or constraints.
-- Events are still persisted in same transaction as decision/workflow.

-- =============================================================================
-- OUTBOX PATTERN COLUMNS
-- =============================================================================

BEGIN;

-- Add outbox columns to event_log
-- These columns track publish status WITHOUT affecting event immutability

ALTER TABLE event_log
ADD COLUMN IF NOT EXISTS published_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS publish_attempts INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_publish_error TEXT,
ADD COLUMN IF NOT EXISTS dlq_at TIMESTAMP WITH TIME ZONE;

-- Index for outbox poller: find unpublished events efficiently
-- Query pattern: WHERE published_at IS NULL AND dlq_at IS NULL ORDER BY recorded_at ASC LIMIT N
CREATE INDEX IF NOT EXISTS idx_event_log_outbox_unpublished
ON event_log(recorded_at ASC)
WHERE published_at IS NULL AND dlq_at IS NULL;

-- Index for DLQ monitoring
CREATE INDEX IF NOT EXISTS idx_event_log_dlq
ON event_log(dlq_at DESC)
WHERE dlq_at IS NOT NULL;

-- Index for retry backoff calculation
CREATE INDEX IF NOT EXISTS idx_event_log_retry_candidates
ON event_log(publish_attempts, recorded_at ASC)
WHERE published_at IS NULL AND dlq_at IS NULL AND publish_attempts > 0;

-- Comments
COMMENT ON COLUMN event_log.published_at IS 'Timestamp when event was successfully published to event bus (NULL = not published)';
COMMENT ON COLUMN event_log.publish_attempts IS 'Number of publish attempts (0 = never tried, used for backoff calculation)';
COMMENT ON COLUMN event_log.last_publish_error IS 'Last publish error message (for diagnostics)';
COMMENT ON COLUMN event_log.dlq_at IS 'Timestamp when event was moved to dead-letter queue (NULL = not in DLQ)';

-- =============================================================================
-- OUTBOX CONFIGURATION TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS event_outbox_config (
    config_key VARCHAR(64) PRIMARY KEY,
    config_value JSONB NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    CONSTRAINT config_key_not_empty CHECK (length(config_key) > 0)
);

-- Insert default configuration
INSERT INTO event_outbox_config (config_key, config_value)
VALUES
    ('poller', '{"batch_size": 100, "poll_interval_ms": 1000, "enabled": true}'::jsonb),
    ('retry', '{"max_attempts": 5, "base_delay_ms": 1000, "max_delay_ms": 60000, "backoff_multiplier": 2}'::jsonb),
    ('dlq', '{"enabled": true, "alert_threshold": 100}'::jsonb)
ON CONFLICT (config_key) DO NOTHING;

COMMENT ON TABLE event_outbox_config IS 'Configuration for event outbox poller, retry, and DLQ';

-- =============================================================================
-- DEAD LETTER QUEUE TABLE (for persistent DLQ storage)
-- =============================================================================

CREATE TABLE IF NOT EXISTS event_dlq (
    dlq_entry_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES event_log(event_id) ON DELETE RESTRICT,
    tenant_id UUID NOT NULL,
    event_type VARCHAR(256) NOT NULL,
    moved_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    failure_reason TEXT NOT NULL,
    total_attempts INTEGER NOT NULL,
    last_error TEXT,
    reprocessed_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT dlq_unique_event UNIQUE (event_id)
);

CREATE INDEX IF NOT EXISTS idx_event_dlq_tenant_moved ON event_dlq(tenant_id, moved_at DESC);
CREATE INDEX IF NOT EXISTS idx_event_dlq_reprocessed ON event_dlq(reprocessed_at) WHERE reprocessed_at IS NULL;

COMMENT ON TABLE event_dlq IS 'Dead-letter queue for events that failed to publish after max retries';

-- =============================================================================
-- GRANT PERMISSIONS TO app_runtime_role
-- =============================================================================

-- app_runtime_role can SELECT and UPDATE (for outbox status) event_log
-- NOTE: INSERT already granted in migration 004
GRANT SELECT, UPDATE (published_at, publish_attempts, last_publish_error, dlq_at)
ON event_log TO app_runtime_role;

GRANT SELECT, INSERT, UPDATE ON event_outbox_config TO app_runtime_role;
GRANT SELECT, INSERT, UPDATE ON event_dlq TO app_runtime_role;

-- =============================================================================
-- RECORD MIGRATION
-- =============================================================================

INSERT INTO schema_migrations (migration_id, migration_name)
VALUES (6, '006_outbox_pattern');

COMMIT;

-- =============================================================================
-- END OF MIGRATION 006
-- =============================================================================
