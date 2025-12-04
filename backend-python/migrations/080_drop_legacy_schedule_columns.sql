-- Migration: 080
-- Description: Drop legacy JSONB columns after successful junction table migration
-- Date: 2025-12-04
-- Impact: IRREVERSIBLE - only run after confirming all apps use junction tables
-- WARNING: Run this ONLY after:
--   1. Migration 078 (create tables) deployed
--   2. Migration 079 (migrate data) completed
--   3. Backend updated to use junction tables
--   4. CMS updated to use target_devices/target_tags
--   5. Player updated to use new response format
--   6. Verified all data migrated correctly

BEGIN;

-- ============================================================================
-- SAFETY CHECK - Verify data migration completed
-- ============================================================================

-- This will fail if any schedule has device_ids but no junction records
DO $$
DECLARE
    orphan_device_count INTEGER;
    orphan_tag_count INTEGER;
BEGIN
    -- Check for schedules with device_ids not in junction table
    SELECT COUNT(*) INTO orphan_device_count
    FROM schedules s
    WHERE s.device_ids IS NOT NULL
      AND jsonb_array_length(s.device_ids) > 0
      AND NOT EXISTS (
          SELECT 1 FROM schedule_device_targeting sdt
          WHERE sdt.schedule_id = s.id
      );

    IF orphan_device_count > 0 THEN
        RAISE EXCEPTION 'Cannot drop columns: % schedules have device_ids not migrated to junction table', orphan_device_count;
    END IF;

    -- Check for schedules with tag_ids not in junction table
    SELECT COUNT(*) INTO orphan_tag_count
    FROM schedules s
    WHERE s.tag_ids IS NOT NULL
      AND jsonb_array_length(s.tag_ids) > 0
      AND NOT EXISTS (
          SELECT 1 FROM schedule_tag_targeting stt
          WHERE stt.schedule_id = s.id
      );

    IF orphan_tag_count > 0 THEN
        RAISE EXCEPTION 'Cannot drop columns: % schedules have tag_ids not migrated to junction table', orphan_tag_count;
    END IF;

    RAISE NOTICE 'Safety check passed: All targeting data migrated successfully';
END $$;

-- ============================================================================
-- DROP LEGACY COLUMNS
-- ============================================================================

-- Remove JSONB array columns (replaced by junction tables)
ALTER TABLE schedules DROP COLUMN IF EXISTS device_ids;
ALTER TABLE schedules DROP COLUMN IF EXISTS tag_ids;

-- ============================================================================
-- UPDATE TABLE COMMENT
-- ============================================================================

COMMENT ON TABLE schedules IS
    'Schedule definitions. Device/tag targeting now uses schedule_device_targeting and schedule_tag_targeting junction tables for proper referential integrity.';

COMMIT;

-- ============================================================================
-- NOTE: This migration is IRREVERSIBLE. The JSONB columns cannot be restored.
-- If rollback is needed, restore from backup before this migration.
-- ============================================================================
