-- Add priority and playlist assignment to tags
-- Allows tags to have playlist assignments for content routing

ALTER TABLE tags 
    ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 50,
    ADD COLUMN IF NOT EXISTS assigned_playlist_id INTEGER REFERENCES playlists(id) ON DELETE SET NULL;

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_tags_priority ON tags(priority);
CREATE INDEX IF NOT EXISTS idx_tags_assigned_playlist ON tags(assigned_playlist_id) WHERE assigned_playlist_id IS NOT NULL;

-- Add comments
COMMENT ON COLUMN tags.priority IS 'Priority for tag-based playlist resolution (higher = more important)';
COMMENT ON COLUMN tags.assigned_playlist_id IS 'Default playlist assigned to devices with this tag';
