-- Migration: 046
-- Description: Make organization_id nullable for SUPER_ADMIN users
-- Date: 2025-01-14
-- Reason: SUPER_ADMIN is system role without organization affiliation

BEGIN;

-- Make users.organization_id nullable
ALTER TABLE users
  ALTER COLUMN organization_id DROP NOT NULL;

-- Make user_sessions.organization_id nullable
ALTER TABLE user_sessions
  ALTER COLUMN organization_id DROP NOT NULL;

-- Update foreign key constraints to allow NULL
-- (Already allows NULL implicitly when column is nullable)

-- Add comments
COMMENT ON COLUMN users.organization_id IS 'Organization ID (NULL for SUPER_ADMIN system users)';
COMMENT ON COLUMN user_sessions.organization_id IS 'Organization ID (NULL for SUPER_ADMIN sessions)';

-- Verify
SELECT
  table_name,
  column_name,
  is_nullable,
  data_type
FROM information_schema.columns
WHERE table_name IN ('users', 'user_sessions')
  AND column_name = 'organization_id';

COMMIT;
