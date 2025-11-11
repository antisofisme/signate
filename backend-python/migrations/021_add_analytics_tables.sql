-- ============================================================================
-- 021_add_analytics_tables.sql
-- Add analytics tables for performance tracking
-- ============================================================================

-- Content performance analytics
CREATE TABLE IF NOT EXISTS content_performance (
    id SERIAL PRIMARY KEY,
    content_id INTEGER NOT NULL REFERENCES contents(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    total_plays INTEGER DEFAULT 0,
    total_duration INTEGER DEFAULT 0,
    unique_devices INTEGER DEFAULT 0,
    avg_completion_rate NUMERIC(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(content_id, date)
);

CREATE INDEX IF NOT EXISTS idx_content_performance_content ON content_performance(content_id);
CREATE INDEX IF NOT EXISTS idx_content_performance_date ON content_performance(date);

-- Device engagement analytics
CREATE TABLE IF NOT EXISTS device_engagement (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    online_duration INTEGER DEFAULT 0,
    content_plays INTEGER DEFAULT 0,
    unique_content INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(device_id, date)
);

CREATE INDEX IF NOT EXISTS idx_device_engagement_device ON device_engagement(device_id);
CREATE INDEX IF NOT EXISTS idx_device_engagement_date ON device_engagement(date);