-- ============================================================================
-- Performance Optimization: Add Missing Database Indexes
-- Created: 2025-01-11
-- Description: Add indexes identified during performance review
-- ============================================================================

-- ============================================================================
-- 1. DEVICES TABLE INDEXES
-- ============================================================================

-- Frequently queried by organization and status
CREATE INDEX IF NOT EXISTS idx_devices_org_status 
    ON devices(organization_id, status);

-- Heartbeat queries (last_seen)
CREATE INDEX IF NOT EXISTS idx_devices_last_seen 
    ON devices(last_seen) 
    WHERE status = 'active';

-- Room-based queries for hotels
CREATE INDEX IF NOT EXISTS idx_devices_room_location 
    ON devices(organization_id, room_number, location_type);

-- ============================================================================
-- 2. CONTENTS TABLE INDEXES
-- ============================================================================

-- Content queries by organization and type
CREATE INDEX IF NOT EXISTS idx_contents_org_type_active 
    ON contents(organization_id, content_type, is_active) 
    WHERE deleted_at IS NULL;

-- Hash-based duplicate detection
CREATE INDEX IF NOT EXISTS idx_contents_file_hash 
    ON contents(file_hash, organization_id) 
    WHERE deleted_at IS NULL;

-- Content status tracking
CREATE INDEX IF NOT EXISTS idx_contents_upload_status 
    ON contents(upload_status) 
    WHERE upload_status != 'completed';

CREATE INDEX IF NOT EXISTS idx_contents_transcoding_status 
    ON contents(transcoding_status) 
    WHERE transcoding_status = 'pending';

-- ============================================================================
-- 3. PLAYLISTS TABLE INDEXES
-- ============================================================================

-- Active playlists by organization
CREATE INDEX IF NOT EXISTS idx_playlists_org_active 
    ON playlists(organization_id, is_active) 
    WHERE deleted_at IS NULL;

-- Priority-based queries
CREATE INDEX IF NOT EXISTS idx_playlists_priority 
    ON playlists(priority DESC, is_active) 
    WHERE deleted_at IS NULL;

-- Special playlist types
CREATE INDEX IF NOT EXISTS idx_playlists_special_types 
    ON playlists(organization_id, is_default, is_pms_template) 
    WHERE deleted_at IS NULL;

-- ============================================================================
-- 4. PLAYLIST_CONTENTS TABLE INDEXES
-- ============================================================================

-- Optimize playlist content retrieval
CREATE INDEX IF NOT EXISTS idx_playlist_contents_order 
    ON playlist_contents(playlist_id, order_index);

-- Content usage tracking
CREATE INDEX IF NOT EXISTS idx_playlist_contents_content 
    ON playlist_contents(content_id);

-- ============================================================================
-- 5. SCHEDULES TABLE INDEXES
-- ============================================================================

-- Active schedules by date range
CREATE INDEX IF NOT EXISTS idx_schedules_active_dates 
    ON schedules(organization_id, is_active, start_date, end_date) 
    WHERE is_active = TRUE;

-- Time-based schedule queries
CREATE INDEX IF NOT EXISTS idx_schedules_time_range 
    ON schedules(start_time, end_time) 
    WHERE is_active = TRUE;

-- Priority-based schedule resolution
CREATE INDEX IF NOT EXISTS idx_schedules_priority_active 
    ON schedules(organization_id, priority DESC) 
    WHERE is_active = TRUE;

-- ============================================================================
-- 6. TAGS TABLE INDEXES
-- ============================================================================

-- Tag queries by organization
CREATE INDEX IF NOT EXISTS idx_tags_org_name 
    ON tags(organization_id, tag_name);

-- Tags with playlist assignments
CREATE INDEX IF NOT EXISTS idx_tags_playlist_assignment 
    ON tags(organization_id, assigned_playlist_id) 
    WHERE assigned_playlist_id IS NOT NULL;

-- ============================================================================
-- 7. DEVICE_TAGS TABLE INDEXES
-- ============================================================================

-- Already has good indexes from migration 006
-- Verify they exist:
CREATE INDEX IF NOT EXISTS idx_device_tags_device ON device_tags(device_id);
CREATE INDEX IF NOT EXISTS idx_device_tags_tag ON device_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_device_tags_both ON device_tags(device_id, tag_id);

-- ============================================================================
-- 8. AUDIT_LOGS TABLE INDEXES
-- ============================================================================

-- Audit trail queries
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_action 
    ON audit_logs(user_id, action, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_logs_resource 
    ON audit_logs(resource_type, resource_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_logs_org_date 
    ON audit_logs(organization_id, created_at DESC);

-- ============================================================================
-- 9. ACTIVITY_LOGS TABLE INDEXES
-- ============================================================================

-- Activity tracking queries
CREATE INDEX IF NOT EXISTS idx_activity_logs_device_time 
    ON activity_logs(device_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_activity_logs_content_time 
    ON activity_logs(content_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_activity_logs_org_action 
    ON activity_logs(organization_id, action, created_at DESC);

-- ============================================================================
-- 10. USERS TABLE INDEXES
-- ============================================================================

-- User queries by organization
CREATE INDEX IF NOT EXISTS idx_users_org_active 
    ON users(organization_id, is_active);

-- Username lookups (already has unique constraint)
-- Email lookups
CREATE INDEX IF NOT EXISTS idx_users_email 
    ON users(email) 
    WHERE email IS NOT NULL;

-- ============================================================================
-- 11. SESSIONS TABLE INDEXES
-- ============================================================================

-- Active session lookups
CREATE INDEX IF NOT EXISTS idx_sessions_user_active 
    ON sessions(user_id, is_active) 
    WHERE is_active = TRUE;

-- Session expiration cleanup
CREATE INDEX IF NOT EXISTS idx_sessions_expires 
    ON sessions(expires_at) 
    WHERE is_active = TRUE;

-- ============================================================================
-- 12. DEVICE_COMMANDS TABLE INDEXES
-- ============================================================================

-- Pending commands by device
CREATE INDEX IF NOT EXISTS idx_device_commands_pending 
    ON device_commands(device_id, status, priority DESC) 
    WHERE status = 'pending';

-- Command history queries
CREATE INDEX IF NOT EXISTS idx_device_commands_device_time 
    ON device_commands(device_id, created_at DESC);

-- ============================================================================
-- 13. DEVICE_HEALTH_METRICS TABLE INDEXES
-- ============================================================================

-- Recent health metrics
CREATE INDEX IF NOT EXISTS idx_device_health_device_time 
    ON device_health_metrics(device_id, recorded_at DESC);

-- Health status monitoring
CREATE INDEX IF NOT EXISTS idx_device_health_status 
    ON device_health_metrics(device_id, health_status) 
    WHERE recorded_at > NOW() - INTERVAL '24 hours';

-- ============================================================================
-- 14. ANALYZE TABLES FOR QUERY PLANNER
-- ============================================================================

-- Update statistics for query planner optimization
ANALYZE devices;
ANALYZE contents;
ANALYZE playlists;
ANALYZE playlist_contents;
ANALYZE schedules;
ANALYZE tags;
ANALYZE device_tags;
ANALYZE audit_logs;
ANALYZE activity_logs;
ANALYZE users;
ANALYZE sessions;
ANALYZE device_commands;
ANALYZE device_health_metrics;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- List all indexes on key tables
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename IN (
    'devices', 'contents', 'playlists', 'playlist_contents', 
    'schedules', 'tags', 'device_tags', 'audit_logs'
)
ORDER BY tablename, indexname;
