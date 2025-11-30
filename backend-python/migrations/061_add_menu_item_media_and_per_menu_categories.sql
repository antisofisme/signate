-- Migration: 061
-- Description: Add menu_item_media junction table and per-menu categories
-- Date: 2025-11-30
-- Features:
--   1. Multiple media per menu item (junction table)
--   2. Categories specific to each menu (not just menu_type)

BEGIN;

-- ==============================================================================
-- 1. Create menu_item_media junction table for multiple media per item
-- ==============================================================================

CREATE TABLE menu_item_media (
  id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  menu_item_id INTEGER NOT NULL REFERENCES menu_items(id) ON DELETE CASCADE,
  menu_media_id INTEGER NOT NULL REFERENCES menu_media(id) ON DELETE CASCADE,
  display_order INTEGER DEFAULT 0 NOT NULL,
  is_primary BOOLEAN DEFAULT FALSE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

  -- Ensure unique combination of item and media
  CONSTRAINT unique_menu_item_media UNIQUE (menu_item_id, menu_media_id)
);

-- Indexes
CREATE INDEX idx_menu_item_media_item ON menu_item_media(menu_item_id);
CREATE INDEX idx_menu_item_media_media ON menu_item_media(menu_media_id);
CREATE INDEX idx_menu_item_media_order ON menu_item_media(menu_item_id, display_order);

-- Comments
COMMENT ON TABLE menu_item_media IS 'Junction table for multiple media per menu item';
COMMENT ON COLUMN menu_item_media.is_primary IS 'Primary media shown as main image in item card';
COMMENT ON COLUMN menu_item_media.display_order IS 'Order in media gallery (0 = first)';

-- ==============================================================================
-- 2. Add menu_id to menu_categories for per-menu categories
-- ==============================================================================

-- Add menu_id column (nullable first for existing data)
ALTER TABLE menu_categories ADD COLUMN menu_id INTEGER REFERENCES menus(id) ON DELETE CASCADE;

-- Create index
CREATE INDEX idx_menu_categories_menu ON menu_categories(menu_id);

-- Drop old unique constraint
ALTER TABLE menu_categories DROP CONSTRAINT IF EXISTS unique_menu_categories_org_type_name;

-- Add new unique constraint (categories unique per menu)
ALTER TABLE menu_categories ADD CONSTRAINT unique_menu_categories_menu_name
  UNIQUE (menu_id, name);

-- Update comment
COMMENT ON COLUMN menu_categories.menu_id IS 'Menu this category belongs to (per-menu categories)';

COMMIT;
