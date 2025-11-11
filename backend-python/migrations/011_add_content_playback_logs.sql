-- ============================================================================
-- 011_add_content_playback_logs.sql
-- Add content playback logs table
-- ============================================================================

-- Content playback logs table
CREATE TABLE IF NOT EXISTS content_playback_logs (
    id SERIAL PRIMARY KEY,
    content_id INTEGER NOT NULL REFERENCES contents(id) ON DELETE CASCADE,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ended_at TIMESTAMP WITH TIME ZONE,
    duration INTEGER,
    completed BOOLEAN DEFAULT false,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_playback_logs_content ON content_playback_logs(content_id);
CREATE INDEX IF NOT EXISTS idx_playback_logs_device ON content_playback_logs(device_id);
CREATE INDEX IF NOT EXISTS idx_playback_logs_started ON content_playback_logs(started_at);