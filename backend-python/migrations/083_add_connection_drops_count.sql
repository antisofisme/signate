-- Migration: 083
-- Description: Add connection_drops_count column to devices table
-- Purpose: Track network disconnection count since device startup for reliability monitoring
-- Date: 2025-12-05

BEGIN;

-- Add connection_drops_count column to devices table
ALTER TABLE devices
ADD COLUMN IF NOT EXISTS connection_drops_count INTEGER DEFAULT 0;

-- Add comment for documentation
COMMENT ON COLUMN devices.connection_drops_count IS 'Number of network disconnections since device startup - for reliability monitoring';

COMMIT;
