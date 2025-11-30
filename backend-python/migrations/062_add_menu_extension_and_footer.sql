-- Migration: 062
-- Description: Add outlet_extension and footer_description fields to menus table
-- Date: 2025-11-30

BEGIN;

-- Add outlet extension field (displayed after description in player)
ALTER TABLE menus ADD COLUMN IF NOT EXISTS outlet_extension VARCHAR(50);
COMMENT ON COLUMN menus.outlet_extension IS 'Outlet phone extension number (non-clickable info badge)';

-- Add footer description field (displayed in player footer)
ALTER TABLE menus ADD COLUMN IF NOT EXISTS footer_description TEXT;
COMMENT ON COLUMN menus.footer_description IS 'Custom footer description text for player menu';

COMMIT;
