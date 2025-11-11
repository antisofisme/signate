-- Migration 027: Widget System
-- Phase 5: Advanced Features - Dynamic widgets for overlays

BEGIN;

-- Widget definitions
CREATE TABLE IF NOT EXISTS widgets (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Widget Info
    name VARCHAR(255) NOT NULL,
    description TEXT,
    widget_type VARCHAR(50) NOT NULL, -- 'clock', 'weather', 'news', 'hotel_info', 'custom'

    -- Configuration
    config JSONB NOT NULL, -- Widget-specific settings
    layout JSONB, -- {"position": "top-right", "width": 300, "height": 100}

    -- Status
    is_active BOOLEAN DEFAULT true,

    -- Metadata
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(organization_id, name)
);

-- Widget assignments to playlists
CREATE TABLE IF NOT EXISTS playlist_widgets (
    id SERIAL PRIMARY KEY,
    playlist_id INTEGER NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
    widget_id INTEGER NOT NULL REFERENCES widgets(id) ON DELETE CASCADE,

    -- Display settings
    position INTEGER DEFAULT 0, -- Order in playlist
    display_duration INTEGER, -- Seconds (NULL = always show)
    z_index INTEGER DEFAULT 100, -- Layer order

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(playlist_id, widget_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_widgets_org ON widgets(organization_id);
CREATE INDEX IF NOT EXISTS idx_widgets_type ON widgets(widget_type);
CREATE INDEX IF NOT EXISTS idx_widgets_active ON widgets(is_active);
CREATE INDEX IF NOT EXISTS idx_playlist_widgets_playlist ON playlist_widgets(playlist_id);
CREATE INDEX IF NOT EXISTS idx_playlist_widgets_widget ON playlist_widgets(widget_id);

-- Triggers
CREATE OR REPLACE FUNCTION update_widgets_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER widgets_updated_at
    BEFORE UPDATE ON widgets
    FOR EACH ROW
    EXECUTE FUNCTION update_widgets_updated_at();

COMMIT;
