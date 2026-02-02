-- Migration: 039_document_templates.sql
-- Purpose: Document generation templates and history
-- Stores templates, generated documents, and export configurations

-- ============================================================================
-- DOCUMENT TEMPLATES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS document_templates (
    -- Primary key
    template_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identity
    name VARCHAR(100) NOT NULL,
    doc_type VARCHAR(30) NOT NULL,
    description TEXT,

    -- Template configuration (stored as JSONB)
    config JSONB NOT NULL DEFAULT '{}',

    -- Filters
    scope_filter TEXT,
    domain_filter VARCHAR(10),
    tag_filters TEXT[] DEFAULT '{}',

    -- Customization
    custom_header TEXT,
    custom_footer TEXT,
    company_name VARCHAR(100),
    logo_url TEXT,

    -- Output settings
    output_format VARCHAR(20) NOT NULL DEFAULT 'MARKDOWN',
    include_toc BOOLEAN DEFAULT TRUE,
    include_metadata BOOLEAN DEFAULT TRUE,

    -- Status
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,

    -- Audit
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT chk_doc_type CHECK (doc_type IN (
        'PRD', 'BRD', 'FEATURE_SPEC',
        'TECH_SPEC', 'API_SPEC', 'DB_SCHEMA', 'UI_SPEC',
        'SECURITY_SPEC', 'THREAT_MODEL', 'COMPLIANCE_DOC',
        'TEST_PLAN', 'PERF_SPEC',
        'DEPLOY_GUIDE', 'RUNBOOK', 'INFRA_SPEC',
        'USER_MANUAL', 'API_DOCS', 'FAQ',
        'ADR', 'CHANGELOG', 'MIGRATION_GUIDE',
        'EXEC_SUMMARY', 'IMPACT_REPORT'
    )),
    CONSTRAINT chk_output_format CHECK (output_format IN (
        'MARKDOWN', 'HTML', 'PDF', 'JSON', 'CONFLUENCE', 'NOTION', 'DOCX', 'RST'
    ))
);

-- ============================================================================
-- GENERATED DOCUMENTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS generated_documents (
    -- Primary key
    doc_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Reference to template (optional)
    template_id UUID REFERENCES document_templates(template_id),

    -- Document info
    doc_type VARCHAR(30) NOT NULL,
    title VARCHAR(200) NOT NULL,
    version VARCHAR(20) NOT NULL DEFAULT '1.0.0',

    -- Content
    output_format VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    content_hash VARCHAR(64),  -- SHA-256 for change detection

    -- Statistics
    word_count INT DEFAULT 0,
    section_count INT DEFAULT 0,
    decision_count INT DEFAULT 0,

    -- Source decisions (for tracking)
    source_decision_ids UUID[] DEFAULT '{}',

    -- Generation info
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    generated_by TEXT NOT NULL,
    generation_time_ms INT,

    -- Export info
    exported_to TEXT,  -- e.g., 'confluence:page-id', 'notion:block-id'
    exported_at TIMESTAMPTZ,

    -- Status
    is_latest BOOLEAN DEFAULT TRUE,
    superseded_by UUID REFERENCES generated_documents(doc_id)
);

-- ============================================================================
-- DOCUMENT EXPORT CONFIGS
-- ============================================================================

