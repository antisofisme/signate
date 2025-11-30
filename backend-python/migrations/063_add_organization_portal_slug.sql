-- Migration: 063
-- Description: Add portal_slug to organizations for unified menu portal URL
-- Date: 2025-12-01

BEGIN;

-- Add portal_slug column to organizations
ALTER TABLE organizations
ADD COLUMN IF NOT EXISTS portal_slug VARCHAR(100) UNIQUE;

-- Generate slugs for existing organizations (name-id format)
-- This ensures uniqueness even if organization names are similar
UPDATE organizations
SET portal_slug = LOWER(
  REGEXP_REPLACE(
    REGEXP_REPLACE(
      REGEXP_REPLACE(name, '[^a-zA-Z0-9\s-]', '', 'g'),  -- remove special chars
      '\s+', '-', 'g'  -- spaces to dashes
    ),
    '-+', '-', 'g'  -- multiple dashes to single
  )
) || '-' || id
WHERE portal_slug IS NULL;

-- Create index for fast public lookup
CREATE INDEX IF NOT EXISTS idx_organizations_portal_slug ON organizations(portal_slug);

-- Add comment for documentation
COMMENT ON COLUMN organizations.portal_slug IS 'URL-friendly slug for public menu portal (format: organization-name-id)';

COMMIT;
