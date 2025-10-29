-- ============================================================================
-- Performance Optimization SQL Script
-- For Merged Anthias-Backend System
--
-- This script contains all database optimizations identified in the
-- performance strategy document. Run these in order on your PostgreSQL
-- database to achieve optimal query performance.
-- ============================================================================

-- ============================================================================
-- PART 1: CONNECTION POOL & DATABASE SETTINGS
-- ============================================================================

-- Adjust PostgreSQL settings for better performance
-- Add these to postgresql.conf or ALTER SYSTEM commands

ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET min_wal_size = '1GB';
ALTER SYSTEM SET max_wal_size = '4GB';
ALTER SYSTEM SET max_worker_processes = 8;
ALTER SYSTEM SET max_parallel_workers_per_gather = 2;
ALTER SYSTEM SET max_parallel_workers = 8;

-- Enable query performance tracking
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET pg_stat_statements.track = 'all';

-- Apply settings (requires restart)
SELECT pg_reload_conf();

-- ============================================================================
-- PART 2: CREATE MISSING INDEXES
-- ============================================================================

-- Foreign Key Indexes (Critical for JOIN performance)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_assignments_content_id
ON content_assignments(content_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_assignments_device_id
ON content_assignments(device_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_assignments_tag_id
ON content_assignments(tag_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_playlist_content_playlist_id
ON playlist_content(playlist_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_playlist_content_content_id
ON playlist_content(content_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_playlist_assignments_playlist_id
ON playlist_assignments(playlist_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_playlist_assignments_device_id
ON playlist_assignments(device_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_device_tags_device_id
ON device_tags(device_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_device_tags_tag_id
ON device_tags(tag_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_device_logs_device_id
ON device_logs(device_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_activity_logs_user_id
ON activity_logs(user_id);

-- ============================================================================
-- PART 3: PERFORMANCE-CRITICAL COMPOSITE INDEXES
-- ============================================================================

-- Optimize content assignment lookups (most frequent query)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_assignments_active_lookup
ON content_assignments(device_id, is_active, display_order)
WHERE is_active = true;

-- Optimize playlist content sequence retrieval
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_playlist_content_sequence
ON playlist_content(playlist_id, play_order, is_enabled)
INCLUDE (content_id, duration)
WHERE is_enabled = true;

-- Optimize device heartbeat and online status checks
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_devices_heartbeat
ON devices(last_seen DESC)
INCLUDE (id, name, is_active)
WHERE is_active = true;

-- Optimize scheduled content queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_schedule
ON content(is_active, start_date, end_date)
INCLUDE (id, title, file_url, file_type, duration)
WHERE is_active = true;

-- Optimize playlist assignments for devices
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_playlist_assignments_active
ON playlist_assignments(device_id, is_active)
INCLUDE (playlist_id, display_order)
WHERE is_active = true;

-- ============================================================================
-- PART 4: PARTIAL INDEXES FOR COMMON FILTERS
-- ============================================================================

-- Index for online devices (last seen within 5 minutes)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_devices_online
ON devices(id, name, last_seen)
WHERE is_active = true AND last_seen > NOW() - INTERVAL '5 minutes';

-- Index for pending device registrations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_devices_pending
ON devices(activation_code, created_at)
WHERE activation_code IS NOT NULL AND is_active = false;

-- Index for active content
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_active
ON content(created_at DESC)
INCLUDE (id, title, file_url, file_type, duration)
WHERE is_active = true;

-- Index for scheduled playlists
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_playlists_scheduled
ON playlists(schedule_start, schedule_end, is_active)
WHERE schedule_start IS NOT NULL AND is_active = true;

-- ============================================================================
-- PART 5: FULL-TEXT SEARCH OPTIMIZATION
-- ============================================================================

-- Add full-text search for content
ALTER TABLE content ADD COLUMN IF NOT EXISTS search_vector tsvector;

UPDATE content SET search_vector =
  to_tsvector('english', COALESCE(title, '') || ' ' || COALESCE(description, ''));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_search
ON content USING gin(search_vector);

-- Trigger to maintain search vector
CREATE OR REPLACE FUNCTION update_content_search_vector()
RETURNS TRIGGER AS $$
BEGIN
  NEW.search_vector := to_tsvector('english',
    COALESCE(NEW.title, '') || ' ' || COALESCE(NEW.description, ''));
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_content_search
BEFORE INSERT OR UPDATE OF title, description ON content
FOR EACH ROW EXECUTE FUNCTION update_content_search_vector();

-- Add full-text search for devices
ALTER TABLE devices ADD COLUMN IF NOT EXISTS search_vector tsvector;

UPDATE devices SET search_vector =
  to_tsvector('english', COALESCE(name, '') || ' ' || COALESCE(location, ''));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_devices_search
ON devices USING gin(search_vector);

-- ============================================================================
-- PART 6: STATISTICS AND QUERY OPTIMIZATION
-- ============================================================================

-- Update table statistics for query planner
ANALYZE content;
ANALYZE devices;
ANALYZE playlist_content;
ANALYZE content_assignments;
ANALYZE playlists;
ANALYZE playlist_assignments;
ANALYZE tags;
ANALYZE device_tags;
ANALYZE device_logs;
ANALYZE activity_logs;

-- Create extended statistics for correlated columns
CREATE STATISTICS IF NOT EXISTS stat_content_assignments_device_tag
ON device_id, tag_id FROM content_assignments;

CREATE STATISTICS IF NOT EXISTS stat_playlist_content_order
ON playlist_id, play_order FROM playlist_content;

CREATE STATISTICS IF NOT EXISTS stat_devices_active_lastseen
ON is_active, last_seen FROM devices;

-- ============================================================================
-- PART 7: MATERIALIZED VIEWS FOR COMPLEX QUERIES
-- ============================================================================

-- Materialized view for device content summary
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_device_content_summary AS
SELECT
    d.id as device_id,
    d.name as device_name,
    COUNT(DISTINCT ca.content_id) as content_count,
    COUNT(DISTINCT pa.playlist_id) as playlist_count,
    MAX(ca.updated_at) as last_content_update,
    MAX(pa.updated_at) as last_playlist_update
FROM devices d
LEFT JOIN content_assignments ca ON ca.device_id = d.id AND ca.is_active = true
LEFT JOIN playlist_assignments pa ON pa.device_id = d.id AND pa.is_active = true
WHERE d.is_active = true
GROUP BY d.id, d.name;

CREATE UNIQUE INDEX ON mv_device_content_summary(device_id);

-- Materialized view for playlist statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_playlist_stats AS
SELECT
    p.id as playlist_id,
    p.name as playlist_name,
    COUNT(pc.id) as content_count,
    SUM(COALESCE(pc.duration, c.duration, 0)) as total_duration,
    COUNT(DISTINCT pa.device_id) as assigned_devices,
    MAX(pc.updated_at) as last_modified
FROM playlists p
LEFT JOIN playlist_content pc ON pc.playlist_id = p.id AND pc.is_enabled = true
LEFT JOIN content c ON c.id = pc.content_id AND c.is_active = true
LEFT JOIN playlist_assignments pa ON pa.playlist_id = p.id AND pa.is_active = true
WHERE p.is_active = true
GROUP BY p.id, p.name;

CREATE UNIQUE INDEX ON mv_playlist_stats(playlist_id);

-- Refresh materialized views periodically (schedule with pg_cron or external scheduler)
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_device_content_summary;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_playlist_stats;

-- ============================================================================
-- PART 8: OPTIMIZE EXISTING QUERIES
-- ============================================================================

-- Function to get online devices efficiently
CREATE OR REPLACE FUNCTION get_online_devices()
RETURNS TABLE(
    device_id INTEGER,
    device_name VARCHAR,
    last_seen TIMESTAMP,
    location VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.id,
        d.name,
        d.last_seen,
        d.location
    FROM devices d
    WHERE d.is_active = true
    AND d.last_seen > NOW() - INTERVAL '5 minutes'
    ORDER BY d.last_seen DESC;
END;
$$ LANGUAGE plpgsql
STABLE
PARALLEL SAFE;

-- Function to get device playlist sequence (cached)
CREATE OR REPLACE FUNCTION get_device_playlist_sequence(p_device_id INTEGER)
RETURNS TABLE(
    content_id INTEGER,
    content_url TEXT,
    content_type VARCHAR,
    duration INTEGER,
    play_order INTEGER
) AS $$
BEGIN
    RETURN QUERY
    WITH active_playlists AS (
        SELECT playlist_id, display_order
        FROM playlist_assignments
        WHERE device_id = p_device_id AND is_active = true
        ORDER BY display_order
    )
    SELECT
        c.id,
        c.file_url,
        c.file_type,
        COALESCE(pc.duration, c.duration, 10) as duration,
        ROW_NUMBER() OVER (ORDER BY ap.display_order, pc.play_order)::INTEGER as play_order
    FROM active_playlists ap
    JOIN playlist_content pc ON pc.playlist_id = ap.playlist_id
    JOIN content c ON c.id = pc.content_id
    WHERE pc.is_enabled = true AND c.is_active = true
    ORDER BY play_order;
END;
$$ LANGUAGE plpgsql
STABLE
PARALLEL SAFE;

-- ============================================================================
-- PART 9: CLEANUP AND MAINTENANCE
-- ============================================================================

-- Remove duplicate indexes (if any)
DO $$
DECLARE
    duplicate_index RECORD;
BEGIN
    FOR duplicate_index IN
        SELECT indexname
        FROM pg_indexes
        WHERE schemaname = 'public'
        GROUP BY tablename, regexp_replace(indexdef, 'idx_[a-z0-9_]+', '', 'g')
        HAVING COUNT(*) > 1
    LOOP
        EXECUTE 'DROP INDEX IF EXISTS ' || duplicate_index.indexname;
    END LOOP;
END $$;

-- Vacuum and reindex tables
VACUUM ANALYZE content;
VACUUM ANALYZE devices;
VACUUM ANALYZE playlist_content;
VACUUM ANALYZE content_assignments;

-- Reindex tables for optimal performance
REINDEX TABLE CONCURRENTLY content;
REINDEX TABLE CONCURRENTLY devices;
REINDEX TABLE CONCURRENTLY playlist_content;
REINDEX TABLE CONCURRENTLY content_assignments;

-- ============================================================================
-- PART 10: MONITORING QUERIES
-- ============================================================================

-- Create view for monitoring slow queries
CREATE OR REPLACE VIEW v_slow_queries AS
SELECT
    query,
    calls,
    mean_exec_time,
    max_exec_time,
    total_exec_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_ratio
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat_statements%'
ORDER BY mean_exec_time DESC
LIMIT 20;

-- Create view for index usage statistics
CREATE OR REPLACE VIEW v_index_usage AS
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Create view for table bloat estimation
CREATE OR REPLACE VIEW v_table_bloat AS
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    n_dead_tup,
    n_live_tup,
    round(n_dead_tup * 100.0 / nullif(n_live_tup + n_dead_tup, 0), 2) AS dead_ratio
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Check all indexes were created successfully
SELECT
    tablename,
    COUNT(*) as index_count
FROM pg_indexes
WHERE schemaname = 'public'
GROUP BY tablename
ORDER BY tablename;

-- Check query performance improvement
SELECT
    'Before optimization: Check pg_stat_statements for baseline' as note
UNION ALL
SELECT
    'After optimization: Compare mean_exec_time reduction' as note;

-- Grant necessary permissions for application user
GRANT USAGE ON SCHEMA public TO signage_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO signage_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO signage_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO signage_user;