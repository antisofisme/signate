-- ============================================================================
-- Migration 015: Add Composite Indexes for Performance Optimization
-- Description: Add strategic composite indexes to improve query performance
-- Created: 2025-01-09
-- Priority: HIGH
-- ============================================================================

BEGIN;

-- ============================================================================
-- PERFORMANCE ANALYSIS
-- ============================================================================
-- Based on expected query patterns in multi-tenant digital signage system:
-- 1. Filter by organization + status (active/inactive)
-- 2. Filter by organization + type/category
-- 3. Sort by organization + created_at/updated_at
-- 4. Join operations on junction tables
-- ============================================================================

-- ============================================================================
-- 1. CONTENTS TABLE - High Traffic Queries
-- ============================================================================

-- Most common query: Get active contents by organization
CREATE INDEX IF NOT EXISTS idx_contents_org_active
    ON contents(organization_id, is_active, created_at DESC)
    WHERE deleted_at IS NULL;

-- Filter by content type
CREATE INDEX IF NOT EXISTS idx_contents_org_type
    ON contents(organization_id, content_type, created_at DESC)
    WHERE deleted_at IS NULL;

-- Search by title (for autocomplete/search features)
CREATE INDEX IF NOT EXISTS idx_contents_title_search
    ON contents USING gin(to_tsvector('english', title))
    WHERE deleted_at IS NULL;

-- Storage key lookup (for file operations)
CREATE INDEX IF NOT EXISTS idx_contents_storage_key
    ON contents(storage_key)
    WHERE deleted_at IS NULL;

COMMENT ON INDEX idx_contents_org_active IS
    'Optimizes queries: Get active contents by organization';
COMMENT ON INDEX idx_contents_org_type IS
    'Optimizes queries: Filter contents by type within organization';
COMMENT ON INDEX idx_contents_title_search IS
    'Full-text search on content titles';
COMMENT ON INDEX idx_contents_storage_key IS
    'Fast lookup for file operations';

-- ============================================================================
-- 2. DEVICES TABLE - Real-time Status Queries
-- ============================================================================

-- Most critical: Get online devices by organization
CREATE INDEX IF NOT EXISTS idx_devices_org_status
    ON devices(organization_id, status, last_seen DESC)
    WHERE deleted_at IS NULL;

-- Location-based queries
CREATE INDEX IF NOT EXISTS idx_devices_org_location
    ON devices(organization_id, location_type, device_name)
    WHERE deleted_at IS NULL;

-- Activation status tracking
CREATE INDEX IF NOT EXISTS idx_devices_activation
    ON devices(is_activated, activation_code)
    WHERE is_activated = FALSE AND deleted_at IS NULL;

COMMENT ON INDEX idx_devices_org_status IS
    'Optimizes dashboard: Get online/offline devices by organization';
COMMENT ON INDEX idx_devices_org_location IS
    'Location-based device filtering';
COMMENT ON INDEX idx_devices_activation IS
    'Track pending device activations';

-- ============================================================================
-- 3. PLAYLISTS TABLE - Assignment Queries
-- ============================================================================

-- Get active playlists by organization
CREATE INDEX IF NOT EXISTS idx_playlists_org_active
    ON playlists(organization_id, is_active, created_at DESC)
    WHERE deleted_at IS NULL;

-- Priority-based sorting for scheduling
CREATE INDEX IF NOT EXISTS idx_playlists_org_priority
    ON playlists(organization_id, priority DESC, name)
    WHERE deleted_at IS NULL AND is_active = TRUE;

COMMENT ON INDEX idx_playlists_org_active IS
    'Get active playlists by organization';
COMMENT ON INDEX idx_playlists_org_priority IS
    'Priority-based playlist scheduling';

-- ============================================================================
-- 4. TAGS TABLE - Categorization Queries
-- ============================================================================

-- Tag-based filtering
CREATE INDEX IF NOT EXISTS idx_tags_org_name
    ON tags(organization_id, name)
    WHERE deleted_at IS NULL;

COMMENT ON INDEX idx_tags_org_name IS
    'Fast tag lookup by name within organization';

-- ============================================================================
-- 5. JUNCTION TABLES - Many-to-Many Relationships
-- ============================================================================

-- Content Tags (M:N)
CREATE INDEX IF NOT EXISTS idx_content_tags_composite
    ON content_tags(content_id, tag_id);

CREATE INDEX IF NOT EXISTS idx_content_tags_reverse
    ON content_tags(tag_id, content_id);

-- Device Tags (M:N)
CREATE INDEX IF NOT EXISTS idx_device_tags_composite
    ON device_tags(device_id, tag_id);

CREATE INDEX IF NOT EXISTS idx_device_tags_reverse
    ON device_tags(tag_id, device_id);

-- Playlist Contents (M:N with ordering)
CREATE INDEX IF NOT EXISTS idx_playlist_contents_order
    ON playlist_contents(playlist_id, display_order, content_id);

