-- Migration: Rename organization_pin to pin
-- Date: 2025-11-13
-- Purpose: Remove redundant prefix - column already in organizations table
-- Related Issue: organization_pin has redundant prefix

-- ============================================================================
-- PHASE 1: Rename column
-- ============================================================================

ALTER TABLE organizations
    RENAME COLUMN organization_pin TO pin;

-- ============================================================================
-- PHASE 2: Update comment
-- ============================================================================

COMMENT ON COLUMN organizations.pin IS 'Organization PIN/code for access control (optional)';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
BEGIN
    -- Verify old column gone
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'organizations' AND column_name = 'organization_pin') THEN
        RAISE EXCEPTION 'Migration failed: organization_pin still exists';
    END IF;

    -- Verify new column exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'organizations' AND column_name = 'pin') THEN
        RAISE EXCEPTION 'Migration failed: pin column missing';
    END IF;

    RAISE NOTICE '✅ Migration successful: organization_pin renamed to pin';
END $$;

-- ============================================================================
-- ROLLBACK INSTRUCTIONS (if needed)
-- ============================================================================

-- If you need to rollback, run this:
-- ALTER TABLE organizations RENAME COLUMN pin TO organization_pin;
