-- Migration: 055
-- Description: Fix tag unique constraint to handle soft deletes
-- Date: 2025-11-29
-- Issue: Soft-deleted tags still trigger unique constraint violation

BEGIN;

-- Drop the existing unique constraint that doesn't account for soft deletes
ALTER TABLE tags DROP CONSTRAINT IF EXISTS unique_tag_name_per_org;

-- Create a partial unique index that only applies to non-deleted records
-- This allows the same tag name to exist multiple times if previous ones are soft-deleted
CREATE UNIQUE INDEX unique_tag_name_per_org_active
ON tags (organization_id, tag_name)
WHERE deleted_at IS NULL;

-- Add comment explaining the constraint
COMMENT ON INDEX unique_tag_name_per_org_active IS
'Ensures tag names are unique per organization, but only for active (non-deleted) tags';

COMMIT;
