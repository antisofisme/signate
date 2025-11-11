-- Phase 6 Final Performance Tuning
BEGIN;

-- ============================================================================
-- VACUUM and ANALYZE
-- ============================================================================

VACUUM ANALYZE contents;
VACUUM ANALYZE devices;
VACUUM ANALYZE playlists;
VACUUM ANALYZE content_playback_logs;

-- ============================================================================
-- Update Statistics
-- ============================================================================

ANALYZE contents;
ANALYZE devices;
ANALYZE playlists;
ANALYZE playlist_items;

-- ============================================================================
-- Add Missing Indexes (if any)
-- ============================================================================

-- Composite index for common query pattern
CREATE INDEX IF NOT EXISTS idx_contents_org_active_type
  ON contents(organization_id, is_active, content_type);

CREATE INDEX IF NOT EXISTS idx_devices_org_status
  ON devices(organization_id, status);

CREATE INDEX IF NOT EXISTS idx_playlists_org_active
  ON playlists(organization_id, is_active);

-- ============================================================================
-- Optimize Large Tables
-- ============================================================================

-- Enable autovacuum more aggressively for large tables
ALTER TABLE content_playback_logs SET (
  autovacuum_vacuum_scale_factor = 0.05,
  autovacuum_analyze_scale_factor = 0.02
);

ALTER TABLE device_health_metrics SET (
  autovacuum_vacuum_scale_factor = 0.05,
  autovacuum_analyze_scale_factor = 0.02
);

-- ============================================================================
-- Connection and Query Limits
-- ============================================================================

-- Set statement timeout to prevent long-running queries
ALTER DATABASE signage_db SET statement_timeout = '30s';

-- Set lock timeout to prevent deadlocks
ALTER DATABASE signage_db SET lock_timeout = '10s';

-- ============================================================================
-- Performance Monitoring View
-- ============================================================================
CREATE OR REPLACE VIEW v_performance_stats AS
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
  pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS indexes_size,
  n_tup_ins AS inserts,
  n_tup_upd AS updates,
  n_tup_del AS deletes,
  seq_scan AS sequential_scans,
  idx_scan AS index_scans,
  CASE WHEN seq_scan + idx_scan > 0
    THEN round(100.0 * idx_scan / (seq_scan + idx_scan), 2)
    ELSE 0
  END AS index_usage_percent
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

COMMIT;