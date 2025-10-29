-- ============================================================================
-- Phase 4 Complete Verification Script
-- ============================================================================
-- Purpose: Comprehensive verification of all Phase 4 migrations
-- Usage: psql -h 192.168.5.12 -p 5433 -U postgres signage_db -f verify_phase4.sql
-- ============================================================================

\set QUIET 1
\timing off
\pset border 2
\pset format wrapped

\echo ''
\echo '============================================================================'
\echo 'Phase 4 Database Migration Verification'
\echo '============================================================================'
\echo ''

-- ============================================================================
-- 1. Table Existence Check
-- ============================================================================

\echo '1. Checking Table Existence...'
\echo ''

SELECT
    'Table Existence' as check_category,
    CASE WHEN COUNT(*) = 8 THEN '✅ PASS' ELSE '❌ FAIL' END as status,
    COUNT(*) as found_tables,
    8 as expected_tables,
    ARRAY_AGG(table_name ORDER BY table_name) as tables
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN (
    'content_templates',
    'template_renders',
    'custom_variables',
    'device_custom_variables',
    'template_security_log',
    'content_translations',
    'language_settings',
    'translation_import_history'
);

\echo ''

-- ============================================================================
-- 2. Partition Check
-- ============================================================================

\echo '2. Checking Template Renders Partitions...'
\echo ''

SELECT
    'Partition Existence' as check_category,
    CASE WHEN COUNT(*) >= 3 THEN '✅ PASS' ELSE '❌ FAIL' END as status,
    COUNT(*) as partition_count,
    ARRAY_AGG(child.relname ORDER BY child.relname) as partitions
FROM pg_inherits
JOIN pg_class parent ON pg_inherits.inhparent = parent.oid
JOIN pg_class child ON pg_inherits.inhrelid = child.oid
WHERE parent.relname = 'template_renders';

\echo ''

-- ============================================================================
-- 3. Column Additions Check
-- ============================================================================

\echo '3. Checking New Columns in Existing Tables...'
\echo ''

WITH expected_columns AS (
    SELECT 'contents' as table_name, 'use_template' as column_name UNION ALL
    SELECT 'contents', 'template_id' UNION ALL
    SELECT 'contents', 'default_language' UNION ALL
    SELECT 'devices', 'primary_language' UNION ALL
    SELECT 'devices', 'secondary_language' UNION ALL
    SELECT 'devices', 'language_rotation' UNION ALL
    SELECT 'devices', 'rotation_interval'
)
SELECT
    'Column Additions' as check_category,
    CASE WHEN COUNT(*) = 7 THEN '✅ PASS' ELSE '❌ FAIL' END as status,
    COUNT(*) as found_columns,
    7 as expected_columns,
    STRING_AGG(ec.table_name || '.' || ec.column_name, ', ' ORDER BY ec.table_name, ec.column_name) as columns
FROM expected_columns ec
JOIN information_schema.columns c ON c.table_name = ec.table_name AND c.column_name = ec.column_name
WHERE c.table_schema = 'public';

\echo ''

-- ============================================================================
-- 4. Function Check
-- ============================================================================

\echo '4. Checking Functions...'
\echo ''

WITH expected_functions AS (
    SELECT 'get_template_context' as function_name UNION ALL
    SELECT 'calculate_context_hash' UNION ALL
    SELECT 'validate_variable_name' UNION ALL
    SELECT 'get_content_translation' UNION ALL
    SELECT 'get_content_languages' UNION ALL
    SELECT 'has_translation' UNION ALL
    SELECT 'get_device_languages' UNION ALL
    SELECT 'refresh_phase4_materialized_views' UNION ALL
    SELECT 'create_template_renders_partition' UNION ALL
    SELECT 'maintain_template_renders_partitions' UNION ALL
    SELECT 'warmup_phase4_cache'
)
SELECT
    'Function Creation' as check_category,
    CASE WHEN COUNT(*) = 11 THEN '✅ PASS' ELSE '❌ FAIL' END as status,
    COUNT(*) as found_functions,
    11 as expected_functions,
    STRING_AGG(r.routine_name, ', ' ORDER BY r.routine_name) as functions
FROM expected_functions ef
JOIN information_schema.routines r ON r.routine_name = ef.function_name
WHERE r.routine_schema = 'public';

\echo ''

-- ============================================================================
-- 5. View Check
-- ============================================================================

\echo '5. Checking Views (Regular and Materialized)...'
\echo ''

WITH regular_views AS (
    SELECT table_name as view_name, 'regular' as view_type
    FROM information_schema.views
    WHERE table_schema = 'public'
    AND table_name IN (
        'template_usage_stats',
        'template_security_summary',
        'translation_coverage',
        'language_usage_stats',
        'translation_completeness'
    )
),
materialized_views AS (
    SELECT matviewname as view_name, 'materialized' as view_type
    FROM pg_matviews
    WHERE schemaname = 'public'
    AND matviewname IN (
        'mv_translation_stats',
        'mv_template_performance',
        'mv_language_by_location'
    )
),
all_views AS (
    SELECT * FROM regular_views
    UNION ALL
    SELECT * FROM materialized_views
)
SELECT
    'View Creation' as check_category,
    CASE WHEN COUNT(*) = 8 THEN '✅ PASS' ELSE '❌ FAIL' END as status,
    COUNT(*) as found_views,
    8 as expected_views,
    COUNT(*) FILTER (WHERE view_type = 'regular') as regular_views,
    COUNT(*) FILTER (WHERE view_type = 'materialized') as materialized_views
