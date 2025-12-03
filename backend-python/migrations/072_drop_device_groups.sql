-- Migration: 072
-- Description: Drop Device Groups feature completely
-- Date: 2025-12-03
-- Reason: Device Groups was only for visual organization (not used in content flow)
--         Feature is being removed to simplify the system

BEGIN;

-- ============================================
-- 1. Drop Device Group Views and Tables (in correct order due to FK dependencies)
-- ============================================

-- Drop views first (they reference tables)
DROP VIEW IF EXISTS device_group_stats CASCADE;
DROP VIEW IF EXISTS device_group_hierarchy CASCADE;

-- Drop members table (references device_groups and devices)
DROP TABLE IF EXISTS device_group_members CASCADE;

-- Drop main device_groups table last
DROP TABLE IF EXISTS device_groups CASCADE;

-- ============================================
-- 2. Remove RBAC Permissions for device_groups
-- ============================================

-- Remove any role_permissions that reference device_groups
DELETE FROM role_permissions WHERE resource = 'device_groups';

-- ============================================
-- 3. Cleanup any orphaned indexes (if they still exist)
-- ============================================

-- These should be dropped with CASCADE, but just to be safe
DROP INDEX IF EXISTS idx_device_groups_org;
DROP INDEX IF EXISTS uix_device_group_member;
DROP INDEX IF EXISTS ix_device_group_members_device_id;
DROP INDEX IF EXISTS ix_device_group_members_group_id;

COMMIT;

-- ============================================
-- Verification Queries (run manually to verify)
-- ============================================
-- SELECT * FROM information_schema.tables WHERE table_name LIKE '%device_group%';
-- SELECT * FROM role_permissions WHERE resource = 'device_groups';
