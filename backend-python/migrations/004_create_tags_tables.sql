-- ============================================================================
-- Migration: Create Tags Tables
-- Description: Tag system for organizing and categorizing content
-- Created: 2025-01-07
-- ============================================================================

-- Create tags table
CREATE TABLE IF NOT EXISTS tags (
    -- Identity
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    color VARCHAR(7) DEFAULT '#3B82F6' NOT NULL,  -- Hex color code (default: blue-600)
    description TEXT,

    -- Multi-tenant (organization-scoped)
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Audit Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,

    -- Unique constraint: tag name must be unique per organization
    CONSTRAINT unique_tag_name_per_org UNIQUE (organization_id, name)
);

-- Create content_tags junction table (many-to-many relationship)
CREATE TABLE IF NOT EXISTS content_tags (
    -- Identity
    id SERIAL PRIMARY KEY,

    -- Foreign Keys
    content_id INTEGER NOT NULL REFERENCES contents(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Unique constraint: prevent duplicate assignments
    CONSTRAINT unique_content_tag UNIQUE (content_id, tag_id)
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Tags: Organization lookup (for listing tags by organization)
CREATE INDEX idx_tags_organization ON tags(organization_id);

-- Tags: Name search within organization
CREATE INDEX idx_tags_org_name ON tags(organization_id, name);

-- Content Tags: Find tags by content
CREATE INDEX idx_content_tags_content ON content_tags(content_id);

-- Content Tags: Find content by tag
CREATE INDEX idx_content_tags_tag ON content_tags(tag_id);

-- Content Tags: Combined index for faster joins
CREATE INDEX idx_content_tags_both ON content_tags(content_id, tag_id);

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON TABLE tags IS 'Tags for organizing and categorizing content';
COMMENT ON TABLE content_tags IS 'Many-to-many relationship between contents and tags';
COMMENT ON COLUMN tags.color IS 'Hex color code for tag display (e.g., #3B82F6)';
COMMENT ON COLUMN tags.name IS 'Tag name, unique per organization';

-- ============================================================================
-- Migration Complete
-- ============================================================================

-- To run this migration on server:
-- docker exec -i signage-postgres psql -U signage_user -d signage_db < backend-python/migrations/004_create_tags_tables.sql
