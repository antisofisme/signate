-- ============================================================================
-- Migration 013: Analytics System - Event Collection and Aggregation
-- ============================================================================
-- Purpose: High-performance analytics for content views, device health,
--          and system metrics with 60,000+ events/hour capacity
--
-- Features:
-- - Time-series events table (partitioned monthly)
-- - Pre-aggregated hourly/daily tables
-- - Materialized views for dashboards
-- - Automatic partition management
-- - Optimized indexes for fast queries
--
-- Performance Targets:
-- - Dashboard load: < 500ms
-- - Real-time metrics: < 100ms
-- - Event ingestion: 1000 events/batch
-- - Storage: ~180 MB/day = 5.4 GB/month
-- ============================================================================

-- ============================================================================
-- PART 1: CORE EVENT TABLES
-- ============================================================================

-- Main analytics events table (partitioned by month)
CREATE TABLE IF NOT EXISTS analytics_events (
    id BIGSERIAL,
    event_time TIMESTAMPTZ NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    device_id INTEGER REFERENCES devices(id) ON DELETE SET NULL,
    content_id INTEGER REFERENCES content(id) ON DELETE SET NULL,
    user_id INTEGER,
    session_id VARCHAR(64),
    metrics JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, event_time)
) PARTITION BY RANGE (event_time);

COMMENT ON TABLE analytics_events IS 'Time-series events storage partitioned monthly for high-volume event tracking';
COMMENT ON COLUMN analytics_events.event_type IS 'Event category: content_play, heartbeat, device_error, etc.';
COMMENT ON COLUMN analytics_events.metrics IS 'Numeric metrics: duration, cpu, memory, bandwidth, etc.';
COMMENT ON COLUMN analytics_events.metadata IS 'Additional context: user_agent, ip_address, error_message, etc.';

-- Create partitions for current and next 3 months
-- This ensures events always have a partition available

-- Current month (November 2025)
CREATE TABLE IF NOT EXISTS analytics_events_2025_11
    PARTITION OF analytics_events
    FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

-- December 2025
CREATE TABLE IF NOT EXISTS analytics_events_2025_12
    PARTITION OF analytics_events
    FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');

-- January 2026
CREATE TABLE IF NOT EXISTS analytics_events_2026_01
    PARTITION OF analytics_events
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

-- February 2026
CREATE TABLE IF NOT EXISTS analytics_events_2026_02
    PARTITION OF analytics_events
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

-- ============================================================================
-- PART 2: AGGREGATION TABLES
-- ============================================================================

-- Hourly aggregations (for real-time analysis)
CREATE TABLE IF NOT EXISTS analytics_hourly (
    hour_time TIMESTAMPTZ NOT NULL,
    device_id INTEGER,
    content_id INTEGER,
    event_type VARCHAR(50),
    event_count INTEGER DEFAULT 0,
    avg_duration NUMERIC(10, 2),
    sum_duration BIGINT DEFAULT 0,
    unique_sessions INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (hour_time, COALESCE(device_id, 0), COALESCE(content_id, 0), event_type)
);

COMMENT ON TABLE analytics_hourly IS 'Pre-aggregated hourly metrics for fast dashboard queries';

-- Daily content aggregations
CREATE TABLE IF NOT EXISTS analytics_daily (
    id SERIAL,
    date DATE NOT NULL,
    device_id INTEGER REFERENCES devices(id) ON DELETE CASCADE,
    content_id INTEGER REFERENCES content(id) ON DELETE CASCADE,
    views INTEGER DEFAULT 0,
    unique_viewers INTEGER DEFAULT 0,
    total_watch_time BIGINT DEFAULT 0,  -- seconds
    avg_watch_time NUMERIC(10, 2) DEFAULT 0,
    completion_rate NUMERIC(5, 4) DEFAULT 0,  -- 0.0 to 1.0
    error_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (date, COALESCE(device_id, 0), COALESCE(content_id, 0))
);

COMMENT ON TABLE analytics_daily IS 'Daily content performance aggregations for reporting';
COMMENT ON COLUMN analytics_daily.completion_rate IS 'Percentage of viewers who watched to completion (0.0-1.0)';

