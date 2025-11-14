-- Migration: 046
-- Description: Add CASCADE constraint to users.organization_id foreign key
-- Date: 2025-01-14
-- CRITICAL FIX: Prevents orphaned users when organization is deleted

BEGIN;

-- Drop existing foreign key constraint
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_organization_id_fkey;

-- Add new constraint with CASCADE
ALTER TABLE users
ADD CONSTRAINT users_organization_id_fkey
FOREIGN KEY (organization_id)
REFERENCES organizations(id)
ON DELETE CASCADE
ON UPDATE CASCADE;

-- Add comment
COMMENT ON CONSTRAINT users_organization_id_fkey ON users IS
'CASCADE delete users when organization is deleted (Fix P0-7)';

COMMIT;
