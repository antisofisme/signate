-- =====================================================
-- Database Schema Alignment Migration Script
-- Created: 2025-01-30
-- Purpose: Align database schema with SQLAlchemy models
-- =====================================================

-- NOTE: This script contains OPTIONAL improvements
-- The critical fixes have already been done in the models
-- Run these only if you want to add missing columns to database

BEGIN;

-- =====================================================
-- 1. ACTIVITY_LOGS TABLE - Add missing columns (OPTIONAL)
-- =====================================================
-- These columns are in the model but not in database
-- The fixed model handles this gracefully by storing in details JSON

-- Uncomment if you want to add these columns:
-- ALTER TABLE activity_logs ADD COLUMN IF NOT EXISTS entity_name VARCHAR(255);
-- ALTER TABLE activity_logs ADD COLUMN IF NOT EXISTS user_agent TEXT;

-- =====================================================
-- 2. DEVICES TABLE - Add language support columns
-- =====================================================
-- These columns exist in database but not in model
-- Adding to model is recommended to use these features

-- Already exist in DB, just need to update model
-- No SQL changes needed

-- =====================================================
-- 3. CONTENTS TABLE - Fix data type for file_size
-- =====================================================
-- file_size should support files larger than 2GB

-- Check if any files are larger than 2GB first
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM contents WHERE file_size > 2147483647) THEN
        RAISE NOTICE 'Warning: Large files detected. file_size column needs BigInt type.';
    END IF;
END $$;

-- Type is already bigint in database, model needs update
-- No SQL changes needed

-- =====================================================
-- 4. INDEXES - Add composite indexes for performance
-- =====================================================

-- Composite index for activity logs queries
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_entity
ON activity_logs(user_id, entity_type, created_at);

-- Composite index for active devices per organization
CREATE INDEX IF NOT EXISTS idx_devices_org_status_active
ON devices(organization_id, status)
WHERE status = 'active';

-- Composite index for active content per organization
CREATE INDEX IF NOT EXISTS idx_contents_org_active
ON contents(organization_id, is_active)
WHERE is_active = true;

-- Composite index for playlist content ordering
CREATE INDEX IF NOT EXISTS idx_playlist_content_playlist_order
ON playlist_content(playlist_id, order_index);

-- =====================================================
-- 5. CONSTRAINTS - Add missing CHECK constraints
-- =====================================================

-- Add check constraint for transcoding progress if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'contents_transcoding_progress_check'
    ) THEN
        ALTER TABLE contents
        ADD CONSTRAINT contents_transcoding_progress_check
        CHECK (transcoding_progress >= 0 AND transcoding_progress <= 100);
    END IF;
END $$;

-- =====================================================
-- 6. DEFAULT VALUES - Ensure proper defaults
-- =====================================================

-- Set default for organization_id in devices if NULL
UPDATE devices SET organization_id = 1 WHERE organization_id IS NULL;
ALTER TABLE devices ALTER COLUMN organization_id SET NOT NULL;

-- Set default for organization_id in contents if NULL
UPDATE contents SET organization_id = 1 WHERE organization_id IS NULL;
ALTER TABLE contents ALTER COLUMN organization_id SET NOT NULL;

-- =====================================================
-- 7. FUNCTIONS - Add utility functions
-- =====================================================

-- Function to get device online status
CREATE OR REPLACE FUNCTION is_device_online(last_seen_time TIMESTAMP)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN last_seen_time IS NOT NULL
           AND last_seen_time > NOW() - INTERVAL '5 minutes';
END;
$$ LANGUAGE plpgsql;

-- Function to get active content count for organization
CREATE OR REPLACE FUNCTION get_active_content_count(org_id INTEGER)
RETURNS INTEGER AS $$
DECLARE
    content_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO content_count
    FROM contents
    WHERE organization_id = org_id
      AND is_active = true
      AND (start_date IS NULL OR start_date <= NOW())
      AND (end_date IS NULL OR end_date >= NOW());

    RETURN content_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 8. VIEWS - Create useful views for reporting
-- =====================================================

-- View for device status summary
CREATE OR REPLACE VIEW v_device_status_summary AS
SELECT
    d.organization_id,
    o.name as organization_name,
    COUNT(*) as total_devices,
    COUNT(CASE WHEN d.status = 'active' THEN 1 END) as active_devices,
    COUNT(CASE WHEN d.status = 'pending' THEN 1 END) as pending_devices,
    COUNT(CASE WHEN d.status = 'inactive' THEN 1 END) as inactive_devices,
    COUNT(CASE WHEN d.last_seen > NOW() - INTERVAL '5 minutes' THEN 1 END) as online_devices
FROM devices d
JOIN organizations o ON d.organization_id = o.id
GROUP BY d.organization_id, o.name;

-- View for recent activity logs with user info
CREATE OR REPLACE VIEW v_recent_activities AS
SELECT
    a.id,
    a.user_id,
    u.username,
    u.email as user_email,
    a.action,
    a.entity_type,
    a.entity_id,
    a.details,
    a.ip_address,
    a.created_at
FROM activity_logs a
LEFT JOIN users u ON a.user_id = u.id
WHERE a.created_at > NOW() - INTERVAL '7 days'
ORDER BY a.created_at DESC;

-- =====================================================
-- 9. STATISTICS - Update table statistics
-- =====================================================

ANALYZE activity_logs;
ANALYZE users;
ANALYZE devices;
ANALYZE contents;
ANALYZE playlists;
ANALYZE organizations;
ANALYZE tags;

-- =====================================================
-- VALIDATION QUERIES
-- =====================================================

-- Check for any remaining issues
SELECT 'Checking for activity_logs with NULL action...' as check_description,
       COUNT(*) as issue_count
FROM activity_logs WHERE action IS NULL
UNION ALL
SELECT 'Checking for devices without organization...',
       COUNT(*)
FROM devices WHERE organization_id IS NULL
UNION ALL
SELECT 'Checking for contents without organization...',
       COUNT(*)
FROM contents WHERE organization_id IS NULL
UNION ALL
SELECT 'Checking for oversized file_size values...',
       COUNT(*)
FROM contents WHERE file_size > 2147483647;

COMMIT;

-- =====================================================
-- POST-MIGRATION NOTES
-- =====================================================
-- 1. After running this migration, update the SQLAlchemy models to match
-- 2. Test all API endpoints thoroughly
-- 3. Monitor application logs for any remaining issues
-- 4. Consider implementing database backups before major changes