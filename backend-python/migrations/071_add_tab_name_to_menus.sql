-- Migration: 071
-- Description: Add tab_name column to menus table for custom portal tab labels
-- Date: 2025-12-03
--
-- This allows menus with the same menu_type to have different tab names in the portal

BEGIN;

-- Add tab_name column to menus table
-- This will be used as the tab label in portal view instead of menu_type
ALTER TABLE menus ADD COLUMN IF NOT EXISTS tab_name VARCHAR(100);

-- Add comment for documentation
COMMENT ON COLUMN menus.tab_name IS 'Custom tab label for portal view. If null, fallback to menu_type label.';

COMMIT;
