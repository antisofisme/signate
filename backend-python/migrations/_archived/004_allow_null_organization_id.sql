-- Migration: Allow NULL organization_id for No-PIN Registration Flow
-- Purpose: Support device registration without organization, assigned during activation
-- Date: 2025-11-07

-- Make organization_id nullable
ALTER TABLE devices
ALTER COLUMN organization_id DROP NOT NULL;

-- Add defaults for columns that were missing them
ALTER TABLE devices
ALTER COLUMN rotation SET DEFAULT 0;

ALTER TABLE devices
ALTER COLUMN location_type SET DEFAULT 'lobby';

ALTER TABLE devices
ALTER COLUMN privacy_mode SET DEFAULT 'normal';

ALTER TABLE devices
ALTER COLUMN supports_personalization SET DEFAULT false;

ALTER TABLE devices
ALTER COLUMN volume_enabled SET DEFAULT false;

-- Add comment to document the change
COMMENT ON COLUMN devices.organization_id IS 'Organization ID - nullable for pending devices, assigned during activation';
