-- ============================================================================
-- Migration 014: Add Content Playback Logs (Analytics)
-- Description: Track content playback for analytics and compliance
-- Created: 2025-01-09
-- Priority: HIGH
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. CREATE CONTENT_PLAYBACK_LOGS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS content_playback_logs (
    -- Identity
    id SERIAL PRIMARY KEY,

    -- What was played
    content_id INTEGER NOT NULL REFERENCES contents(id) ON DELETE CASCADE,
    playlist_id INTEGER REFERENCES playlists(id) ON DELETE SET NULL,

    -- Where was it played
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- When and how long
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ended_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER, -- Actual play duration

    -- Completion tracking
    completed BOOLEAN DEFAULT FALSE NOT NULL,
    skip_reason VARCHAR(50), -- 'user_skip', 'error', 'schedule_change', 'interrupted'

    -- Context
    source VARCHAR(50), -- 'playlist', 'direct_assignment', 'tag_assignment'

    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- ============================================================================
-- 2. CREATE INDEXES
-- ============================================================================

-- Content analytics (most viewed)
CREATE INDEX idx_playback_content ON content_playback_logs(content_id, started_at DESC);

-- Device playback history
CREATE INDEX idx_playback_device ON content_playback_logs(device_id, started_at DESC);

-- Organization analytics
CREATE INDEX idx_playback_organization ON content_playback_logs(organization_id, started_at DESC);

-- Time-based queries (recent playbacks)
CREATE INDEX idx_playback_date ON content_playback_logs(started_at DESC);

-- Completed playbacks only
CREATE INDEX idx_playback_completed ON content_playback_logs(content_id, completed)
    WHERE completed = TRUE;

-- Playlist analytics
CREATE INDEX idx_playback_playlist ON content_playback_logs(playlist_id, started_at DESC)
    WHERE playlist_id IS NOT NULL;

-- ============================================================================
-- 3. CREATE ANALYTICS VIEWS
-- ============================================================================

-- View: Content performance summary
CREATE OR REPLACE VIEW content_performance AS
SELECT
    c.id as content_id,
    c.title,
    c.content_type,
    c.organization_id,
    count(*) as total_plays,
    count(*) FILTER (WHERE cpl.completed = TRUE) as completed_plays,
    round(avg(cpl.duration_seconds), 2) as avg_duration_seconds,
    max(cpl.started_at) as last_played_at,
    count(DISTINCT cpl.device_id) as unique_devices
FROM contents c
LEFT JOIN content_playback_logs cpl ON cpl.content_id = c.id
GROUP BY c.id, c.title, c.content_type, c.organization_id;

COMMENT ON VIEW content_performance IS
    'Content playback performance metrics for analytics';

-- View: Device engagement summary
CREATE OR REPLACE VIEW device_engagement AS
SELECT
    d.id as device_id,
    d.device_name,
    d.organization_id,
    count(*) as total_plays,
    count(DISTINCT cpl.content_id) as unique_content,
    max(cpl.started_at) as last_playback_at,
    sum(cpl.duration_seconds) as total_watch_time_seconds
FROM devices d
LEFT JOIN content_playback_logs cpl ON cpl.device_id = d.id
GROUP BY d.id, d.device_name, d.organization_id;

COMMENT ON VIEW device_engagement IS
    'Device engagement metrics for monitoring';

-- ============================================================================
-- 4. COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE content_playback_logs IS 'Content playback tracking for analytics and compliance';
COMMENT ON COLUMN content_playback_logs.duration_seconds IS 'Actual playback duration (may differ from content.duration)';
COMMENT ON COLUMN content_playback_logs.completed IS 'TRUE if content played to the end';
COMMENT ON COLUMN content_playback_logs.skip_reason IS 'Why playback was interrupted (NULL if completed)';
COMMENT ON COLUMN content_playback_logs.source IS 'How content was assigned: playlist, direct_assignment, tag_assignment';

-- ============================================================================
-- 5. VERIFICATION QUERY
-- ============================================================================

-- Verify table created
SELECT
    table_name,
    (SELECT count(*) FROM information_schema.columns WHERE table_name = 'content_playback_logs') as column_count
FROM information_schema.tables
WHERE table_name = 'content_playback_logs';

-- Verify views created
SELECT
    table_name as view_name,
    view_definition
FROM information_schema.views
WHERE table_name IN ('content_performance', 'device_engagement');

COMMIT;

-- ============================================================================
-- ROLLBACK SCRIPT
-- ============================================================================
/*
BEGIN;
DROP VIEW IF EXISTS content_performance;
DROP VIEW IF EXISTS device_engagement;
DROP INDEX IF EXISTS idx_playback_content;
DROP INDEX IF EXISTS idx_playback_device;
DROP INDEX IF EXISTS idx_playback_organization;
DROP INDEX IF EXISTS idx_playback_date;
DROP INDEX IF EXISTS idx_playback_completed;
DROP INDEX IF EXISTS idx_playback_playlist;
DROP TABLE IF EXISTS content_playback_logs;
COMMIT;
*/

-- ============================================================================
-- USAGE EXAMPLES
-- ============================================================================

-- Log playback start
/*
INSERT INTO content_playback_logs (
    content_id, device_id, organization_id, playlist_id,
    started_at, source
) VALUES (
    123, 456, 1, 789,
    NOW(), 'playlist'
) RETURNING id;
*/

-- Log playback end
/*
UPDATE content_playback_logs
SET
    ended_at = NOW(),
    duration_seconds = EXTRACT(EPOCH FROM (NOW() - started_at)),
    completed = TRUE
WHERE id = 12345;
*/

-- Top 10 most played content
/*
SELECT * FROM content_performance
ORDER BY total_plays DESC
LIMIT 10;
*/

-- Device with most engagement
/*
SELECT * FROM device_engagement
ORDER BY total_watch_time_seconds DESC
LIMIT 10;
*/

-- ============================================================================
-- Migration Complete
-- ============================================================================

-- To run this migration on server:
-- docker exec -i signage-postgres psql -U signage_user -d signage_db < database/fix-database/migrations/014_add_content_playback_logs.sql
