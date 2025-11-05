-- Migration: Add new fields to organizations table and update PIN length
-- Date: 2025-11-04
-- Description: Add description, address, contact info, logo_url and change organization_pin from VARCHAR(6) to VARCHAR(8)

BEGIN;

-- Add new columns to organizations table
ALTER TABLE organizations
  ADD COLUMN IF NOT EXISTS description VARCHAR(500),
  ADD COLUMN IF NOT EXISTS address VARCHAR(500),
  ADD COLUMN IF NOT EXISTS contact_email VARCHAR(100),
  ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(20),
  ADD COLUMN IF NOT EXISTS logo_url VARCHAR(500);

-- Update organization_pin column to allow 8 characters instead of 6
ALTER TABLE organizations
  ALTER COLUMN organization_pin TYPE VARCHAR(8);

COMMIT;

-- Notes:
-- 1. This migration is safe to run on existing data
-- 2. All new columns are nullable, so existing rows won't be affected
-- 3. Changing organization_pin from VARCHAR(6) to VARCHAR(8) is safe as it only increases max length
-- 4. Existing PINs (6 chars) will remain valid
-- 5. New organizations will require 8-digit PINs
