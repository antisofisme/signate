-- Migration: 048
-- Description: Add UNIQUE constraint to pending_devices.activation_code
-- Date: 2025-01-14
-- CRITICAL FIX: Prevent duplicate activation codes via race condition

BEGIN;

-- Add UNIQUE constraint on activation_code
-- This will prevent duplicate codes at database level
ALTER TABLE pending_devices
ADD CONSTRAINT unique_activation_code UNIQUE (activation_code);

-- Add comment
COMMENT ON CONSTRAINT unique_activation_code ON pending_devices IS
'Ensures activation codes are globally unique (Fix P0-9)';

COMMIT;
