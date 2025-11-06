-- ============================================================================
-- Rollback Migration 009: Phase 4.1 - Template Variables System
-- ============================================================================
-- Author: Database Administrator
-- Date: 2025-10-28
-- Purpose: Safely rollback template system changes
--
-- WARNING: This will DELETE all template data!
-- Backup your data before running this rollback!
-- ============================================================================

BEGIN;

-- ============================================================================
-- Step 1: Drop Triggers
-- ============================================================================

DROP TRIGGER IF EXISTS trg_device_custom_variables_updated_at ON device_custom_variables;
DROP TRIGGER IF EXISTS trg_custom_variables_updated_at ON custom_variables;
DROP TRIGGER IF EXISTS trg_content_templates_updated_at ON content_templates;

-- Drop trigger function
DROP FUNCTION IF EXISTS update_template_updated_at();

-- ============================================================================
-- Step 2: Drop Views
-- ============================================================================

DROP VIEW IF EXISTS template_security_summary CASCADE;
DROP VIEW IF EXISTS template_usage_stats CASCADE;

-- ============================================================================
-- Step 3: Drop Functions
-- ============================================================================

DROP FUNCTION IF EXISTS validate_variable_name(VARCHAR);
DROP FUNCTION IF EXISTS calculate_context_hash(JSONB);
DROP FUNCTION IF EXISTS get_template_context(INTEGER, BOOLEAN);

-- ============================================================================
-- Step 4: Remove Columns from Contents Table
-- ============================================================================

ALTER TABLE contents DROP COLUMN IF EXISTS template_id;
ALTER TABLE contents DROP COLUMN IF EXISTS use_template;

-- ============================================================================
-- Step 5: Drop Tables (in reverse dependency order)
-- ============================================================================

-- Drop security log (no dependencies)
DROP TABLE IF EXISTS template_security_log CASCADE;

-- Drop device variables (depends on custom_variables)
DROP TABLE IF EXISTS device_custom_variables CASCADE;

-- Drop custom variables (no dependencies after device_custom_variables)
DROP TABLE IF EXISTS custom_variables CASCADE;

-- Drop template renders (partitioned table with partitions)
DROP TABLE IF EXISTS template_renders CASCADE;  -- This drops all partitions too

-- Drop content templates (no dependencies after template_renders)
DROP TABLE IF EXISTS content_templates CASCADE;

-- ============================================================================
-- Step 6: Clean up any orphaned sequences
-- ============================================================================

-- These should be auto-dropped with tables, but ensure cleanup
DROP SEQUENCE IF EXISTS content_templates_id_seq CASCADE;
DROP SEQUENCE IF EXISTS custom_variables_id_seq CASCADE;
DROP SEQUENCE IF EXISTS device_custom_variables_id_seq CASCADE;

COMMIT;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- 1. Verify all tables were dropped
SELECT
    'Table Cleanup Check' as check_type,
    COUNT(CASE WHEN table_name = 'content_templates' THEN 1 END) as content_templates_exists,
    COUNT(CASE WHEN table_name = 'template_renders' THEN 1 END) as template_renders_exists,
    COUNT(CASE WHEN table_name = 'custom_variables' THEN 1 END) as custom_variables_exists,
    COUNT(CASE WHEN table_name = 'device_custom_variables' THEN 1 END) as device_custom_variables_exists,
    COUNT(CASE WHEN table_name = 'template_security_log' THEN 1 END) as template_security_log_exists
FROM information_schema.tables
WHERE table_schema = 'public';
-- All counts should be 0

-- 2. Verify columns were removed from contents
SELECT
    column_name
FROM information_schema.columns
WHERE table_name = 'contents'
AND column_name IN ('use_template', 'template_id');
-- Should return no rows

-- 3. Verify functions were dropped
SELECT
    routine_name
FROM information_schema.routines
WHERE routine_name IN ('get_template_context', 'calculate_context_hash', 'validate_variable_name');
-- Should return no rows

-- 4. Verify views were dropped
SELECT
    table_name
FROM information_schema.views
WHERE table_name IN ('template_usage_stats', 'template_security_summary');
-- Should return no rows

-- 5. Verify no orphaned partitions
SELECT
    parent.relname as parent_table,
    child.relname as partition_name
FROM pg_inherits
JOIN pg_class parent ON pg_inherits.inhparent = parent.oid
JOIN pg_class child ON pg_inherits.inhrelid = child.oid
WHERE parent.relname = 'template_renders';
-- Should return no rows

-- ============================================================================
-- Rollback Summary
-- ============================================================================
-- This rollback successfully:
-- ✅ Dropped 3 triggers
-- ✅ Dropped 2 views
-- ✅ Dropped 3 functions
-- ✅ Removed 2 columns from contents table
-- ✅ Dropped 5 tables (including partitioned table with all partitions)
-- ✅ Cleaned up sequences
--
-- System restored to pre-Migration 009 state.
--
-- ⚠️ DATA LOSS WARNING:
-- - All template definitions deleted
-- - All template render history deleted
-- - All custom variables deleted
-- - All device variable assignments deleted
-- - All security audit logs deleted
-- ============================================================================
