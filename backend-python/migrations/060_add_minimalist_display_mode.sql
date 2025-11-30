-- Migration: 060
-- Description: Add 'minimalist' display mode to menus table
-- Date: 2025-11-30
-- Feature: Public Menu Display Redesign - Minimalist Style

BEGIN;

-- ==============================================================================
-- Update display_mode constraint to include 'minimalist'
-- ==============================================================================

-- Drop existing constraint
ALTER TABLE menus DROP CONSTRAINT IF EXISTS check_menus_display_mode;

-- Add updated constraint with 'minimalist' option
ALTER TABLE menus ADD CONSTRAINT check_menus_display_mode
  CHECK (display_mode IN ('grid', 'list', 'carousel', 'minimalist'));

-- Update comment
COMMENT ON COLUMN menus.display_mode IS 'Layout mode for public viewer (grid, list, carousel, minimalist)';

COMMIT;
