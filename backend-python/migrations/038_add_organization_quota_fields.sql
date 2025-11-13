-- Migration: Add Organization Quota Management Fields
-- Date: 2025-11-13
-- Purpose: Add quota management columns to organizations table (max_devices, max_users, settings)
-- Related Fix: Backend testing - Organization quota system

-- Add quota management columns
ALTER TABLE organizations
ADD COLUMN IF NOT EXISTS max_devices INTEGER DEFAULT 10 NOT NULL,
ADD COLUMN IF NOT EXISTS max_users INTEGER DEFAULT 5 NOT NULL,
ADD COLUMN IF NOT EXISTS settings JSONB DEFAULT '{}'::jsonb;

-- Create index for quota queries
CREATE INDEX IF NOT EXISTS idx_organizations_max_devices ON organizations(max_devices);
CREATE INDEX IF NOT EXISTS idx_organizations_max_users ON organizations(max_users);

-- Update existing organizations to have default quotas if NULL
UPDATE organizations
SET max_devices = 10
WHERE max_devices IS NULL;

UPDATE organizations
SET max_users = 5
WHERE max_users IS NULL;

UPDATE organizations
SET settings = '{}'::jsonb
WHERE settings IS NULL;

-- Add comment
COMMENT ON COLUMN organizations.max_devices IS 'Maximum number of devices allowed for this organization';
COMMENT ON COLUMN organizations.max_users IS 'Maximum number of users allowed for this organization';
COMMENT ON COLUMN organizations.settings IS 'Organization-specific settings in JSON format';
