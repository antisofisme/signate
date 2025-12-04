-- Migration: 078
-- Description: Create schedule targeting junction tables for proper normalization
-- Date: 2025-12-04
-- Impact: Breaking change - requires coordinated backend/CMS/player updates

BEGIN;

-- ============================================================================
-- 1. CREATE JUNCTION TABLES - Replace JSONB arrays with proper foreign keys
-- ============================================================================

-- Schedule to Device targeting (replaces schedules.device_ids JSONB)
CREATE TABLE IF NOT EXISTS schedule_device_targeting (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    schedule_id INTEGER NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    -- Ensure unique combinations
    CONSTRAINT uq_schedule_device UNIQUE(schedule_id, device_id)
);

-- Schedule to Tag targeting (replaces schedules.tag_ids JSONB)
CREATE TABLE IF NOT EXISTS schedule_tag_targeting (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    schedule_id INTEGER NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    -- Ensure unique combinations
    CONSTRAINT uq_schedule_tag UNIQUE(schedule_id, tag_id)
);

-- ============================================================================
-- 2. CREATE INDEXES - For fast lookups from both directions
-- ============================================================================

-- Device targeting indexes
CREATE INDEX IF NOT EXISTS idx_schedule_device_schedule
    ON schedule_device_targeting(schedule_id);
CREATE INDEX IF NOT EXISTS idx_schedule_device_device
    ON schedule_device_targeting(device_id);

-- Tag targeting indexes
CREATE INDEX IF NOT EXISTS idx_schedule_tag_schedule
    ON schedule_tag_targeting(schedule_id);
CREATE INDEX IF NOT EXISTS idx_schedule_tag_tag
    ON schedule_tag_targeting(tag_id);

-- ============================================================================
-- 3. ADD TABLE COMMENTS
-- ============================================================================

COMMENT ON TABLE schedule_device_targeting IS
    'Junction table for schedule-to-device targeting. Replaces JSONB device_ids array for better referential integrity and query performance.';

COMMENT ON TABLE schedule_tag_targeting IS
    'Junction table for schedule-to-tag targeting. Replaces JSONB tag_ids array for better referential integrity and query performance.';

COMMIT;

-- ============================================================================
-- ROLLBACK (if needed):
-- DROP INDEX IF EXISTS idx_schedule_device_schedule;
-- DROP INDEX IF EXISTS idx_schedule_device_device;
-- DROP INDEX IF EXISTS idx_schedule_tag_schedule;
-- DROP INDEX IF EXISTS idx_schedule_tag_tag;
-- DROP TABLE IF EXISTS schedule_device_targeting;
-- DROP TABLE IF EXISTS schedule_tag_targeting;
-- ============================================================================
