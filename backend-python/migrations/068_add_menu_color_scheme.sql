-- Migration: 068
-- Description: Add 60-30-10 color scheme fields to menus table
-- Date: 2025-12-02
--
-- Color scheme follows UI 60-30-10 principle:
-- - primary_color (60%): Background color, dominant areas
-- - secondary_color (30%): Header, sidebar, categories
-- - theme_color (10%): Accent color for CTAs, highlights, prices (already exists)

BEGIN;

-- Add primary_color column (60% - background)
ALTER TABLE menus
ADD COLUMN IF NOT EXISTS primary_color VARCHAR(7) DEFAULT '#ffffff';

-- Add secondary_color column (30% - header/categories)
ALTER TABLE menus
ADD COLUMN IF NOT EXISTS secondary_color VARCHAR(7) DEFAULT '#f3f4f6';

-- Add comments for documentation
COMMENT ON COLUMN menus.primary_color IS 'Primary/background color (60% of UI)';
COMMENT ON COLUMN menus.secondary_color IS 'Secondary color for header/categories (30% of UI)';
COMMENT ON COLUMN menus.theme_color IS 'Accent color for CTAs, highlights, prices (10% of UI)';

-- Update existing menus with sensible defaults based on existing theme_color
-- If theme_color is dark, use light primary/secondary
-- If theme_color is light, use dark primary/secondary
UPDATE menus
SET
    primary_color = '#ffffff',
    secondary_color = '#f3f4f6'
WHERE primary_color IS NULL OR secondary_color IS NULL;

COMMIT;