-- Daily device aggregations
CREATE TABLE IF NOT EXISTS analytics_daily_devices (
    id SERIAL,
    date DATE NOT NULL,
    device_id INTEGER REFERENCES devices(id) ON DELETE CASCADE,
    uptime_seconds INTEGER DEFAULT 0,
    online_count INTEGER DEFAULT 0,
    offline_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    avg_cpu_usage NUMERIC(5, 2),
    avg_memory_usage NUMERIC(5, 2),
    total_bandwidth_mb INTEGER DEFAULT 0,
    content_played INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (date, device_id)
);

COMMENT ON TABLE analytics_daily_devices IS 'Daily device health and performance metrics';

-- ============================================================================
-- PART 3: INDEXES FOR PERFORMANCE
-- ============================================================================

-- Events table indexes (critical for query performance)
CREATE INDEX IF NOT EXISTS idx_analytics_events_time
    ON analytics_events (event_time DESC);

CREATE INDEX IF NOT EXISTS idx_analytics_events_device_time
    ON analytics_events (device_id, event_time DESC)
    WHERE device_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_analytics_events_content_time
    ON analytics_events (content_id, event_time DESC)
    WHERE content_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_analytics_events_type_time
    ON analytics_events (event_type, event_time DESC);

CREATE INDEX IF NOT EXISTS idx_analytics_events_session
    ON analytics_events (session_id, event_time DESC)
    WHERE session_id IS NOT NULL;

-- GIN index for JSONB queries
CREATE INDEX IF NOT EXISTS idx_analytics_events_metrics
    ON analytics_events USING GIN (metrics);

CREATE INDEX IF NOT EXISTS idx_analytics_events_metadata
    ON analytics_events USING GIN (metadata);

-- Hourly aggregations indexes
CREATE INDEX IF NOT EXISTS idx_analytics_hourly_time
    ON analytics_hourly (hour_time DESC);

CREATE INDEX IF NOT EXISTS idx_analytics_hourly_device
    ON analytics_hourly (device_id, hour_time DESC)
    WHERE device_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_analytics_hourly_content
    ON analytics_hourly (content_id, hour_time DESC)
    WHERE content_id IS NOT NULL;

-- Daily aggregations indexes
CREATE INDEX IF NOT EXISTS idx_analytics_daily_date
    ON analytics_daily (date DESC);

CREATE INDEX IF NOT EXISTS idx_analytics_daily_content
    ON analytics_daily (content_id, date DESC)
    WHERE content_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_analytics_daily_devices_date
    ON analytics_daily_devices (date DESC);

CREATE INDEX IF NOT EXISTS idx_analytics_daily_devices_device
    ON analytics_daily_devices (device_id, date DESC);

-- ============================================================================
-- PART 4: MATERIALIZED VIEWS FOR DASHBOARDS
-- ============================================================================

-- Real-time dashboard statistics (refreshed every 5 minutes)
CREATE MATERIALIZED VIEW IF NOT EXISTS dashboard_stats AS
SELECT
    -- Device metrics
    COUNT(DISTINCT d.id) as active_devices,
    COUNT(DISTINCT CASE
        WHEN d.last_seen > NOW() - INTERVAL '5 minutes'
        THEN d.id
    END) as online_devices,
    COUNT(DISTINCT CASE
        WHEN d.status = 'maintenance'
        THEN d.id
    END) as maintenance_devices,

    -- Content metrics
    COUNT(DISTINCT c.id) as total_content,
    COALESCE(SUM(c.file_size_bytes) / 1024 / 1024, 0) as total_storage_mb,

    -- Today's playback stats
    (
        SELECT COUNT(*)
        FROM analytics_events
        WHERE event_type = 'content_play'
          AND event_time >= CURRENT_DATE
    ) as total_plays_today,

    (
        SELECT COALESCE(SUM(CAST(metrics->>'duration' AS INTEGER)), 0)
        FROM analytics_events
        WHERE event_type = 'content_play'
          AND event_time >= CURRENT_DATE
    ) as total_watch_time_today,

    -- System health (last hour)
    (
        SELECT AVG(CAST(metrics->>'cpu' AS NUMERIC))
        FROM analytics_events
        WHERE event_type = 'heartbeat'
          AND event_time > NOW() - INTERVAL '1 hour'
          AND metrics->>'cpu' IS NOT NULL
    ) as avg_cpu,

    (
        SELECT AVG(CAST(metrics->>'memory' AS NUMERIC))
        FROM analytics_events
        WHERE event_type = 'heartbeat'
          AND event_time > NOW() - INTERVAL '1 hour'
          AND metrics->>'memory' IS NOT NULL
    ) as avg_memory,

    NOW() as last_updated