CREATE INDEX IF NOT EXISTS idx_playlist_contents_reverse
    ON playlist_contents(content_id, playlist_id);

-- Playlist Assignments (polymorphic)
CREATE INDEX IF NOT EXISTS idx_playlist_assignments_device
    ON playlist_assignments(device_id, playlist_id)
    WHERE device_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_playlist_assignments_tag
    ON playlist_assignments(tag_id, playlist_id)
    WHERE tag_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_playlist_assignments_priority
    ON playlist_assignments(playlist_id, priority DESC);

COMMENT ON INDEX idx_content_tags_composite IS
    'Optimizes: Get all tags for a content';
COMMENT ON INDEX idx_content_tags_reverse IS
    'Optimizes: Get all contents for a tag';
COMMENT ON INDEX idx_playlist_contents_order IS
    'Optimizes: Get ordered contents in playlist';
COMMENT ON INDEX idx_playlist_assignments_device IS
    'Get playlists assigned to specific device';
COMMENT ON INDEX idx_playlist_assignments_tag IS
    'Get playlists assigned to tag';

-- ============================================================================
-- 6. USER_SESSIONS TABLE - Authentication Queries
-- ============================================================================

-- Get active sessions by user
CREATE INDEX IF NOT EXISTS idx_sessions_user_active
    ON user_sessions(user_id, created_at DESC)
    WHERE revoked_at IS NULL AND expires_at > NOW();

-- Session token lookup (most frequent)
CREATE INDEX IF NOT EXISTS idx_sessions_token_active
    ON user_sessions(session_token)
    WHERE revoked_at IS NULL AND expires_at > NOW();

-- Organization-wide session tracking
CREATE INDEX IF NOT EXISTS idx_sessions_org_active
    ON user_sessions(organization_id, last_activity DESC)
    WHERE revoked_at IS NULL AND expires_at > NOW();

COMMENT ON INDEX idx_sessions_user_active IS
    'Get active sessions for user (for "active devices" feature)';
COMMENT ON INDEX idx_sessions_token_active IS
    'Fast token validation on every API request';
COMMENT ON INDEX idx_sessions_org_active IS
    'Organization-wide session monitoring';

-- ============================================================================
-- 7. CONTENT_PLAYBACK_LOGS TABLE - Analytics Queries
-- ============================================================================

-- Time-series analytics (most common)
CREATE INDEX IF NOT EXISTS idx_playback_org_date
    ON content_playback_logs(organization_id, started_at DESC);

-- Content performance by date range
CREATE INDEX IF NOT EXISTS idx_playback_content_completed
    ON content_playback_logs(content_id, completed, started_at DESC);

-- Device engagement tracking
CREATE INDEX IF NOT EXISTS idx_playback_device_date
    ON content_playback_logs(device_id, started_at DESC);

-- Playlist analytics
CREATE INDEX IF NOT EXISTS idx_playback_playlist_stats
    ON content_playback_logs(playlist_id, completed, started_at DESC)
    WHERE playlist_id IS NOT NULL;

COMMENT ON INDEX idx_playback_org_date IS
    'Organization-wide playback analytics';
COMMENT ON INDEX idx_playback_content_completed IS
    'Content completion rate analysis';
COMMENT ON INDEX idx_playback_device_date IS
    'Device engagement tracking';
COMMENT ON INDEX idx_playback_playlist_stats IS
    'Playlist performance analytics';

-- ============================================================================
-- 8. ROLES TABLE - RBAC Queries
-- ============================================================================

-- Get roles by organization
CREATE INDEX IF NOT EXISTS idx_roles_org_system
    ON roles(organization_id, is_system_role, name);

-- Permission-based queries (JSONB GIN index)
CREATE INDEX IF NOT EXISTS idx_roles_permissions
    ON roles USING gin(permissions);

COMMENT ON INDEX idx_roles_org_system IS
    'List roles by organization (system vs custom)';
COMMENT ON INDEX idx_roles_permissions IS
    'Fast permission lookup in JSONB field';

-- ============================================================================
-- 9. AUDIT_LOGS TABLE - Activity Tracking
-- ============================================================================

-- Most common: Recent activity by organization
CREATE INDEX IF NOT EXISTS idx_audit_org_date
    ON audit_logs(organization_id, created_at DESC);

-- Filter by action type
CREATE INDEX IF NOT EXISTS idx_audit_org_action
    ON audit_logs(organization_id, action, created_at DESC);

-- User activity tracking
CREATE INDEX IF NOT EXISTS idx_audit_user_date
    ON audit_logs(user_id, created_at DESC)
    WHERE user_id IS NOT NULL;

-- Entity-specific audit trail
CREATE INDEX IF NOT EXISTS idx_audit_entity
    ON audit_logs(entity_type, entity_id, created_at DESC);

COMMENT ON INDEX idx_audit_org_date IS
    'Recent activity timeline by organization';
COMMENT ON INDEX idx_audit_org_action IS
    'Filter audit logs by action type';
COMMENT ON INDEX idx_audit_user_date IS
    'User activity history';
