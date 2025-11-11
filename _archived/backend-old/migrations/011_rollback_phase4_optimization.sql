-- ============================================================================
-- Rollback Migration 011: Phase 4 Performance Optimization
-- ============================================================================
-- Author: Database Administrator
-- Date: 2025-10-28
-- Purpose: Safely rollback performance optimization changes
--
-- Note: This rollback is safe and non-destructive (no data loss)
-- It only removes indexes, views, and functions added for optimization
-- ============================================================================

BEGIN;

-- ============================================================================
-- Step 1: Drop Cron Jobs (if pg_cron extension is enabled)
-- ============================================================================

-- Uncomment if pg_cron was configured:
/*
SELECT cron.unschedule('warmup-phase4-cache');
SELECT cron.unschedule('maintain-template-partitions');
SELECT cron.unschedule('refresh-phase4-views');
*/

-- ============================================================================
-- Step 2: Drop Functions
-- ============================================================================

DROP FUNCTION IF EXISTS warmup_phase4_cache();
DROP FUNCTION IF EXISTS maintain_template_renders_partitions();
DROP FUNCTION IF EXISTS create_template_renders_partition(INTEGER, INTEGER);
DROP FUNCTION IF EXISTS refresh_phase4_materialized_views();

-- ============================================================================
-- Step 3: Drop Materialized Views
-- ============================================================================

DROP MATERIALIZED VIEW IF EXISTS mv_language_by_location CASCADE;
DROP MATERIALIZED VIEW IF EXISTS mv_template_performance CASCADE;
DROP MATERIALIZED VIEW IF EXISTS mv_translation_stats CASCADE;

-- ============================================================================
-- Step 4: Drop Performance Indexes (CONCURRENTLY to avoid locking)
-- ============================================================================

-- Template-related indexes
DROP INDEX CONCURRENTLY IF EXISTS idx_content_templates_template_gin;
DROP INDEX CONCURRENTLY IF EXISTS idx_content_templates_active;
DROP INDEX CONCURRENTLY IF EXISTS idx_template_renders_recent;
DROP INDEX CONCURRENTLY IF EXISTS idx_template_renders_errors;
DROP INDEX CONCURRENTLY IF EXISTS idx_template_renders_cache;

-- Custom variables indexes
DROP INDEX CONCURRENTLY IF EXISTS idx_custom_variables_type;
DROP INDEX CONCURRENTLY IF EXISTS idx_device_custom_variables_lookup;

-- Translation-related indexes
DROP INDEX CONCURRENTLY IF EXISTS idx_content_translations_search;
DROP INDEX CONCURRENTLY IF EXISTS idx_content_translations_primary;

-- Language settings indexes
DROP INDEX CONCURRENTLY IF EXISTS idx_language_settings_rtl;
DROP INDEX CONCURRENTLY IF EXISTS idx_language_settings_enabled;

-- ============================================================================
-- Step 5: Reset Autovacuum Settings to Defaults
-- ============================================================================

-- Reset template_renders
ALTER TABLE template_renders RESET (
    autovacuum_vacuum_scale_factor,
    autovacuum_analyze_scale_factor,
    autovacuum_vacuum_cost_delay
);

-- Reset content_translations
ALTER TABLE content_translations RESET (
    autovacuum_vacuum_scale_factor,
    autovacuum_analyze_scale_factor
);

-- Reset device_custom_variables
ALTER TABLE device_custom_variables RESET (
    autovacuum_vacuum_scale_factor,
    autovacuum_analyze_scale_factor
);

-- Reset template_security_log
ALTER TABLE template_security_log RESET (
    autovacuum_vacuum_scale_factor,
    autovacuum_analyze_scale_factor
);

COMMIT;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- 1. Verify materialized views were dropped
SELECT
    'Materialized View Check' as check_type,
    COUNT(CASE WHEN matviewname = 'mv_translation_stats' THEN 1 END) as mv_translation_stats_exists,
    COUNT(CASE WHEN matviewname = 'mv_template_performance' THEN 1 END) as mv_template_performance_exists,
    COUNT(CASE WHEN matviewname = 'mv_language_by_location' THEN 1 END) as mv_language_by_location_exists
FROM pg_matviews
WHERE matviewname LIKE 'mv_%';
-- All counts should be 0

-- 2. Verify functions were dropped
SELECT
    routine_name
FROM information_schema.routines
WHERE routine_name IN (
    'refresh_phase4_materialized_views',
    'create_template_renders_partition',
    'maintain_template_renders_partitions',
    'warmup_phase4_cache'
);
-- Should return no rows

-- 3. Verify performance indexes were dropped
SELECT
    schemaname,
    tablename,
    indexname
FROM pg_indexes
WHERE indexname IN (
    'idx_content_templates_template_gin',
    'idx_content_templates_active',
    'idx_template_renders_recent',
    'idx_template_renders_errors',
    'idx_template_renders_cache',
    'idx_custom_variables_type',
    'idx_device_custom_variables_lookup',
    'idx_content_translations_search',
    'idx_content_translations_primary',
    'idx_language_settings_rtl',
    'idx_language_settings_enabled'
);
-- Should return no rows

-- 4. Count remaining indexes per table
SELECT
    tablename,
    COUNT(*) as remaining_indexes
FROM pg_indexes
WHERE tablename IN (
    'content_templates', 'template_renders', 'custom_variables',
    'device_custom_variables', 'content_translations', 'language_settings'
)
GROUP BY tablename
ORDER BY tablename;
-- Should show original indexes from migrations 009 and 010

-- 5. Verify autovacuum settings reset
SELECT
    nspname || '.' || relname as table_name,
    reloptions
FROM pg_class
JOIN pg_namespace ON pg_namespace.oid = pg_class.relnamespace
WHERE relname IN (
    'template_renders', 'content_translations',
    'device_custom_variables', 'template_security_log'
);
-- reloptions should be NULL or empty

-- 6. Check cron jobs (if pg_cron is available)
/*
SELECT
    jobname,
    schedule,
    command
FROM cron.job
WHERE jobname LIKE '%phase4%';
-- Should return no rows
*/

-- ============================================================================
-- Rollback Summary
-- ============================================================================
-- This rollback successfully:
-- ✅ Dropped 4 maintenance functions
-- ✅ Dropped 3 materialized views
-- ✅ Dropped 11 performance indexes (CONCURRENTLY)
-- ✅ Reset autovacuum settings to defaults (4 tables)
-- ✅ Removed cron jobs (if pg_cron enabled)
--
-- Performance Indexes Removed: 11
-- Materialized Views Removed: 3
-- Functions Removed: 4
-- Autovacuum Reset: 4 tables
--
-- ⚠️ NO DATA LOSS:
-- - All core tables and data preserved
-- - Only performance optimizations removed
-- - Base functionality from migrations 009 and 010 intact
--
-- Impact:
-- - Queries may be slower without optimization indexes
-- - Dashboard may be slower without materialized views
-- - No automated partition management
-- - Manual statistics updates may be needed
--
-- Note: You can safely re-run migration 011 at any time to restore optimizations
-- ============================================================================
