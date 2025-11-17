-- Migration: 046
-- Description: Enhance content_assignments table with organization_id, tag support, and audit trail
-- Date: 2025-01-13
-- Purpose: Add missing multi-tenancy, tag-based assignment, and standardize columns

BEGIN;

-- ============================================================================
-- STEP 1: Add missing columns
-- ============================================================================

-- Add organization_id for multi-tenancy (CRITICAL for security)
ALTER TABLE content_assignments
ADD COLUMN organization_id INTEGER;

-- Add tag_id for tag-based assignment (Method 3)
ALTER TABLE content_assignments
ADD COLUMN tag_id INTEGER;

-- Add created_at for audit trail
ALTER TABLE content_assignments
ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL;

-- Add updated_at for tracking changes
ALTER TABLE content_assignments
ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE;

-- ============================================================================
-- STEP 2: Populate organization_id from devices
-- ============================================================================

-- Populate organization_id based on device's organization
UPDATE content_assignments ca
SET organization_id = d.organization_id
FROM devices d
WHERE ca.device_id = d.id
  AND ca.organization_id IS NULL;

-- ============================================================================
-- STEP 3: Make device_id nullable (for tag-based assignments)
-- ============================================================================

-- Tag-based assignments won't have device_id, only tag_id
ALTER TABLE content_assignments
ALTER COLUMN device_id DROP NOT NULL;

-- ============================================================================
-- STEP 4: Add constraints
-- ============================================================================

-- Make organization_id NOT NULL (required for all assignments)
ALTER TABLE content_assignments
ALTER COLUMN organization_id SET NOT NULL;

-- Add foreign key for organization_id
ALTER TABLE content_assignments
ADD CONSTRAINT content_assignments_organization_id_fkey
FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE;

-- Add foreign key for tag_id (optional)
ALTER TABLE content_assignments
ADD CONSTRAINT content_assignments_tag_id_fkey
FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE;

-- Add CHECK constraint: either device_id OR tag_id must be set (not both, not neither)
ALTER TABLE content_assignments
ADD CONSTRAINT content_assignments_target_check
CHECK (
    (device_id IS NOT NULL AND tag_id IS NULL) OR
    (device_id IS NULL AND tag_id IS NOT NULL)
);

-- ============================================================================
-- STEP 5: Add indexes for performance
-- ============================================================================

-- Index for organization filtering (multi-tenancy)
CREATE INDEX idx_content_assignments_organization ON content_assignments(organization_id);

-- Index for tag-based queries
CREATE INDEX idx_content_assignments_tag ON content_assignments(tag_id) WHERE tag_id IS NOT NULL;

-- Composite index for organization + device lookups
CREATE INDEX idx_content_assignments_org_device ON content_assignments(organization_id, device_id);

-- Composite index for organization + tag lookups
CREATE INDEX idx_content_assignments_org_tag ON content_assignments(organization_id, tag_id);

-- Composite index for organization + content (for content usage tracking)
CREATE INDEX idx_content_assignments_org_content ON content_assignments(organization_id, content_id);

-- Index for expiration queries (without NOW() function - not allowed in index predicate)
CREATE INDEX idx_content_assignments_active ON content_assignments(organization_id, expires_at)
WHERE expires_at IS NOT NULL;

-- ============================================================================
-- STEP 6: Update unique constraint to include organization
-- ============================================================================

-- Drop old unique constraint
ALTER TABLE content_assignments
DROP CONSTRAINT IF EXISTS unique_device_content;

-- Add new unique constraint per organization (device-based)
-- One device can only have one assignment per content per organization
CREATE UNIQUE INDEX unique_org_device_content ON content_assignments(organization_id, device_id, content_id)
WHERE device_id IS NOT NULL;

-- Add unique constraint for tag-based assignments
-- One tag can only have one assignment per content per organization
CREATE UNIQUE INDEX unique_org_tag_content ON content_assignments(organization_id, tag_id, content_id)
WHERE tag_id IS NOT NULL;

-- ============================================================================
-- STEP 7: Add table comment
-- ============================================================================

COMMENT ON TABLE content_assignments IS 'Content assignments to devices or tags - supports direct and tag-based assignment methods';
COMMENT ON COLUMN content_assignments.organization_id IS 'Organization owning this assignment (multi-tenancy)';
COMMENT ON COLUMN content_assignments.device_id IS 'Direct device assignment (Method 1 - mutually exclusive with tag_id)';
COMMENT ON COLUMN content_assignments.tag_id IS 'Tag-based assignment (Method 3 - mutually exclusive with device_id)';
COMMENT ON COLUMN content_assignments.content_id IS 'Content to be assigned';
COMMENT ON COLUMN content_assignments.priority IS 'Display priority (lower number = higher priority)';
COMMENT ON COLUMN content_assignments.schedule IS 'Optional schedule configuration (JSONB)';
COMMENT ON COLUMN content_assignments.assigned_at IS 'When assignment was created';
COMMENT ON COLUMN content_assignments.assigned_by_id IS 'User who created the assignment';
COMMENT ON COLUMN content_assignments.expires_at IS 'Optional expiration date for temporary assignments';
COMMENT ON COLUMN content_assignments.created_at IS 'Record creation timestamp';
COMMENT ON COLUMN content_assignments.updated_at IS 'Record last update timestamp';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Verify table structure
DO $$
DECLARE
    v_org_id_exists BOOLEAN;
    v_tag_id_exists BOOLEAN;
    v_created_at_exists BOOLEAN;
    v_updated_at_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'content_assignments' AND column_name = 'organization_id'
    ) INTO v_org_id_exists;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'content_assignments' AND column_name = 'tag_id'
    ) INTO v_tag_id_exists;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'content_assignments' AND column_name = 'created_at'
    ) INTO v_created_at_exists;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'content_assignments' AND column_name = 'updated_at'
    ) INTO v_updated_at_exists;

    IF NOT v_org_id_exists THEN
        RAISE EXCEPTION 'Migration failed: organization_id column not created';
    END IF;

    IF NOT v_tag_id_exists THEN
        RAISE EXCEPTION 'Migration failed: tag_id column not created';
    END IF;

    IF NOT v_created_at_exists THEN
        RAISE EXCEPTION 'Migration failed: created_at column not created';
    END IF;

    IF NOT v_updated_at_exists THEN
        RAISE EXCEPTION 'Migration failed: updated_at column not created';
    END IF;

    RAISE NOTICE 'Migration 046 completed successfully';
    RAISE NOTICE '✓ organization_id added (multi-tenancy enabled)';
    RAISE NOTICE '✓ tag_id added (tag-based assignment supported)';
    RAISE NOTICE '✓ created_at and updated_at added (audit trail)';
    RAISE NOTICE '✓ Foreign keys and constraints added';
    RAISE NOTICE '✓ Performance indexes created';
END $$;

COMMIT;
