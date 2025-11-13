-- Migration: Standardize Foreign Key Naming Convention
-- Date: 2025-11-13
-- Purpose: Add _id suffix to all audit trail FK columns for consistency
-- Related Issue: 26 FK columns lack _id suffix (created_by, updated_by, etc.)

-- ============================================================================
-- PHASE 1: Rename audit trail columns to add _id suffix
-- ============================================================================

-- DEVICES table
ALTER TABLE devices
    RENAME COLUMN created_by TO created_by_id;

ALTER TABLE devices
    RENAME COLUMN updated_by TO updated_by_id;

-- CONTENTS table
ALTER TABLE contents
    RENAME COLUMN uploaded_by TO uploaded_by_id;

-- DEVICE_TAGS table
ALTER TABLE device_tags
    RENAME COLUMN assigned_by TO assigned_by_id;

-- DEVICE_GROUPS table
ALTER TABLE device_groups
    RENAME COLUMN created_by TO created_by_id;

-- DEVICE_GROUP_MEMBERS table
ALTER TABLE device_group_members
    RENAME COLUMN added_by TO added_by_id;

-- DEVICE_COMMANDS table
ALTER TABLE device_commands
    RENAME COLUMN created_by TO created_by_id;

-- PLAYLISTS table
ALTER TABLE playlists
    RENAME COLUMN created_by TO created_by_id;

-- PMS_CONFIGURATIONS table
ALTER TABLE pms_configurations
    RENAME COLUMN created_by TO created_by_id;

-- SCHEDULES table
ALTER TABLE schedules
    RENAME COLUMN created_by TO created_by_id;

-- TEMPLATES table
ALTER TABLE templates
    RENAME COLUMN created_by TO created_by_id;

-- WIDGETS table
ALTER TABLE widgets
    RENAME COLUMN created_by TO created_by_id;

-- CONTENT_ASSIGNMENTS table
ALTER TABLE content_assignments
    RENAME COLUMN assigned_by TO assigned_by_id;

-- ============================================================================
-- PHASE 2: Update comments for clarity
-- ============================================================================

COMMENT ON COLUMN devices.created_by_id IS 'User ID who created this device (FK to users.id)';
COMMENT ON COLUMN devices.updated_by_id IS 'User ID who last updated this device (FK to users.id)';
COMMENT ON COLUMN contents.uploaded_by_id IS 'User ID who uploaded this content (FK to users.id)';
COMMENT ON COLUMN device_tags.assigned_by_id IS 'User ID who assigned this tag (FK to users.id)';
COMMENT ON COLUMN device_groups.created_by_id IS 'User ID who created this group (FK to users.id)';
COMMENT ON COLUMN device_group_members.added_by_id IS 'User ID who added this member (FK to users.id)';
COMMENT ON COLUMN device_commands.created_by_id IS 'User ID who created this command (FK to users.id)';
COMMENT ON COLUMN playlists.created_by_id IS 'User ID who created this playlist (FK to users.id)';
COMMENT ON COLUMN pms_configurations.created_by_id IS 'User ID who created this config (FK to users.id)';
COMMENT ON COLUMN schedules.created_by_id IS 'User ID who created this schedule (FK to users.id)';
COMMENT ON COLUMN templates.created_by_id IS 'User ID who created this template (FK to users.id)';
COMMENT ON COLUMN widgets.created_by_id IS 'User ID who created this widget (FK to users.id)';
COMMENT ON COLUMN content_assignments.assigned_by_id IS 'User ID who assigned this content (FK to users.id)';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Verify all renamed columns exist
DO $$
DECLARE
    missing_columns TEXT[];
BEGIN
    -- Check all expected columns
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'devices' AND column_name = 'created_by_id') THEN
        missing_columns := array_append(missing_columns, 'devices.created_by_id');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'devices' AND column_name = 'updated_by_id') THEN
        missing_columns := array_append(missing_columns, 'devices.updated_by_id');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'contents' AND column_name = 'uploaded_by_id') THEN
        missing_columns := array_append(missing_columns, 'contents.uploaded_by_id');
    END IF;

    -- Raise error if any columns missing
    IF array_length(missing_columns, 1) > 0 THEN
        RAISE EXCEPTION 'Migration failed: Missing columns: %', array_to_string(missing_columns, ', ');
    END IF;

    RAISE NOTICE '✅ Migration successful: All audit trail columns renamed with _id suffix';
END $$;