FROM all_views;

\echo ''

-- ============================================================================
-- 6. Index Count Check
-- ============================================================================

\echo '6. Checking Indexes...'
\echo ''

SELECT
    tablename,
    COUNT(*) as index_count,
    STRING_AGG(indexname, ', ' ORDER BY indexname) as indexes
FROM pg_indexes
WHERE schemaname = 'public'
AND tablename IN (
    'content_templates',
    'template_renders',
    'custom_variables',
    'device_custom_variables',
    'template_security_log',
    'content_translations',
    'language_settings',
    'translation_import_history'
)
GROUP BY tablename
ORDER BY tablename;

\echo ''

-- ============================================================================
-- 7. Default Language Data Check
-- ============================================================================

\echo '7. Checking Default Language Data...'
\echo ''

SELECT
    'Language Settings' as check_category,
    CASE WHEN COUNT(*) >= 15 THEN '✅ PASS' ELSE '❌ FAIL' END as status,
    COUNT(*) as language_count,
    COUNT(*) FILTER (WHERE is_enabled = TRUE) as enabled_count,
    COUNT(*) FILTER (WHERE is_rtl = TRUE) as rtl_count
FROM language_settings;

\echo ''

SELECT
    language_code,
    language_name,
    native_name,
    CASE WHEN is_rtl THEN 'RTL' ELSE 'LTR' END as direction,
    CASE WHEN is_enabled THEN '✓' ELSE '✗' END as enabled
FROM language_settings
ORDER BY sort_order
LIMIT 15;

\echo ''

-- ============================================================================
-- 8. Custom Variables Check
-- ============================================================================

\echo '8. Checking Custom Variables...'
\echo ''

SELECT
    'Custom Variables' as check_category,
    CASE WHEN COUNT(*) >= 8 THEN '✅ PASS' ELSE '⚠️ WARNING' END as status,
    COUNT(*) as variable_count,
    COUNT(*) FILTER (WHERE is_global = TRUE) as global_count
FROM custom_variables;

\echo ''

SELECT
    key,
    value_type,
    default_value,
    CASE WHEN is_global THEN 'Global' ELSE 'Local' END as scope,
    description
FROM custom_variables
ORDER BY is_global DESC, key;

\echo ''

-- ============================================================================
-- 9. Content Migration Check
-- ============================================================================

\echo '9. Checking Content Translation Migration...'
\echo ''

SELECT
    'Content Migration' as check_category,
    CASE
        WHEN contents_count > 0 AND translation_count = contents_count THEN '✅ PASS'
        WHEN contents_count = 0 THEN '⚠️ NO CONTENT'
        ELSE '❌ FAIL'
    END as status,
    contents_count,
    translation_count,
    CASE
        WHEN contents_count > 0 THEN
            ROUND((translation_count::NUMERIC / contents_count * 100), 2)
        ELSE 0
    END as migration_percentage
FROM (
    SELECT
        COUNT(DISTINCT c.id) as contents_count,
        COUNT(DISTINCT ct.content_id) as translation_count
    FROM contents c
    LEFT JOIN content_translations ct ON c.id = ct.content_id AND ct.is_primary = TRUE
) sub;

\echo ''

-- ============================================================================
-- 10. Trigger Check
-- ============================================================================

\echo '10. Checking Triggers...'
\echo ''

SELECT
    'Trigger Creation' as check_category,
    CASE WHEN COUNT(*) >= 6 THEN '✅ PASS' ELSE '❌ FAIL' END as status,
    COUNT(*) as trigger_count,
    6 as expected_triggers
FROM information_schema.triggers
WHERE event_object_schema = 'public'
AND trigger_name IN (
    'trg_content_templates_updated_at',
    'trg_custom_variables_updated_at',
    'trg_device_custom_variables_updated_at',
    'trg_content_translations_updated_at',
    'trg_language_settings_updated_at',
    'trg_enforce_single_primary'
);

\echo ''

-- ============================================================================
-- 11. Foreign Key Check
-- ============================================================================

\echo '11. Checking Foreign Key Constraints...'
\echo ''

SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.delete_rule
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
JOIN information_schema.referential_constraints AS rc
    ON rc.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_schema = 'public'
AND tc.table_name IN (
    'content_templates',
    'template_renders',
    'device_custom_variables',
    'content_translations'
)
ORDER BY tc.table_name, kcu.column_name;

\echo ''

-- ============================================================================
-- 12. Unique Constraint Check
-- ============================================================================

\echo '12. Checking Unique Constraints...'
\echo ''

