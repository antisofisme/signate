-- Migration: 064
-- Description: Add subcategories JSONB column to menu_categories for nested subcategory management
-- Date: 2025-12-01

BEGIN;

-- Add subcategories column to menu_categories table
-- Stores array of subcategory names: ["Nasi", "Mie", "Ayam"]
ALTER TABLE menu_categories
ADD COLUMN IF NOT EXISTS subcategories JSONB DEFAULT '[]'::jsonb NOT NULL;

-- Add comment for documentation
COMMENT ON COLUMN menu_categories.subcategories IS 'Array of subcategory names for this category, e.g. ["Nasi", "Mie", "Ayam"]';

-- Create index for JSONB operations (optional, for performance)
CREATE INDEX IF NOT EXISTS idx_menu_categories_subcategories
ON menu_categories USING GIN (subcategories);

COMMIT;
