-- Migration: Make organization_pin optional for No-PIN Registration Flow
-- Purpose: Allow organizations to be created without PIN since device activation uses JWT tokens
-- Date: 2025-11-07

BEGIN;

-- Step 1: Make organization_pin nullable
ALTER TABLE organizations
    ALTER COLUMN organization_pin DROP NOT NULL;

-- Step 2: Drop unique constraint (if exists)
-- This allows multiple organizations to have NULL PINs
ALTER TABLE organizations
    DROP CONSTRAINT IF EXISTS organizations_organization_pin_key;

-- Step 3: Drop unique index (if exists)
-- This allows multiple organizations to have NULL PINs
DROP INDEX IF EXISTS ix_organizations_organization_pin;

-- Add comment to document the change
COMMENT ON COLUMN organizations.organization_pin IS
    'Organization PIN (8-digit) - DEPRECATED: Now optional, organizations use JWT-based device activation instead of PIN-based registration';

COMMIT;
