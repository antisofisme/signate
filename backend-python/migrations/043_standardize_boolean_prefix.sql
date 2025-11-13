-- Migration 043: Standardize Boolean Column Naming (Add is_ Prefix)
-- Phase 3: Boolean Prefix Standardization
-- Purpose: Ensure all boolean columns follow is_* naming convention for clarity
-- Score Impact: +3 points (90 → 93)

-- ============================================================================
-- OVERVIEW
-- ============================================================================
-- This migration renames 3 boolean columns to follow the is_* prefix convention:
-- 1. devices.volume_enabled → is_volume_enabled
-- 2. devices.supports_personalization → is_personalization_supported
-- 3. device_health_metrics.alert_triggered → is_alert_triggered
--
-- Note: device_commands.completed does NOT exist in current schema
--       (uses status VARCHAR instead of boolean)
-- ============================================================================


-- ============================================================================
-- PHASE 1: RENAME BOOLEAN COLUMNS
-- ============================================================================

-- 1. Rename devices.volume_enabled → is_volume_enabled
ALTER TABLE devices
    RENAME COLUMN volume_enabled TO is_volume_enabled;

-- 2. Rename devices.supports_personalization → is_personalization_supported
ALTER TABLE devices
    RENAME COLUMN supports_personalization TO is_personalization_supported;

-- 3. Rename device_health_metrics.alert_triggered → is_alert_triggered
ALTER TABLE device_health_metrics
    RENAME COLUMN alert_triggered TO is_alert_triggered;


-- ============================================================================
-- PHASE 2: UPDATE COLUMN COMMENTS
-- ============================================================================

-- Update comments to explain boolean meaning clearly
COMMENT ON COLUMN devices.is_volume_enabled IS
    'TRUE if device audio/volume is enabled, FALSE if muted/disabled';

COMMENT ON COLUMN devices.is_personalization_supported IS
    'TRUE if device supports PMS guest personalization features, FALSE otherwise';

COMMENT ON COLUMN device_health_metrics.is_alert_triggered IS
    'TRUE if health metric triggered an alert condition, FALSE if healthy';


-- ============================================================================
-- PHASE 3: VERIFICATION
-- ============================================================================

-- Verify all boolean columns now have is_ prefix
DO $$
DECLARE
    non_prefixed_booleans INTEGER;
    total_boolean_columns INTEGER;
BEGIN
    -- Count boolean columns without is_ prefix (excluding system columns and special cases)
    SELECT COUNT(*) INTO non_prefixed_booleans
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND data_type = 'boolean'
      AND column_name NOT LIKE 'is_%'
      -- Exclude known exceptions
      AND column_name NOT IN (
          'active',           -- status field, not boolean predicate
          'enabled',          -- when part of feature name (e.g., 'sms_enabled')
          'deleted',          -- soft delete flag
          'read',             -- notifications.read (acceptable)
          'verified'          -- user.verified (acceptable)
      );

    -- Count total boolean columns
    SELECT COUNT(*) INTO total_boolean_columns
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND data_type = 'boolean';

    -- Report results
    RAISE NOTICE '====================================';
    RAISE NOTICE 'BOOLEAN COLUMN STANDARDIZATION';
    RAISE NOTICE '====================================';
    RAISE NOTICE 'Total boolean columns: %', total_boolean_columns;
    RAISE NOTICE 'Non-prefixed booleans: %', non_prefixed_booleans;

    IF non_prefixed_booleans = 0 THEN
        RAISE NOTICE 'SUCCESS: All boolean columns follow naming convention!';
    ELSE
        RAISE NOTICE 'WARNING: % boolean columns still need review', non_prefixed_booleans;
    END IF;
    RAISE NOTICE '====================================';
END $$;


-- ============================================================================
-- ROLLBACK INSTRUCTIONS
-- ============================================================================
-- To rollback this migration, run:
/*
ALTER TABLE devices RENAME COLUMN is_volume_enabled TO volume_enabled;
ALTER TABLE devices RENAME COLUMN is_personalization_supported TO supports_personalization;
ALTER TABLE device_health_metrics RENAME COLUMN is_alert_triggered TO alert_triggered;

-- Restore original comments
COMMENT ON COLUMN devices.volume_enabled IS 'Whether device audio is enabled';
COMMENT ON COLUMN devices.supports_personalization IS 'Whether device supports guest personalization';
COMMENT ON COLUMN device_health_metrics.alert_triggered IS 'Whether an alert was triggered';
*/


-- ============================================================================
-- POST-MIGRATION CHECKLIST
-- ============================================================================
-- [ ] Update Python models (DeviceModel, DeviceHealthMetricModel)
-- [ ] Update DTOs (DeviceDTO, DeviceUpdateDTO, HealthMetricDTO)
-- [ ] Update domain entities (Device, DeviceHealth)
-- [ ] Update repositories (device_repo.py, device_health_repo.py)
-- [ ] Update use cases (update_device.py, request_activation_code.py)
-- [ ] Update routes (routes.py, command_routes.py)
-- [ ] Update frontend TypeScript types
-- [ ] Run backend tests
-- [ ] Run integration tests
-- [ ] Update API documentation
