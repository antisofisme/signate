-- Migration: 066
-- Description: Add variant column to menu_items for item variations (Hot, Cold, Large, Small)
-- Date: 2024-12-01

BEGIN;

-- Add variant column to menu_items
-- Variant is for item variations like: Hot, Cold, Large, Small, Spicy, etc.
-- Subcategory remains for category-based grouping: Nasi, Mie, Ayam, etc.
ALTER TABLE menu_items
  ADD COLUMN IF NOT EXISTS variant VARCHAR(200);

-- Add comment
COMMENT ON COLUMN menu_items.variant IS 'Item variations like Hot, Cold, Large, Small (comma-separated)';

COMMIT;
