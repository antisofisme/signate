-- Migration: 057
-- Description: Add menu_media table for storing menu-specific images
-- Date: 2025-11-30

BEGIN;

-- Create menu_media table for menu-specific images (separate from content)
CREATE TABLE IF NOT EXISTS menu_media (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- File information
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL DEFAULT 0,
    mime_type VARCHAR(100) NOT NULL,

    -- Image metadata
    width INTEGER,
    height INTEGER,

    -- Thumbnail
    thumbnail_path VARCHAR(500),

    -- Display
    title VARCHAR(200),
    alt_text VARCHAR(255),

    -- Status
    is_active BOOLEAN DEFAULT TRUE NOT NULL,

    -- Audit trail
    uploaded_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for performance
CREATE INDEX idx_menu_media_organization ON menu_media(organization_id);
CREATE INDEX idx_menu_media_deleted ON menu_media(deleted_at);
CREATE INDEX idx_menu_media_active ON menu_media(is_active) WHERE deleted_at IS NULL;

-- Comment on table
COMMENT ON TABLE menu_media IS 'Media files specifically for digital menus (separate from content library)';

-- Add menu_media_id to menu_items for direct reference
ALTER TABLE menu_items
ADD COLUMN IF NOT EXISTS menu_media_id INTEGER REFERENCES menu_media(id) ON DELETE SET NULL;

-- Index for menu items menu_media reference
CREATE INDEX IF NOT EXISTS idx_menu_items_media ON menu_items(menu_media_id);

COMMIT;