FROM devices d
CROSS JOIN content c
WHERE d.status != 'inactive';

-- Create unique index to support CONCURRENTLY refresh
CREATE UNIQUE INDEX IF NOT EXISTS idx_dashboard_stats_singleton
    ON dashboard_stats ((1));

COMMENT ON MATERIALIZED VIEW dashboard_stats IS 'Dashboard metrics refreshed every 5 minutes via scheduled task';

-- ============================================================================
-- PART 5: PARTITION MANAGEMENT FUNCTIONS
-- ============================================================================

-- Function to create next month's partition automatically
CREATE OR REPLACE FUNCTION create_analytics_partition()
RETURNS void AS $$
DECLARE
    partition_name text;
    start_date date;
    end_date date;
    partition_exists boolean;
BEGIN
    -- Calculate next month
    start_date := DATE_TRUNC('month', CURRENT_DATE + INTERVAL '1 month')::date;
    end_date := (start_date + INTERVAL '1 month')::date;
    partition_name := 'analytics_events_' || TO_CHAR(start_date, 'YYYY_MM');

    -- Check if partition already exists
    SELECT EXISTS (
        SELECT 1
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relname = partition_name
          AND n.nspname = 'public'
    ) INTO partition_exists;

    IF NOT partition_exists THEN
        -- Create partition
        EXECUTE format(
            'CREATE TABLE %I PARTITION OF analytics_events FOR VALUES FROM (%L) TO (%L)',
            partition_name,
            start_date,
            end_date
        );

        RAISE NOTICE 'Created partition: %', partition_name;
    ELSE
        RAISE NOTICE 'Partition already exists: %', partition_name;
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION create_analytics_partition IS 'Creates next month partition for analytics_events table';

-- Function to drop old partitions (retention: 12 months)
CREATE OR REPLACE FUNCTION cleanup_old_analytics_partitions()
RETURNS void AS $$
DECLARE
    partition_record record;
    cutoff_date text;
BEGIN
    cutoff_date := TO_CHAR(CURRENT_DATE - INTERVAL '12 months', 'YYYY_MM');

    FOR partition_record IN
        SELECT tablename
        FROM pg_tables
        WHERE tablename LIKE 'analytics_events_%'
          AND tablename < 'analytics_events_' || cutoff_date
          AND schemaname = 'public'
    LOOP
        EXECUTE format('DROP TABLE IF EXISTS %I CASCADE', partition_record.tablename);
        RAISE NOTICE 'Dropped old partition: %', partition_record.tablename;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_old_analytics_partitions IS 'Drops partitions older than 12 months';

-- ============================================================================
-- PART 6: HELPER VIEWS
-- ============================================================================

-- Top content view (last 7 days)
CREATE OR REPLACE VIEW v_top_content_7d AS
SELECT
    c.id,
    c.name,
    c.content_type,
    c.duration_seconds,
    COUNT(DISTINCT ae.device_id) as unique_viewers,
    COUNT(*) FILTER (WHERE ae.event_type = 'content_play') as total_plays,
    AVG(CAST(ae.metrics->>'completion_rate' AS NUMERIC)) as avg_completion_rate,
    SUM(CAST(ae.metrics->>'duration' AS INTEGER)) as total_watch_seconds
FROM content c
LEFT JOIN analytics_events ae
    ON ae.content_id = c.id
    AND ae.event_time > CURRENT_DATE - INTERVAL '7 days'
    AND ae.event_type IN ('content_play', 'content_complete')
WHERE c.is_archived = false
GROUP BY c.id, c.name, c.content_type, c.duration_seconds
HAVING COUNT(*) FILTER (WHERE ae.event_type = 'content_play') > 0
ORDER BY total_plays DESC;

COMMENT ON VIEW v_top_content_7d IS 'Top performing content in last 7 days';

