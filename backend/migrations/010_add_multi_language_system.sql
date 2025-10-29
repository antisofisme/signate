-- ============================================================================
-- Migration 010: Phase 4.2 - Multi-Language Content System
-- ============================================================================
-- Author: Database Administrator
-- Date: 2025-10-28
-- Purpose: Add comprehensive multi-language support for international deployments
--
-- Features:
-- 1. Content translations with primary language designation
-- 2. Language preferences per device (primary + secondary)
-- 3. Language rotation for airport/multi-lingual environments
-- 4. System-wide language settings management
-- 5. Translation import history tracking
-- 6. Automatic fallback to default language
--
-- Performance Optimizations:
-- - Full-text search indexes on translations
-- - Composite indexes for fast language lookups
-- - Smart fallback function with minimal queries
-- - Backward compatible (existing content auto-migrated to English)
-- ============================================================================

BEGIN;

-- ============================================================================
-- Step 1: Content Translations Table
-- ============================================================================

-- Core translations storage with primary language designation
CREATE TABLE IF NOT EXISTS content_translations (
    id SERIAL PRIMARY KEY,
    content_id INTEGER NOT NULL REFERENCES contents(id) ON DELETE CASCADE,
    language VARCHAR(5) NOT NULL,  -- ISO 639-1 code (en, id, zh, ja, etc.)
    title VARCHAR(255) NOT NULL,
    description TEXT,
    overlay_text JSONB,  -- For template variables in translated content
    metadata JSONB,  -- Additional translation metadata (translator, notes, etc.)
    is_primary BOOLEAN DEFAULT FALSE,
    translation_status VARCHAR(20) DEFAULT 'active',  -- active, pending, review, archived
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    UNIQUE(content_id, language),
    CONSTRAINT chk_language_code_format CHECK (language ~ '^[a-z]{2}(-[A-Z]{2})?$'),
    CONSTRAINT chk_translation_status CHECK (translation_status IN ('active', 'pending', 'review', 'archived')),
    CONSTRAINT chk_title_not_empty CHECK (LENGTH(title) > 0)
);

-- Indexes for content_translations
CREATE INDEX idx_content_translations_content_id ON content_translations(content_id);
CREATE INDEX idx_content_translations_language ON content_translations(language);
CREATE INDEX idx_content_translations_is_primary ON content_translations(is_primary) WHERE is_primary = TRUE;
CREATE INDEX idx_content_translations_status ON content_translations(translation_status) WHERE translation_status = 'active';

-- Composite indexes for fast lookups
CREATE INDEX idx_content_translations_content_lang ON content_translations(content_id, language);
CREATE INDEX idx_content_translations_lookup ON content_translations(content_id, language, is_primary);

-- Full-text search indexes
CREATE INDEX idx_content_translations_title_gin ON content_translations USING gin(to_tsvector('english', title));
CREATE INDEX idx_content_translations_description_gin ON content_translations USING gin(to_tsvector('english', COALESCE(description, '')));

-- Comments
COMMENT ON TABLE content_translations IS 'Multi-language translations for content (title, description, overlay text)';
COMMENT ON COLUMN content_translations.language IS 'ISO 639-1 language code (en, id, zh) or full code (en-US, zh-CN)';
COMMENT ON COLUMN content_translations.overlay_text IS 'Translated template variable values in JSON format';
COMMENT ON COLUMN content_translations.is_primary IS 'TRUE if this is the primary/original language for this content';
COMMENT ON COLUMN content_translations.translation_status IS 'Translation state: active (live), pending (draft), review (needs approval), archived (old)';

-- ============================================================================
-- Step 2: Add Language Support to Devices Table
-- ============================================================================

-- Add language preference columns to devices
ALTER TABLE devices ADD COLUMN IF NOT EXISTS primary_language VARCHAR(5) DEFAULT 'en';
ALTER TABLE devices ADD COLUMN IF NOT EXISTS secondary_language VARCHAR(5);
ALTER TABLE devices ADD COLUMN IF NOT EXISTS language_rotation BOOLEAN DEFAULT FALSE;
ALTER TABLE devices ADD COLUMN IF NOT EXISTS rotation_interval INTEGER DEFAULT 30;

-- Indexes
CREATE INDEX idx_devices_primary_language ON devices(primary_language);
CREATE INDEX idx_devices_language_rotation ON devices(language_rotation) WHERE language_rotation = TRUE;

