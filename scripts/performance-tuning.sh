#!/bin/bash
# Phase 6 Database Performance Tuning

echo "Starting database performance tuning..."

# Run VACUUM and ANALYZE
echo "Running VACUUM ANALYZE..."
docker exec signage-postgres psql -U signage_user -d signage_db -c "VACUUM ANALYZE contents;"
docker exec signage-postgres psql -U signage_user -d signage_db -c "VACUUM ANALYZE devices;"
docker exec signage-postgres psql -U signage_user -d signage_db -c "VACUUM ANALYZE playlists;"
docker exec signage-postgres psql -U signage_user -d signage_db -c "VACUUM ANALYZE content_playback_logs;"

# Create indexes
echo "Creating performance indexes..."
docker exec signage-postgres psql -U signage_user -d signage_db << 'EOF'
-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_contents_org_active_type
  ON contents(organization_id, is_active, content_type);

CREATE INDEX IF NOT EXISTS idx_devices_org_status
  ON devices(organization_id, status);

CREATE INDEX IF NOT EXISTS idx_playlists_org_active
  ON playlists(organization_id, is_active);

-- Create performance monitoring view
CREATE OR REPLACE VIEW v_performance_stats AS
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
  pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
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
EOF

echo "Performance tuning completed!"

# Show performance stats
echo -e "\nDatabase Performance Stats:"
docker exec signage-postgres psql -U signage_user -d signage_db -c "SELECT * FROM v_performance_stats;"