-- Device health summary view
CREATE OR REPLACE VIEW v_device_health_summary AS
SELECT
    d.id,
    d.device_name,
    d.device_type,
    d.status,
    d.last_seen,
    CASE
        WHEN d.last_seen > NOW() - INTERVAL '5 minutes' THEN 'online'
        WHEN d.last_seen > NOW() - INTERVAL '1 hour' THEN 'idle'
        ELSE 'offline'
    END as health_status,
    (
        SELECT COUNT(*)
        FROM analytics_events ae
        WHERE ae.device_id = d.id
          AND ae.event_type = 'device_error'
          AND ae.event_time > CURRENT_DATE
    ) as errors_today,
    (
        SELECT AVG(CAST(metrics->>'cpu' AS NUMERIC))
        FROM analytics_events ae
        WHERE ae.device_id = d.id
          AND ae.event_type = 'heartbeat'
          AND ae.event_time > NOW() - INTERVAL '1 hour'
    ) as avg_cpu_1h,
    (
        SELECT AVG(CAST(metrics->>'memory' AS NUMERIC))
        FROM analytics_events ae
        WHERE ae.device_id = d.id
          AND ae.event_type = 'heartbeat'
          AND ae.event_time > NOW() - INTERVAL '1 hour'
    ) as avg_memory_1h
FROM devices d
WHERE d.status != 'inactive'
ORDER BY d.last_seen DESC NULLS LAST;

COMMENT ON VIEW v_device_health_summary IS 'Real-time device health status with error counts and performance metrics';

-- ============================================================================
-- PART 7: SAMPLE QUERIES FOR TESTING
-- ============================================================================

-- Test query: Dashboard metrics
-- Expected: < 500ms with materialized view
/*
SELECT * FROM dashboard_stats;
*/

-- Test query: Content performance
-- Expected: < 200ms with daily aggregations
/*
SELECT
    c.name,
    ad.date,
    ad.views,
    ad.unique_viewers,
    ad.avg_watch_time,
    ad.completion_rate
FROM analytics_daily ad
JOIN content c ON c.id = ad.content_id
WHERE ad.date >= CURRENT_DATE - INTERVAL '30 days'
  AND ad.content_id = 1
ORDER BY ad.date DESC;
*/

-- Test query: Device uptime
-- Expected: < 300ms with daily aggregations
/*
SELECT
    d.device_name,
    add.date,
    add.uptime_seconds,
    add.error_count,
    add.avg_cpu_usage,
    add.avg_memory_usage
FROM analytics_daily_devices add
JOIN devices d ON d.id = add.device_id
WHERE add.device_id = 1
  AND add.date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY add.date DESC;
*/

-- Test query: Trending content (from events)
-- Expected: < 1s with proper indexes
/*
SELECT
    c.name,
    COUNT(*) as views,
    COUNT(DISTINCT ae.device_id) as unique_viewers
FROM analytics_events ae
JOIN content c ON c.id = ae.content_id
WHERE ae.event_type = 'content_play'
  AND ae.event_time > NOW() - INTERVAL '24 hours'
GROUP BY c.id, c.name
ORDER BY views DESC
LIMIT 10;
*/

-- ============================================================================
-- PART 8: INITIAL DATA SETUP
-- ============================================================================

-- Create initial dashboard stats (will be refreshed by scheduled task)
REFRESH MATERIALIZED VIEW dashboard_stats;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Analytics System Migration Complete!';
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Created:';
    RAISE NOTICE '  - analytics_events (partitioned table)';
    RAISE NOTICE '  - analytics_hourly (pre-aggregation)';
    RAISE NOTICE '  - analytics_daily (content metrics)';
    RAISE NOTICE '  - analytics_daily_devices (device metrics)';
    RAISE NOTICE '  - dashboard_stats (materialized view)';
    RAISE NOTICE '  - Partition management functions';
    RAISE NOTICE '  - 15+ optimized indexes';
    RAISE NOTICE '';
    RAISE NOTICE 'Capacity:';
    RAISE NOTICE '  - 60,000+ events/hour';
    RAISE NOTICE '  - ~180 MB/day storage';
    RAISE NOTICE '  - 12 month retention';
    RAISE NOTICE '';
    RAISE NOTICE 'Performance Targets:';
    RAISE NOTICE '  - Dashboard: < 500ms';
    RAISE NOTICE '  - Real-time: < 100ms';
    RAISE NOTICE '  - Reports: < 1s';
    RAISE NOTICE '';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '  1. Set up scheduled tasks:';
    RAISE NOTICE '     - Hourly: aggregate_hourly_data()';
    RAISE NOTICE '     - Daily: aggregate_daily_data()';
    RAISE NOTICE '     - Every 5 min: REFRESH MATERIALIZED VIEW';
    RAISE NOTICE '     - Monthly: create_analytics_partition()';
    RAISE NOTICE '  2. Deploy viewer analytics tracker';
    RAISE NOTICE '  3. Enable real-time dashboard';
    RAISE NOTICE '';
END $$;