-- Comments
COMMENT ON COLUMN devices.primary_language IS 'Primary display language (ISO 639-1 code, e.g., en, id, zh)';
COMMENT ON COLUMN devices.secondary_language IS 'Secondary language for rotation in multi-lingual environments';
COMMENT ON COLUMN devices.language_rotation IS 'TRUE to rotate between primary and secondary languages (airport mode)';
COMMENT ON COLUMN devices.rotation_interval IS 'Seconds between language switches when rotation is enabled (default: 30)';

-- ============================================================================
-- Step 3: System Language Settings
-- ============================================================================

-- System-wide language configuration and management
CREATE TABLE IF NOT EXISTS language_settings (
    id SERIAL PRIMARY KEY,
    language_code VARCHAR(5) UNIQUE NOT NULL,
    language_name VARCHAR(100) NOT NULL,  -- English name
    native_name VARCHAR(100),  -- Native language name (e.g., "日本語" for Japanese)
    is_rtl BOOLEAN DEFAULT FALSE,  -- Right-to-left writing direction
    is_enabled BOOLEAN DEFAULT TRUE,  -- Enable/disable language system-wide
    sort_order INTEGER DEFAULT 0,  -- Display order in UI
    flag_emoji VARCHAR(10),  -- Country flag emoji for UI
    locale_code VARCHAR(10),  -- Full locale code (e.g., en-US, zh-CN)
    date_format VARCHAR(50),  -- Date format pattern for this language
    time_format VARCHAR(50),  -- Time format pattern for this language
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_language_settings_code_format CHECK (language_code ~ '^[a-z]{2}(-[A-Z]{2})?$')
);

-- Indexes
CREATE INDEX idx_language_settings_is_enabled ON language_settings(is_enabled) WHERE is_enabled = TRUE;
CREATE INDEX idx_language_settings_sort_order ON language_settings(sort_order);
CREATE INDEX idx_language_settings_code ON language_settings(language_code);

-- Comments
COMMENT ON TABLE language_settings IS 'System-wide language configuration and metadata';
COMMENT ON COLUMN language_settings.is_rtl IS 'TRUE for right-to-left languages (Arabic, Hebrew)';
COMMENT ON COLUMN language_settings.is_enabled IS 'FALSE to disable language system-wide';
COMMENT ON COLUMN language_settings.sort_order IS 'Display order in UI (lower = higher priority)';

-- ============================================================================
-- Step 4: Insert Default Languages
-- ============================================================================

-- Insert common languages with proper metadata
INSERT INTO language_settings (language_code, language_name, native_name, is_rtl, sort_order, flag_emoji, locale_code, date_format, time_format) VALUES
    ('en', 'English', 'English', FALSE, 1, '🇬🇧', 'en-US', 'MM/DD/YYYY', 'hh:mm A'),
    ('id', 'Indonesian', 'Bahasa Indonesia', FALSE, 2, '🇮🇩', 'id-ID', 'DD/MM/YYYY', 'HH:mm'),
    ('zh', 'Chinese (Simplified)', '简体中文', FALSE, 3, '🇨🇳', 'zh-CN', 'YYYY-MM-DD', 'HH:mm'),
    ('zh-TW', 'Chinese (Traditional)', '繁體中文', FALSE, 4, '🇹🇼', 'zh-TW', 'YYYY-MM-DD', 'HH:mm'),
    ('ja', 'Japanese', '日本語', FALSE, 5, '🇯🇵', 'ja-JP', 'YYYY年MM月DD日', 'HH:mm'),
    ('ko', 'Korean', '한국어', FALSE, 6, '🇰🇷', 'ko-KR', 'YYYY-MM-DD', 'HH:mm'),
    ('es', 'Spanish', 'Español', FALSE, 7, '🇪🇸', 'es-ES', 'DD/MM/YYYY', 'HH:mm'),
    ('fr', 'French', 'Français', FALSE, 8, '🇫🇷', 'fr-FR', 'DD/MM/YYYY', 'HH:mm'),
    ('de', 'German', 'Deutsch', FALSE, 9, '🇩🇪', 'de-DE', 'DD.MM.YYYY', 'HH:mm'),
    ('pt', 'Portuguese', 'Português', FALSE, 10, '🇵🇹', 'pt-PT', 'DD/MM/YYYY', 'HH:mm'),
    ('ru', 'Russian', 'Русский', FALSE, 11, '🇷🇺', 'ru-RU', 'DD.MM.YYYY', 'HH:mm'),
    ('ar', 'Arabic', 'العربية', TRUE, 12, '🇸🇦', 'ar-SA', 'DD/MM/YYYY', 'hh:mm A'),
    ('he', 'Hebrew', 'עברית', TRUE, 13, '🇮🇱', 'he-IL', 'DD/MM/YYYY', 'HH:mm'),
    ('th', 'Thai', 'ไทย', FALSE, 14, '🇹🇭', 'th-TH', 'DD/MM/YYYY', 'HH:mm'),
    ('vi', 'Vietnamese', 'Tiếng Việt', FALSE, 15, '🇻🇳', 'vi-VN', 'DD/MM/YYYY', 'HH:mm')