COMMENT ON INDEX idx_audit_entity IS
    'Entity-specific audit trail (e.g., content edit history)';

-- ============================================================================
-- 10. DEVICE SUPPORT TABLES - Monitoring & Logs
-- ============================================================================

-- Device commands queue
CREATE INDEX IF NOT EXISTS idx_device_commands_pending
    ON device_commands(device_id, status, created_at DESC)
    WHERE status IN ('pending', 'sent');

-- Device logs (recent first)
CREATE INDEX IF NOT EXISTS idx_device_logs_recent
    ON device_logs(device_id, created_at DESC);

-- Speed test history
CREATE INDEX IF NOT EXISTS idx_speed_tests_device_date
    ON device_speed_tests(device_id, tested_at DESC);

COMMENT ON INDEX idx_device_commands_pending IS
    'Get pending commands for device polling';
COMMENT ON INDEX idx_device_logs_recent IS
    'Recent logs for device debugging';
COMMENT ON INDEX idx_speed_tests_device_date IS
    'Speed test history timeline';

-- ============================================================================
-- 11. VERIFICATION QUERIES
-- ============================================================================

-- Count total indexes created
SELECT
    schemaname,
    tablename,
    indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexname LIKE 'idx_%composite%'
   OR indexname LIKE 'idx_%org_%'
   OR indexname LIKE 'idx_%active%'
ORDER BY tablename, indexname;

-- Analyze index usage (run after some production traffic)
/*
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
*/

COMMIT;

-- ============================================================================
-- ROLLBACK SCRIPT
-- ============================================================================
/*
BEGIN;

-- Contents
DROP INDEX IF EXISTS idx_contents_org_active;
DROP INDEX IF EXISTS idx_contents_org_type;
DROP INDEX IF EXISTS idx_contents_title_search;
DROP INDEX IF EXISTS idx_contents_storage_key;

-- Devices
DROP INDEX IF EXISTS idx_devices_org_status;
DROP INDEX IF EXISTS idx_devices_org_location;
DROP INDEX IF EXISTS idx_devices_activation;

-- Playlists
DROP INDEX IF EXISTS idx_playlists_org_active;
DROP INDEX IF EXISTS idx_playlists_org_priority;

-- Tags
DROP INDEX IF EXISTS idx_tags_org_name;

-- Junction tables
DROP INDEX IF EXISTS idx_content_tags_composite;
DROP INDEX IF EXISTS idx_content_tags_reverse;
DROP INDEX IF EXISTS idx_device_tags_composite;
DROP INDEX IF EXISTS idx_device_tags_reverse;
DROP INDEX IF EXISTS idx_playlist_contents_order;
DROP INDEX IF EXISTS idx_playlist_contents_reverse;
DROP INDEX IF EXISTS idx_playlist_assignments_device;
DROP INDEX IF EXISTS idx_playlist_assignments_tag;
DROP INDEX IF EXISTS idx_playlist_assignments_priority;

-- User sessions
DROP INDEX IF EXISTS idx_sessions_user_active;
DROP INDEX IF EXISTS idx_sessions_token_active;
DROP INDEX IF EXISTS idx_sessions_org_active;

-- Playback logs
DROP INDEX IF EXISTS idx_playback_org_date;
DROP INDEX IF EXISTS idx_playback_content_completed;
DROP INDEX IF EXISTS idx_playback_device_date;
DROP INDEX IF EXISTS idx_playback_playlist_stats;

-- Roles
DROP INDEX IF EXISTS idx_roles_org_system;
DROP INDEX IF EXISTS idx_roles_permissions;

-- Audit logs
DROP INDEX IF EXISTS idx_audit_org_date;
DROP INDEX IF EXISTS idx_audit_org_action;
DROP INDEX IF EXISTS idx_audit_user_date;
DROP INDEX IF EXISTS idx_audit_entity;

-- Device support
DROP INDEX IF EXISTS idx_device_commands_pending;
DROP INDEX IF EXISTS idx_device_logs_recent;
DROP INDEX IF EXISTS idx_speed_tests_device_date;

COMMIT;
*/

-- ============================================================================
-- PERFORMANCE IMPACT ANALYSIS
-- ============================================================================
/*
Expected Performance Improvements:
1. Dashboard queries: 5-10x faster (organization + status filters)
2. Content search: 20-50x faster (full-text search index)
3. Playlist assignment: 3-5x faster (composite indexes on junction tables)
4. Analytics queries: 10-20x faster (time-series indexes)
5. Session validation: 2-3x faster (partial index on active sessions)

Trade-offs:
- Write operations: 10-15% slower (more indexes to update)
- Storage: ~5-10% increase (index overhead)
- Benefit: Read-heavy workload (90% reads, 10% writes) - NET WIN!
*/

-- ============================================================================
-- Migration Complete
-- ============================================================================

-- To run this migration on server:
-- docker exec -i signage-postgres psql -U signage_user -d signage_db < database/fix-database/migrations/015_add_composite_indexes.sql