CREATE TABLE IF NOT EXISTS document_export_configs (
    -- Primary key
    config_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identity
    name VARCHAR(100) NOT NULL,
    export_type VARCHAR(30) NOT NULL,  -- confluence, notion, github, etc.

    -- Connection settings (encrypted in production)
    connection_config JSONB NOT NULL DEFAULT '{}',

    -- Export settings
    auto_export BOOLEAN DEFAULT FALSE,
    export_on_change BOOLEAN DEFAULT FALSE,

    -- Target
    target_path TEXT,  -- e.g., space/folder path

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    last_export_at TIMESTAMPTZ,
    last_export_status VARCHAR(20),

    -- Audit
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_export_type CHECK (export_type IN (
        'confluence', 'notion', 'github', 'gitlab',
        'sharepoint', 'google_docs', 'local_file', 's3'
    ))
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Templates
CREATE INDEX IF NOT EXISTS idx_templates_type ON document_templates(doc_type);
CREATE INDEX IF NOT EXISTS idx_templates_active ON document_templates(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_templates_default ON document_templates(is_default) WHERE is_default = TRUE;

-- Generated documents
CREATE INDEX IF NOT EXISTS idx_generated_type ON generated_documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_generated_at ON generated_documents(generated_at);
CREATE INDEX IF NOT EXISTS idx_generated_latest ON generated_documents(is_latest) WHERE is_latest = TRUE;
CREATE INDEX IF NOT EXISTS idx_generated_decisions ON generated_documents USING GIN(source_decision_ids);

-- Export configs
CREATE INDEX IF NOT EXISTS idx_export_type ON document_export_configs(export_type);
CREATE INDEX IF NOT EXISTS idx_export_active ON document_export_configs(is_active);

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Latest documents by type
CREATE OR REPLACE VIEW latest_documents AS
SELECT
    doc_id,
    doc_type,
    title,
    version,
    output_format,
    word_count,
    section_count,
    decision_count,
    generated_at,
    generated_by
FROM generated_documents
WHERE is_latest = TRUE
ORDER BY generated_at DESC;

-- Document generation stats
CREATE OR REPLACE VIEW document_stats AS
SELECT
    doc_type,
    COUNT(*) as total_generated,
    COUNT(*) FILTER (WHERE is_latest = TRUE) as current_count,
    MAX(generated_at) as last_generated,
    AVG(word_count) as avg_word_count,
    AVG(generation_time_ms) as avg_generation_ms
FROM generated_documents
GROUP BY doc_type
ORDER BY total_generated DESC;

-- Template usage
CREATE OR REPLACE VIEW template_usage AS
SELECT
    t.template_id,
    t.name,
    t.doc_type,
    COUNT(g.doc_id) as times_used,
    MAX(g.generated_at) as last_used
FROM document_templates t
LEFT JOIN generated_documents g ON t.template_id = g.template_id
GROUP BY t.template_id, t.name, t.doc_type;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Generate document record
CREATE OR REPLACE FUNCTION record_generated_document(
    p_doc_type VARCHAR,
    p_title VARCHAR,
    p_version VARCHAR,
    p_output_format VARCHAR,
    p_content TEXT,
    p_decision_ids UUID[],
    p_generated_by TEXT,
    p_template_id UUID DEFAULT NULL,
    p_generation_time_ms INT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_doc_id UUID;
    v_word_count INT;
    v_section_count INT;
BEGIN
    -- Calculate stats
    v_word_count := array_length(string_to_array(p_content, ' '), 1);
    v_section_count := (LENGTH(p_content) - LENGTH(REPLACE(p_content, '## ', ''))) / 3;

    -- Mark previous versions as not latest
    UPDATE generated_documents
    SET is_latest = FALSE
    WHERE doc_type = p_doc_type
      AND is_latest = TRUE;

    -- Insert new document
    INSERT INTO generated_documents (
        template_id,
        doc_type,
        title,
        version,
        output_format,
        content,
        content_hash,
        word_count,
        section_count,
        decision_count,
        source_decision_ids,
        generated_by,
        generation_time_ms
    )
    VALUES (
        p_template_id,
        p_doc_type,
        p_title,
        p_version,
        p_output_format,
        p_content,
        encode(sha256(p_content::bytea), 'hex'),
        v_word_count,
        v_section_count,
        array_length(p_decision_ids, 1),
        p_decision_ids,
        p_generated_by,
        p_generation_time_ms
    )
    RETURNING doc_id INTO v_doc_id;

    RETURN v_doc_id;
END;
$$ LANGUAGE plpgsql;

-- Get default template for doc type
CREATE OR REPLACE FUNCTION get_default_template(p_doc_type VARCHAR)
RETURNS document_templates AS $$
DECLARE
    v_template document_templates;
BEGIN
    SELECT * INTO v_template
    FROM document_templates
    WHERE doc_type = p_doc_type
      AND is_default = TRUE
      AND is_active = TRUE
    LIMIT 1;

    RETURN v_template;
END;
$$ LANGUAGE plpgsql;

-- Check if document content changed
CREATE OR REPLACE FUNCTION document_content_changed(
    p_doc_type VARCHAR,
    p_content TEXT
)
RETURNS BOOLEAN AS $$
DECLARE
    v_latest_hash VARCHAR;
    v_new_hash VARCHAR;
BEGIN
    -- Get latest document hash
    SELECT content_hash INTO v_latest_hash
    FROM generated_documents
    WHERE doc_type = p_doc_type
      AND is_latest = TRUE
    LIMIT 1;

    IF v_latest_hash IS NULL THEN
        RETURN TRUE;  -- No previous document
    END IF;

    -- Calculate new hash
    v_new_hash := encode(sha256(p_content::bytea), 'hex');

    RETURN v_latest_hash != v_new_hash;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGER: Update timestamp
-- ============================================================================

CREATE OR REPLACE FUNCTION update_template_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_template_updated
    BEFORE UPDATE ON document_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_template_timestamp();

-- ============================================================================
-- SAMPLE TEMPLATES
-- ============================================================================

-- Insert default templates for common document types
INSERT INTO document_templates (name, doc_type, description, config, created_by, is_default)
VALUES
    ('Default Tech Spec', 'TECH_SPEC',
     'Standard technical specification template',
     '{"include_rationale": true, "include_examples": true}'::jsonb,
     'system', TRUE),

    ('Default API Spec', 'API_SPEC',
     'Standard API specification template',
     '{"include_auth": true, "include_errors": true}'::jsonb,
     'system', TRUE),

    ('Default Security Spec', 'SECURITY_SPEC',
     'Standard security specification template',
     '{"include_threats": true, "include_compliance": true}'::jsonb,
     'system', TRUE),

    ('Default User Guide', 'USER_MANUAL',
     'User-friendly documentation template',
     '{"simplify_language": true, "include_faq": true}'::jsonb,
     'system', TRUE),

    ('Default Executive Summary', 'EXEC_SUMMARY',
     'High-level executive summary template',
     '{"max_decisions": 10, "simplify_language": true}'::jsonb,
     'system', TRUE)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE document_templates IS
    'Reusable templates for document generation with customization options.';

COMMENT ON TABLE generated_documents IS
    'History of generated documents with content and statistics. '
    'Tracks which decisions were used and supports versioning.';

COMMENT ON TABLE document_export_configs IS
    'Configuration for exporting documents to external systems '
    'like Confluence, Notion, GitHub, etc.';

COMMENT ON FUNCTION record_generated_document IS
    'Records a newly generated document and marks previous versions as not latest.';

COMMENT ON FUNCTION document_content_changed IS
    'Checks if document content has changed from the latest version using SHA-256 hash.';
