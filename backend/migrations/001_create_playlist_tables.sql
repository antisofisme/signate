-- Migration: Create Playlist Tables
-- Date: 2025-10-26
-- Description: Add playlist functionality with content management and device/tag assignments

-- Create playlists table
CREATE TABLE IF NOT EXISTS playlists (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    priority INTEGER NOT NULL DEFAULT 1,
    schedule JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for playlists
CREATE INDEX IF NOT EXISTS idx_playlists_is_active ON playlists(is_active);
CREATE INDEX IF NOT EXISTS idx_playlists_name ON playlists(name);

-- Create playlist_content join table
CREATE TABLE IF NOT EXISTS playlist_content (
    id SERIAL PRIMARY KEY,
    playlist_id INTEGER NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
    content_id INTEGER NOT NULL REFERENCES content(id) ON DELETE CASCADE,
    order_index INTEGER NOT NULL DEFAULT 0,
    duration INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for playlist_content
CREATE INDEX IF NOT EXISTS idx_playlist_content_playlist_id ON playlist_content(playlist_id);
CREATE INDEX IF NOT EXISTS idx_playlist_content_content_id ON playlist_content(content_id);

-- Create playlist_assignments table
CREATE TABLE IF NOT EXISTS playlist_assignments (
    id SERIAL PRIMARY KEY,
    playlist_id INTEGER NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
    device_id INTEGER REFERENCES devices(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT check_device_or_tag CHECK (
        (device_id IS NOT NULL AND tag_id IS NULL) OR
        (device_id IS NULL AND tag_id IS NOT NULL)
    )
);

-- Create indexes for playlist_assignments
CREATE INDEX IF NOT EXISTS idx_playlist_assignments_playlist_id ON playlist_assignments(playlist_id);
CREATE INDEX IF NOT EXISTS idx_playlist_assignments_device_id ON playlist_assignments(device_id);
CREATE INDEX IF NOT EXISTS idx_playlist_assignments_tag_id ON playlist_assignments(tag_id);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_playlist_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_playlist_updated_at
BEFORE UPDATE ON playlists
FOR EACH ROW
EXECUTE FUNCTION update_playlist_updated_at();

COMMIT;
