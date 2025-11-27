-- Migration: 052
-- Description: Complete audit trail columns for all business features
-- Date: 2025-11-27
--
-- This migration adds missing audit columns identified in BUSINESS_FEATURES_ANALYSIS.md:
-- - Device Groups: updated_by_id, deleted_by_id
-- - Tags: deleted_at, deleted_by_id (soft delete)
-- - Playlists: updated_by_id
-- - Devices: deleted_at, deleted_by_id (soft delete)
-- - Schedules: deleted_at, deleted_by_id (soft delete)
-- - Content Tags: assigned_by_id

BEGIN;

-- =============================================================================
-- 1. DEVICE GROUPS - Add updated_by_id and deleted_by_id
-- =============================================================================

ALTER TABLE device_groups
ADD COLUMN IF NOT EXISTS updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE device_groups
ADD COLUMN IF NOT EXISTS deleted_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

COMMENT ON COLUMN device_groups.updated_by_id IS 'User who last modified this device group';
COMMENT ON COLUMN device_groups.deleted_by_id IS 'User who deleted this device group';

CREATE INDEX IF NOT EXISTS idx_device_groups_updated_by ON device_groups(updated_by_id);
CREATE INDEX IF NOT EXISTS idx_device_groups_deleted_by ON device_groups(deleted_by_id);

-- =============================================================================
-- 2. TAGS - Add soft delete columns
-- =============================================================================

ALTER TABLE tags
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE tags
ADD COLUMN IF NOT EXISTS deleted_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

COMMENT ON COLUMN tags.deleted_at IS 'Soft delete timestamp';
COMMENT ON COLUMN tags.deleted_by_id IS 'User who deleted this tag';

CREATE INDEX IF NOT EXISTS idx_tags_deleted_at ON tags(deleted_at);
CREATE INDEX IF NOT EXISTS idx_tags_deleted_by ON tags(deleted_by_id);

-- =============================================================================
-- 3. PLAYLISTS - Add updated_by_id
-- =============================================================================

ALTER TABLE playlists
ADD COLUMN IF NOT EXISTS updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

COMMENT ON COLUMN playlists.updated_by_id IS 'User who last modified this playlist';

CREATE INDEX IF NOT EXISTS idx_playlists_updated_by ON playlists(updated_by_id);

-- =============================================================================
-- 4. DEVICES - Add soft delete columns
-- =============================================================================

ALTER TABLE devices
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE devices
ADD COLUMN IF NOT EXISTS deleted_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

COMMENT ON COLUMN devices.deleted_at IS 'Soft delete timestamp';
COMMENT ON COLUMN devices.deleted_by_id IS 'User who deleted this device';

CREATE INDEX IF NOT EXISTS idx_devices_deleted_at ON devices(deleted_at);
CREATE INDEX IF NOT EXISTS idx_devices_deleted_by ON devices(deleted_by_id);

-- =============================================================================
-- 5. SCHEDULES - Add soft delete columns
-- =============================================================================

ALTER TABLE schedules
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE schedules
ADD COLUMN IF NOT EXISTS deleted_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

COMMENT ON COLUMN schedules.deleted_at IS 'Soft delete timestamp';
COMMENT ON COLUMN schedules.deleted_by_id IS 'User who deleted this schedule';

CREATE INDEX IF NOT EXISTS idx_schedules_deleted_at ON schedules(deleted_at);
CREATE INDEX IF NOT EXISTS idx_schedules_deleted_by ON schedules(deleted_by_id);

-- =============================================================================
-- 6. CONTENT TAGS - Add assigned_by_id for tracking who tagged content
-- =============================================================================

ALTER TABLE content_tags
ADD COLUMN IF NOT EXISTS assigned_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

COMMENT ON COLUMN content_tags.assigned_by_id IS 'User who assigned this tag to content';

CREATE INDEX IF NOT EXISTS idx_content_tags_assigned_by ON content_tags(assigned_by_id);

-- =============================================================================
-- 7. Update existing records with default values where needed
-- =============================================================================

-- No default value needed - NULL is acceptable for historical records

COMMIT;