ON CONFLICT (language_code) DO UPDATE SET
    language_name = EXCLUDED.language_name,
    native_name = EXCLUDED.native_name,
    is_rtl = EXCLUDED.is_rtl,
    sort_order = EXCLUDED.sort_order,
    flag_emoji = EXCLUDED.flag_emoji,
    locale_code = EXCLUDED.locale_code,
    date_format = EXCLUDED.date_format,
    time_format = EXCLUDED.time_format,
    updated_at = NOW();

-- ============================================================================
-- Step 5: Translation Import History
-- ============================================================================

-- Track bulk translation imports (CSV, Excel, etc.)
CREATE TABLE IF NOT EXISTS translation_import_history (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255),
    file_size INTEGER,  -- File size in bytes
    imported_count INTEGER DEFAULT 0,
    updated_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    skipped_count INTEGER DEFAULT 0,
    errors JSONB,  -- Array of error objects
    import_summary JSONB,  -- Summary statistics
    imported_by INTEGER,  -- FK to users table
    imported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    duration_ms INTEGER  -- Import duration in milliseconds
);

-- Indexes
CREATE INDEX idx_translation_import_imported_by ON translation_import_history(imported_by) WHERE imported_by IS NOT NULL;
CREATE INDEX idx_translation_import_imported_at ON translation_import_history(imported_at DESC);

-- Comments
COMMENT ON TABLE translation_import_history IS 'Audit log of bulk translation import operations';
COMMENT ON COLUMN translation_import_history.errors IS 'Array of error objects with row numbers and messages';
COMMENT ON COLUMN translation_import_history.import_summary IS 'Summary statistics (languages, content types, etc.)';

-- ============================================================================
-- Step 6: Add Default Language to Contents Table
-- ============================================================================

-- Add default language column to contents
ALTER TABLE contents ADD COLUMN IF NOT EXISTS default_language VARCHAR(5) DEFAULT 'en';

-- Index
CREATE INDEX idx_contents_default_language ON contents(default_language);

-- Comment
COMMENT ON COLUMN contents.default_language IS 'Default/fallback language for this content (ISO 639-1 code)';

-- ============================================================================
-- Step 7: Migrate Existing Content to Translations
-- ============================================================================

-- Copy existing content titles and descriptions as English translations
INSERT INTO content_translations (content_id, language, title, description, is_primary, translation_status)
SELECT
    id,
    COALESCE(default_language, 'en') as language,
    title,
    description,
    TRUE as is_primary,
    'active' as translation_status
FROM contents
WHERE NOT EXISTS (
    SELECT 1 FROM content_translations
    WHERE content_translations.content_id = contents.id
    AND content_translations.language = COALESCE(contents.default_language, 'en')
);

-- ============================================================================
-- Step 8: Helper Functions
-- ============================================================================

-- Function: Get translation with smart fallback
CREATE OR REPLACE FUNCTION get_content_translation(
    p_content_id INTEGER,
    p_language VARCHAR(5),
    p_fallback_language VARCHAR(5) DEFAULT 'en'
) RETURNS TABLE (
    title VARCHAR(255),
    description TEXT,
    overlay_text JSONB,
    language_used VARCHAR(5)
) AS $$
BEGIN
    -- Try requested language (active only)
    RETURN QUERY
    SELECT ct.title, ct.description, ct.overlay_text, ct.language
    FROM content_translations ct
    WHERE ct.content_id = p_content_id
    AND ct.language = p_language
    AND ct.translation_status = 'active'
    LIMIT 1;

    IF NOT FOUND THEN
        -- Try fallback language
        RETURN QUERY
        SELECT ct.title, ct.description, ct.overlay_text, ct.language
        FROM content_translations ct
        WHERE ct.content_id = p_content_id
        AND ct.language = p_fallback_language
        AND ct.translation_status = 'active'
        LIMIT 1;
    END IF;

    IF NOT FOUND THEN
        -- Try primary language for this content
        RETURN QUERY
        SELECT ct.title, ct.description, ct.overlay_text, ct.language
        FROM content_translations ct
        WHERE ct.content_id = p_content_id
        AND ct.is_primary = TRUE
        AND ct.translation_status = 'active'
        LIMIT 1;
    END IF;

    IF NOT FOUND THEN
        -- Last resort: any available active translation
        RETURN QUERY
        SELECT ct.title, ct.description, ct.overlay_text, ct.language
        FROM content_translations ct
        WHERE ct.content_id = p_content_id
        AND ct.translation_status = 'active'
        ORDER BY ct.created_at ASC
        LIMIT 1;
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_content_translation IS 'Get content translation with smart fallback: requested → fallback → primary → any';

