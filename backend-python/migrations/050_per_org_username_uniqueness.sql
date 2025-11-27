-- Migration: 050
-- Description: Change username from global to per-organization unique
-- Note: Email stays globally unique for login purposes
-- Date: 2025-11-26

BEGIN;

-- 1. Drop existing global username constraint ONLY
-- Note: Constraint name may vary, try common patterns
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_username_key;
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_username_unique;
DROP INDEX IF EXISTS ix_users_username;

-- 2. Create composite unique constraint for username (per-organization)
ALTER TABLE users ADD CONSTRAINT users_org_username_unique
  UNIQUE (organization_id, username);

-- 3. Add index for faster lookups (if not created by constraint)
CREATE INDEX IF NOT EXISTS idx_users_org_username
  ON users(organization_id, username);

-- 4. Update comments
COMMENT ON COLUMN users.username IS 'Username unique within organization';
COMMENT ON COLUMN users.email IS 'Email globally unique (for login)';

COMMIT;
