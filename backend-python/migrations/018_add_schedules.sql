-- Migration 026: Advanced Scheduling System
-- Phase 5: Advanced Features - Enhanced scheduling with recurrence patterns

BEGIN;

-- Advanced scheduling with recurrence
CREATE TABLE IF NOT EXISTS schedules (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Schedule Info
    name VARCHAR(255) NOT NULL,
    description TEXT,
    playlist_id INTEGER REFERENCES playlists(id) ON DELETE CASCADE,

    -- Time Range
    start_date DATE NOT NULL,
    end_date DATE,
    start_time TIME,
    end_time TIME,

    -- Recurrence Pattern
    recurrence_type VARCHAR(20), -- 'once', 'daily', 'weekly', 'monthly', 'yearly'
    recurrence_pattern JSONB, -- {"days": [1,3,5], "interval": 2}
    exceptions JSONB, -- ["2025-01-15", "2025-02-20"]

    -- Priority & Status
    priority INTEGER DEFAULT 0, -- Higher = more important
    is_active BOOLEAN DEFAULT true,

    -- Metadata
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_schedules_org ON schedules(organization_id);
CREATE INDEX IF NOT EXISTS idx_schedules_playlist ON schedules(playlist_id);
CREATE INDEX IF NOT EXISTS idx_schedules_dates ON schedules(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_schedules_active ON schedules(is_active);
CREATE INDEX IF NOT EXISTS idx_schedules_priority ON schedules(priority DESC);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_schedules_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER schedules_updated_at
    BEFORE UPDATE ON schedules
    FOR EACH ROW
    EXECUTE FUNCTION update_schedules_updated_at();

COMMIT;
