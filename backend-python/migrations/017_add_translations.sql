-- Migration 025: Multi-language Translations
-- Phase 5: Advanced Features - Translation system

BEGIN;

-- Translations for multi-language support
CREATE TABLE IF NOT EXISTS translations (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Entity reference
    entity_type VARCHAR(50) NOT NULL, -- 'content', 'playlist', 'template', 'widget'
    entity_id INTEGER NOT NULL,

    -- Translation
    language_code VARCHAR(5) NOT NULL, -- 'en', 'id', 'zh', 'ja', 'ko'
    field_name VARCHAR(100) NOT NULL, -- 'title', 'description', 'content'
    translated_value TEXT NOT NULL,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(entity_type, entity_id, language_code, field_name)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_translations_org ON translations(organization_id);
CREATE INDEX IF NOT EXISTS idx_translations_entity ON translations(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_translations_lang ON translations(language_code);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_translations_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER translations_updated_at
    BEFORE UPDATE ON translations
    FOR EACH ROW
    EXECUTE FUNCTION update_translations_updated_at();

COMMIT;
