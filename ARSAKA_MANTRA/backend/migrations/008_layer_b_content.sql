-- Migration: 008
-- Description: Add Layer B Content columns for MICS Long Content Strategy
-- Date: 2026-01-27
-- Per: MANTRA-SCHEMA-001 Two-Layer Content Model

BEGIN;

-- ============================================================================
-- Layer B Content Columns
-- ============================================================================
--
-- Two-Layer Content Model:
-- - Layer A: statement, rationale, constraints (executive summary, validated)
-- - Layer B: detailed_content, sections, content_summary (full spec, structure-validated)
--
-- This enables:
-- - Long-form technical specifications without polluting Layer A
-- - Selective retrieval for token budget management
-- - Structured sections for different content types (OVERVIEW, RULES, EXAMPLES, etc.)
--

-- Add detailed_content column (full Markdown specification)
ALTER TABLE decisions
ADD COLUMN IF NOT EXISTS detailed_content TEXT DEFAULT NULL;

-- Add sections column (structured breakdown as JSONB array)
-- Format: [{"section_id": "S-001", "section_type": "OVERVIEW", "title": "...", "content": "...", "order": 1}, ...]
ALTER TABLE decisions
ADD COLUMN IF NOT EXISTS sections JSONB DEFAULT '[]';

-- Add content_summary column (auto-generated token-efficient summary)
ALTER TABLE decisions
ADD COLUMN IF NOT EXISTS content_summary TEXT DEFAULT NULL;

-- Comments
COMMENT ON COLUMN decisions.detailed_content IS 'Layer B: Full Markdown specification for long-form decisions';
COMMENT ON COLUMN decisions.sections IS 'Layer B: Structured sections (OVERVIEW, RULES, EXAMPLES, STRUCTURE, DIAGRAM, REFERENCE)';
COMMENT ON COLUMN decisions.content_summary IS 'Layer B: Auto-generated summary for token-efficient retrieval';

-- Index for section_type filtering (GIN index for JSONB array queries)
CREATE INDEX IF NOT EXISTS idx_decisions_sections_type
ON decisions USING GIN (sections jsonb_path_ops);

COMMIT;