-- Function: Get available languages for content
CREATE OR REPLACE FUNCTION get_content_languages(p_content_id INTEGER)
RETURNS TEXT[] AS $$
BEGIN
    RETURN ARRAY(
        SELECT language
        FROM content_translations
        WHERE content_id = p_content_id
        AND translation_status = 'active'
        ORDER BY is_primary DESC, language ASC
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_content_languages IS 'Get array of available languages for a specific content';

-- Function: Check if translation exists
CREATE OR REPLACE FUNCTION has_translation(
    p_content_id INTEGER,
    p_language VARCHAR(5)
) RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS(
        SELECT 1
        FROM content_translations
        WHERE content_id = p_content_id
        AND language = p_language
        AND translation_status = 'active'
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION has_translation IS 'Check if content has active translation for specified language';

-- Function: Get device language preferences
CREATE OR REPLACE FUNCTION get_device_languages(p_device_id INTEGER)
RETURNS TABLE (
    primary_lang VARCHAR(5),
    secondary_lang VARCHAR(5),
    rotation_enabled BOOLEAN,
    rotation_seconds INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.primary_language,
        d.secondary_language,
        d.language_rotation,
        d.rotation_interval
    FROM devices d
    WHERE d.id = p_device_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_device_languages IS 'Get language preferences for a specific device';

-- ============================================================================
-- Step 9: Create Views
-- ============================================================================

-- View: Translation coverage statistics
CREATE OR REPLACE VIEW translation_coverage AS
SELECT
    c.id as content_id,
    c.title as original_title,
    c.default_language,
    COUNT(ct.id) as translation_count,
    ARRAY_AGG(ct.language ORDER BY ct.language) FILTER (WHERE ct.translation_status = 'active') as available_languages,
    BOOL_OR(ct.language = 'en') as has_english,
    BOOL_OR(ct.language = c.default_language) as has_default_language,
    BOOL_OR(ct.is_primary) as has_primary_translation,
    MAX(ct.updated_at) as last_translation_update
FROM contents c
LEFT JOIN content_translations ct ON c.id = ct.content_id
GROUP BY c.id, c.title, c.default_language;

COMMENT ON VIEW translation_coverage IS 'Translation coverage statistics per content item';

-- View: Language usage statistics
CREATE OR REPLACE VIEW language_usage_stats AS
SELECT
    ct.language,
    ls.language_name,
    ls.native_name,
    COUNT(DISTINCT ct.content_id) as content_count,
    COUNT(*) FILTER (WHERE ct.is_primary) as primary_count,
    COUNT(DISTINCT d.id) as device_count,
    ls.is_enabled as language_enabled
FROM content_translations ct
LEFT JOIN language_settings ls ON ls.language_code = ct.language
LEFT JOIN devices d ON d.primary_language = ct.language OR d.secondary_language = ct.language
WHERE ct.translation_status = 'active'
GROUP BY ct.language, ls.language_name, ls.native_name, ls.is_enabled
ORDER BY content_count DESC;

COMMENT ON VIEW language_usage_stats IS 'Language usage statistics across content and devices';

-- View: Translation completeness report
CREATE OR REPLACE VIEW translation_completeness AS
SELECT
    c.id as content_id,
    c.title,
    c.content_type,
    ls.language_code,
    ls.language_name,
    CASE
        WHEN ct.id IS NOT NULL THEN TRUE
        ELSE FALSE
    END as has_translation,
    ct.translation_status,
    ct.updated_at as last_updated
FROM contents c
CROSS JOIN language_settings ls
LEFT JOIN content_translations ct ON ct.content_id = c.id AND ct.language = ls.language_code
WHERE ls.is_enabled = TRUE
AND c.is_enabled = TRUE
ORDER BY c.id, ls.sort_order;

COMMENT ON VIEW translation_completeness IS 'Matrix of content vs languages showing translation completeness';

-- ============================================================================
-- Step 10: Create Triggers
-- ============================================================================

-- Trigger function for updating updated_at
CREATE OR REPLACE FUNCTION update_translation_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers
CREATE TRIGGER trg_content_translations_updated_at
    BEFORE UPDATE ON content_translations
    FOR EACH ROW
    EXECUTE FUNCTION update_translation_updated_at();

CREATE TRIGGER trg_language_settings_updated_at
    BEFORE UPDATE ON language_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_translation_updated_at();

-- Trigger: Ensure only one primary translation per content
CREATE OR REPLACE FUNCTION enforce_single_primary_translation()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_primary = TRUE THEN
        -- Unset any existing primary for this content
        UPDATE content_translations
        SET is_primary = FALSE
        WHERE content_id = NEW.content_id
        AND id != COALESCE(NEW.id, -1)
        AND is_primary = TRUE;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_enforce_single_primary
    BEFORE INSERT OR UPDATE ON content_translations
    FOR EACH ROW
    WHEN (NEW.is_primary = TRUE)
    EXECUTE FUNCTION enforce_single_primary_translation();

-- ============================================================================
-- Step 11: Statistics and Optimization
-- ============================================================================

-- Analyze tables for query planner
ANALYZE content_translations;
ANALYZE language_settings;
ANALYZE translation_import_history;

-- Set autovacuum settings for high-traffic tables
ALTER TABLE content_translations SET (
    autovacuum_vacuum_scale_factor = 0.02,
    autovacuum_analyze_scale_factor = 0.02
);

COMMIT;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- 1. Verify all tables were created
SELECT
    'Table Creation Check' as check_type,
    COUNT(CASE WHEN table_name = 'content_translations' THEN 1 END) as content_translations_exists,
    COUNT(CASE WHEN table_name = 'language_settings' THEN 1 END) as language_settings_exists,
    COUNT(CASE WHEN table_name = 'translation_import_history' THEN 1 END) as translation_import_history_exists
FROM information_schema.tables
WHERE table_schema = 'public';

-- 2. Verify languages were inserted
SELECT COUNT(*) as language_count, ARRAY_AGG(language_code ORDER BY sort_order) as languages
FROM language_settings
WHERE is_enabled = TRUE;

-- 3. Verify existing content was migrated
SELECT
    COUNT(*) as total_contents,
    COUNT(DISTINCT ct.content_id) as contents_with_translations,
    COUNT(*) FILTER (WHERE ct.is_primary) as primary_translations
FROM contents c
LEFT JOIN content_translations ct ON c.id = ct.content_id;

-- 4. Verify indexes
SELECT
    schemaname,
    tablename,
    indexname
FROM pg_indexes
WHERE tablename IN ('content_translations', 'language_settings', 'devices')
AND indexname LIKE '%language%'
ORDER BY tablename, indexname;

-- 5. Verify functions
SELECT
    routine_name,
    routine_type,
    data_type as return_type
FROM information_schema.routines
WHERE routine_name IN ('get_content_translation', 'get_content_languages',
                       'has_translation', 'get_device_languages')
ORDER BY routine_name;

-- 6. Verify views
SELECT
    table_name as view_name
FROM information_schema.views
WHERE table_name IN ('translation_coverage', 'language_usage_stats', 'translation_completeness')
ORDER BY table_name;

-- 7. Test translation fallback function
SELECT * FROM get_content_translation(1, 'zh', 'en');

-- ============================================================================
-- Migration Summary
-- ============================================================================
-- This migration successfully:
-- ✅ Created content_translations table with full-text search
-- ✅ Added language preferences to devices table (primary + secondary + rotation)
-- ✅ Created language_settings table with 15 default languages
-- ✅ Created translation_import_history for bulk operations tracking
-- ✅ Added default_language column to contents table
-- ✅ Migrated all existing content to English translations
-- ✅ Created 4 helper functions for translation management
-- ✅ Created 3 comprehensive views for translation monitoring
-- ✅ Set up triggers for timestamp updates and primary enforcement
-- ✅ Backward compatible - existing content auto-migrated
--
-- Tables Created: 3
-- Functions Created: 4
-- Views Created: 3
-- Triggers Created: 3
-- Default Languages: 15
-- Contents Migrated: ALL (auto)
--
-- Estimated Storage Impact:
-- - content_translations: ~1KB per translation
-- - language_settings: ~500 bytes per language (fixed)
-- - translation_import_history: ~1KB per import operation
-- - Total overhead for 100 content items with 3 languages: ~300KB
-- ============================================================================