SELECT
    tc.table_name,
    STRING_AGG(kcu.column_name, ', ' ORDER BY kcu.ordinal_position) as columns,
    tc.constraint_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
WHERE tc.constraint_type = 'UNIQUE'
AND tc.table_schema = 'public'
AND tc.table_name IN (
    'custom_variables',
    'device_custom_variables',
    'content_translations',
    'language_settings'
)
GROUP BY tc.table_name, tc.constraint_name
ORDER BY tc.table_name;

\echo ''

-- ============================================================================
-- 13. Table Size Report
-- ============================================================================

\echo '13. Checking Table Sizes...'
\echo ''

SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) -
                   pg_relation_size(schemaname||'.'||tablename)) AS index_size
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN (
    'content_templates',
    'template_renders',
    'custom_variables',
    'device_custom_variables',
    'template_security_log',
    'content_translations',
    'language_settings',
    'translation_import_history'
)
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

\echo ''

-- ============================================================================
-- 14. Statistics Check
-- ============================================================================

\echo '14. Checking Table Statistics...'
\echo ''

SELECT
    schemaname,
    tablename,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows,
    CASE
        WHEN last_analyze IS NOT NULL THEN 'Analyzed'
        ELSE 'Not Analyzed'
    END as analyze_status,
    last_analyze
FROM pg_stat_user_tables
WHERE schemaname = 'public'
AND tablename IN (
    'content_templates',
    'template_renders',
    'custom_variables',
    'device_custom_variables',
    'template_security_log',
    'content_translations',
    'language_settings'
)
ORDER BY tablename;

\echo ''

-- ============================================================================
-- 15. Test Core Functions
-- ============================================================================

\echo '15. Testing Core Functions...'
\echo ''

\echo 'Testing get_template_context():'
SELECT
    jsonb_pretty(get_template_context(1, TRUE)) as context_sample
LIMIT 1;

\echo ''
\echo 'Testing calculate_context_hash():'
SELECT
    calculate_context_hash('{"key": "value"}'::JSONB) as hash_sample;

\echo ''
\echo 'Testing validate_variable_name():'
SELECT
    'valid_name' as test_input,
    validate_variable_name('valid_name') as is_valid
UNION ALL
SELECT
    '123invalid' as test_input,
    validate_variable_name('123invalid') as is_valid;

\echo ''

-- ============================================================================
-- 16. Overall Summary
-- ============================================================================

\echo ''
\echo '============================================================================'
\echo 'Verification Summary'
\echo '============================================================================'
\echo ''

WITH verification_results AS (
    SELECT
        SUM(CASE WHEN check_result = 'PASS' THEN 1 ELSE 0 END) as passed_checks,
        COUNT(*) as total_checks
    FROM (
        -- Table check
        SELECT CASE WHEN COUNT(*) = 8 THEN 'PASS' ELSE 'FAIL' END as check_result
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name IN (
            'content_templates', 'template_renders', 'custom_variables',
            'device_custom_variables', 'template_security_log',
            'content_translations', 'language_settings', 'translation_import_history'
        )

        UNION ALL

        -- Partition check
        SELECT CASE WHEN COUNT(*) >= 3 THEN 'PASS' ELSE 'FAIL' END
        FROM pg_inherits
        JOIN pg_class parent ON pg_inherits.inhparent = parent.oid
        JOIN pg_class child ON pg_inherits.inhrelid = child.oid
        WHERE parent.relname = 'template_renders'

        UNION ALL

        -- Function check
        SELECT CASE WHEN COUNT(*) = 11 THEN 'PASS' ELSE 'FAIL' END
        FROM information_schema.routines
        WHERE routine_schema = 'public'
        AND routine_name IN (
            'get_template_context', 'calculate_context_hash', 'validate_variable_name',
            'get_content_translation', 'get_content_languages', 'has_translation',
            'get_device_languages', 'refresh_phase4_materialized_views',
            'create_template_renders_partition', 'maintain_template_renders_partitions',
            'warmup_phase4_cache'
        )

        UNION ALL

        -- Language check
        SELECT CASE WHEN COUNT(*) >= 15 THEN 'PASS' ELSE 'FAIL' END
        FROM language_settings

        UNION ALL

        -- Column check
        SELECT CASE WHEN COUNT(*) = 7 THEN 'PASS' ELSE 'FAIL' END
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND (
            (table_name = 'contents' AND column_name IN ('use_template', 'template_id', 'default_language'))
            OR (table_name = 'devices' AND column_name IN ('primary_language', 'secondary_language', 'language_rotation', 'rotation_interval'))
        )
    ) checks
)
SELECT
    CASE
        WHEN passed_checks = total_checks THEN '✅ ALL CHECKS PASSED'
        ELSE '❌ SOME CHECKS FAILED'
    END as overall_status,
    passed_checks || ' / ' || total_checks as check_ratio,
    ROUND((passed_checks::NUMERIC / total_checks * 100), 2) || '%' as success_rate
FROM verification_results;

\echo ''
\echo 'Phase 4 database migration verification complete.'
\echo ''
\echo '============================================================================'
