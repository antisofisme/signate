-- Migration: 051
-- Description: Add created_by_id and updated_by_id audit columns to core tables
-- Date: 2025-11-27

BEGIN;

-- =============================================================================
-- CONTENTS TABLE - Track who uploaded/modified content
-- =============================================================================

-- Note: contents already has uploaded_by_id, add updated_by_id
ALTER TABLE contents
ADD COLUMN IF NOT EXISTS updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

COMMENT ON COLUMN contents.updated_by_id IS 'User who last modified this content';

-- =============================================================================
-- TAGS TABLE - Track who created/modified tags
-- =============================================================================

ALTER TABLE tags
ADD COLUMN IF NOT EXISTS created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE tags
ADD COLUMN IF NOT EXISTS updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

COMMENT ON COLUMN tags.created_by_id IS 'User who created this tag';
COMMENT ON COLUMN tags.updated_by_id IS 'User who last modified this tag';

-- =============================================================================
-- TRANSLATIONS TABLE - Track who created/modified translations
-- =============================================================================

ALTER TABLE translations
ADD COLUMN IF NOT EXISTS created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE translations
ADD COLUMN IF NOT EXISTS updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

COMMENT ON COLUMN translations.created_by_id IS 'User who created this translation';
COMMENT ON COLUMN translations.updated_by_id IS 'User who last modified this translation';

-- =============================================================================
-- ORGANIZATIONS TABLE - Track who created/modified organizations
-- =============================================================================

ALTER TABLE organizations
ADD COLUMN IF NOT EXISTS created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE organizations
ADD COLUMN IF NOT EXISTS updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

COMMENT ON COLUMN organizations.created_by_id IS 'User who created this organization';
COMMENT ON COLUMN organizations.updated_by_id IS 'User who last modified this organization';

-- =============================================================================
-- CONTENT_ASSIGNMENTS TABLE - Track who assigned content
-- =============================================================================

ALTER TABLE content_assignments
ADD COLUMN IF NOT EXISTS assigned_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

COMMENT ON COLUMN content_assignments.assigned_by_id IS 'User who made this assignment';

-- =============================================================================
-- PLAYLIST_ASSIGNMENTS TABLE - Track who assigned playlist
-- =============================================================================

ALTER TABLE playlist_assignments
ADD COLUMN IF NOT EXISTS assigned_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

COMMENT ON COLUMN playlist_assignments.assigned_by_id IS 'User who made this assignment';

-- =============================================================================
-- Add indexes for audit columns (for querying who did what)
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_contents_updated_by ON contents(updated_by_id);
CREATE INDEX IF NOT EXISTS idx_tags_created_by ON tags(created_by_id);
CREATE INDEX IF NOT EXISTS idx_translations_created_by ON translations(created_by_id);
CREATE INDEX IF NOT EXISTS idx_organizations_created_by ON organizations(created_by_id);
CREATE INDEX IF NOT EXISTS idx_content_assignments_assigned_by ON content_assignments(assigned_by_id);
CREATE INDEX IF NOT EXISTS idx_playlist_assignments_assigned_by ON playlist_assignments(assigned_by_id);

COMMIT;
