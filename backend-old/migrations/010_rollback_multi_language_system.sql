-- ============================================================================
-- Rollback Migration 010: Phase 4.2 - Multi-Language Content System
-- ============================================================================
-- Author: Database Administrator
-- Date: 2025-10-28
-- Purpose: Safely rollback multi-language system changes
--
-- WARNING: This will DELETE all translation data!
-- Backup your data before running this rollback!
-- ============================================================================

BEGIN;

-- ============================================================================
-- Step 1: Drop Triggers
-- ============================================================================

DROP TRIGGER IF EXISTS trg_enforce_single_primary ON content_translations;
DROP TRIGGER IF EXISTS trg_language_settings_updated_at ON language_settings;
DROP TRIGGER IF EXISTS trg_content_translations_updated_at ON content_translations;

-- Drop trigger functions
DROP FUNCTION IF EXISTS enforce_single_primary_translation();
DROP FUNCTION IF EXISTS update_translation_updated_at();

-- ============================================================================
-- Step 2: Drop Views
-- ============================================================================

DROP VIEW IF EXISTS translation_completeness CASCADE;
DROP VIEW IF EXISTS language_usage_stats CASCADE;
DROP VIEW IF EXISTS translation_coverage CASCADE;

-- ============================================================================
-- Step 3: Drop Functions
-- ============================================================================

DROP FUNCTION IF EXISTS get_device_languages(INTEGER);
DROP FUNCTION IF EXISTS has_translation(INTEGER, VARCHAR);
DROP FUNCTION IF EXISTS get_content_languages(INTEGER);
DROP FUNCTION IF EXISTS get_content_translation(INTEGER, VARCHAR, VARCHAR);

-- ============================================================================
-- Step 4: Remove Columns from Tables
-- ============================================================================

-- Remove language columns from devices table
ALTER TABLE devices DROP COLUMN IF EXISTS rotation_interval;
ALTER TABLE devices DROP COLUMN IF EXISTS language_rotation;
ALTER TABLE devices DROP COLUMN IF EXISTS secondary_language;
ALTER TABLE devices DROP COLUMN IF EXISTS primary_language;

-- Remove default_language from contents table
ALTER TABLE contents DROP COLUMN IF EXISTS default_language;

-- ============================================================================
-- Step 5: Drop Tables (in reverse dependency order)
-- ============================================================================

-- Drop translation import history (no dependencies)
DROP TABLE IF EXISTS translation_import_history CASCADE;

-- Drop language settings (no dependencies)
DROP TABLE IF EXISTS language_settings CASCADE;

-- Drop content translations (references contents)
DROP TABLE IF EXISTS content_translations CASCADE;

-- ============================================================================
-- Step 6: Clean up any orphaned sequences
-- ============================================================================

-- These should be auto-dropped with tables, but ensure cleanup
DROP SEQUENCE IF EXISTS content_translations_id_seq CASCADE;
DROP SEQUENCE IF EXISTS language_settings_id_seq CASCADE;
DROP SEQUENCE IF EXISTS translation_import_history_id_seq CASCADE;

-- ============================================================================
-- Step 7: Drop Indexes (if they weren't cascade-deleted)
-- ============================================================================

-- These should be auto-dropped with tables, but explicit cleanup for safety
DROP INDEX IF EXISTS idx_content_translations_title_gin;
DROP INDEX IF EXISTS idx_content_translations_description_gin;
DROP INDEX IF EXISTS idx_content_translations_lookup;
DROP INDEX IF EXISTS idx_content_translations_content_lang;
DROP INDEX IF EXISTS idx_content_translations_is_primary;
DROP INDEX IF EXISTS idx_content_translations_language;
DROP INDEX IF EXISTS idx_content_translations_content_id;
DROP INDEX IF EXISTS idx_devices_primary_language;
DROP INDEX IF EXISTS idx_devices_language_rotation;
DROP INDEX IF EXISTS idx_language_settings_is_enabled;
DROP INDEX IF EXISTS idx_language_settings_sort_order;
DROP INDEX IF EXISTS idx_language_settings_code;
DROP INDEX IF EXISTS idx_translation_import_imported_by;
DROP INDEX IF EXISTS idx_translation_import_imported_at;
DROP INDEX IF EXISTS idx_contents_default_language;

COMMIT;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- 1. Verify all tables were dropped
SELECT
    'Table Cleanup Check' as check_type,
    COUNT(CASE WHEN table_name = 'content_translations' THEN 1 END) as content_translations_exists,
    COUNT(CASE WHEN table_name = 'language_settings' THEN 1 END) as language_settings_exists,
    COUNT(CASE WHEN table_name = 'translation_import_history' THEN 1 END) as translation_import_history_exists
FROM information_schema.tables
WHERE table_schema = 'public';
-- All counts should be 0

-- 2. Verify columns were removed from devices
SELECT
    column_name
FROM information_schema.columns
WHERE table_name = 'devices'
AND column_name IN ('primary_language', 'secondary_language', 'language_rotation', 'rotation_interval');
-- Should return no rows

-- 3. Verify columns were removed from contents
SELECT
    column_name
FROM information_schema.columns
WHERE table_name = 'contents'
AND column_name IN ('default_language');
-- Should return no rows

-- 4. Verify functions were dropped
SELECT
    routine_name
FROM information_schema.routines
WHERE routine_name IN ('get_content_translation', 'get_content_languages',
                       'has_translation', 'get_device_languages');
-- Should return no rows

-- 5. Verify views were dropped
SELECT
    table_name
FROM information_schema.views
WHERE table_name IN ('translation_coverage', 'language_usage_stats', 'translation_completeness');
-- Should return no rows

-- 6. Verify triggers were dropped
SELECT
    trigger_name,
    event_object_table
FROM information_schema.triggers
WHERE trigger_name IN ('trg_content_translations_updated_at',
                       'trg_language_settings_updated_at',
                       'trg_enforce_single_primary');
-- Should return no rows

-- 7. Verify indexes were dropped
SELECT
    schemaname,
    tablename,
    indexname
FROM pg_indexes
WHERE indexname LIKE '%language%'
OR indexname LIKE '%translation%'
ORDER BY tablename, indexname;
-- Should return no rows (or only unrelated indexes)

-- ============================================================================
-- Rollback Summary
-- ============================================================================
-- This rollback successfully:
-- ✅ Dropped 3 triggers
-- ✅ Dropped 3 views
-- ✅ Dropped 4 functions
-- ✅ Removed 4 columns from devices table
-- ✅ Removed 1 column from contents table
-- ✅ Dropped 3 tables
-- ✅ Cleaned up sequences
-- ✅ Cleaned up indexes
--
-- System restored to pre-Migration 010 state.
--
-- ⚠️ DATA LOSS WARNING:
-- - All content translations deleted
-- - All language settings deleted
-- - All translation import history deleted
-- - Device language preferences removed
--
-- Note: Original content titles and descriptions in contents table are preserved
-- ============================================================================
