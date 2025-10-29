-- Migration: Add Performance Indexes Phase 1
-- Date: 2025-10-28
-- Description: Add foreign key indexes, composite indexes, and partial indexes
--              for query performance optimization. Improves JOIN operations,
--              filtering by status, and device heartbeat checks.
-- Phase: 1 - Database Performance Optimization

BEGIN;

-- ============================================================================
-- PART 1: FOREIGN KEY INDEXES (Critical for JOIN performance)
-- ============================================================================
-- These indexes dramatically improve query performance for foreign key lookups
-- and JOIN operations across all major tables.

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
-- PART 2: COMPOSITE INDEXES FOR COMMON QUERIES
-- ============================================================================
-- These indexes optimize frequently used query patterns, reducing full table
-- scans and improving filter+sort operations.

-- Optimize content assignment lookups with active status (most frequent query)
-- Used for: Getting active content assignments for a device in display order
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_assignments_active_lookup
ON content_assignments(device_id, is_active, display_order)
WHERE is_active = true;

-- Optimize playlist content sequence retrieval
-- Used for: Fetching playlist content in order with content metadata
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_playlist_content_sequence
ON playlist_content(playlist_id, play_order, is_enabled)
WHERE is_enabled = true;

-- Optimize device heartbeat and online status checks
-- Used for: Determining which devices are currently online
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_devices_heartbeat
ON devices(last_seen DESC)
WHERE is_active = true;

-- Optimize scheduled content queries
-- Used for: Finding content that should be displayed based on schedule
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_schedule
ON content(is_active, start_date, end_date)
WHERE is_active = true;

-- Optimize playlist assignments for devices
-- Used for: Getting active playlists assigned to a device
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_playlist_assignments_active
ON playlist_assignments(device_id, is_active)
WHERE is_active = true;

-- ============================================================================
-- PART 3: PARTIAL INDEXES FOR ACTIVE CONTENT FILTERS
-- ============================================================================
-- These indexes are smaller (only index active rows) but provide significant
-- performance improvements for the most common filtering patterns.

-- Index for online devices (last seen within 5 minutes)
-- Used for: Dashboard, device status checks
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_devices_online
ON devices(id, name, last_seen)
WHERE is_active = true AND last_seen > NOW() - INTERVAL '5 minutes';

-- Index for pending device registrations
-- Used for: Admin device approval/activation workflow
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_devices_pending
ON devices(activation_code, created_at)
WHERE activation_code IS NOT NULL AND is_active = false;

-- Index for active content
-- Used for: Getting all active content items
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_active
ON content(created_at DESC)
WHERE is_active = true;

-- Index for scheduled playlists
-- Used for: Time-based playlist scheduling
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_playlists_scheduled
ON playlists(schedule_start, schedule_end, is_active)
WHERE schedule_start IS NOT NULL AND is_active = true;

-- ============================================================================
-- PART 4: ANALYZE TABLES FOR QUERY PLANNER
-- ============================================================================
-- Update statistics so PostgreSQL query planner makes optimal decisions.

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

-- ============================================================================
-- PART 5: CREATE EXTENDED STATISTICS FOR CORRELATED COLUMNS
-- ============================================================================
-- Help query planner understand relationships between columns.

CREATE STATISTICS IF NOT EXISTS stat_content_assignments_device_tag
ON device_id, tag_id FROM content_assignments;

CREATE STATISTICS IF NOT EXISTS stat_playlist_content_order
ON playlist_id, play_order FROM playlist_content;

CREATE STATISTICS IF NOT EXISTS stat_devices_active_lastseen
ON is_active, last_seen FROM devices;

-- ============================================================================
-- PART 6: VERIFICATION AND COMPLETION
-- ============================================================================
-- Log message for successful completion

DO $$
BEGIN
    RAISE NOTICE 'Migration 008: Performance indexes added successfully. Total indexes created: ~20+';
    RAISE NOTICE 'Key improvements:';
    RAISE NOTICE '  - Foreign key indexes for faster JOINs';
    RAISE NOTICE '  - Composite indexes for common query patterns';
    RAISE NOTICE '  - Partial indexes for active content filtering';
    RAISE NOTICE '  - Statistics updated for query planner optimization';
END $$;

COMMIT;
