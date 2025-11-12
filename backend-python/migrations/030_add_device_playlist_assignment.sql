-- Add assigned_playlist_id to devices table
-- Allows direct playlist assignment to devices

ALTER TABLE devices 
    ADD COLUMN IF NOT EXISTS assigned_playlist_id INTEGER REFERENCES playlists(id) ON DELETE SET NULL;

-- Add index for better performance
CREATE INDEX IF NOT EXISTS idx_devices_assigned_playlist ON devices(assigned_playlist_id) WHERE assigned_playlist_id IS NOT NULL;

-- Add comment
COMMENT ON COLUMN devices.assigned_playlist_id IS 'Direct playlist assignment to device';
