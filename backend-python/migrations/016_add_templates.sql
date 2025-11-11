-- Migration 024: Template System
-- Phase 5: Advanced Features - Templates for dynamic content

BEGIN;

-- Templates for dynamic content
CREATE TABLE IF NOT EXISTS templates (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Template Info
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_type VARCHAR(50) NOT NULL, -- 'text', 'image', 'video', 'html', 'greeting'

    -- Content
    content TEXT NOT NULL, -- Template content with {{variables}}
    variables JSONB, -- Variable definitions: {"guest_name": "string", "room": "string"}
    preview_data JSONB, -- Sample data for preview: {"guest_name": "John", "room": "101"}

    -- Settings
    is_active BOOLEAN DEFAULT true,

    -- Metadata
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(organization_id, name)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_templates_org ON templates(organization_id);
CREATE INDEX IF NOT EXISTS idx_templates_type ON templates(template_type);
CREATE INDEX IF NOT EXISTS idx_templates_active ON templates(is_active);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_templates_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER templates_updated_at
    BEFORE UPDATE ON templates
    FOR EACH ROW
    EXECUTE FUNCTION update_templates_updated_at();

COMMIT;
