-- Add flags to playlists table for special playlist types

ALTER TABLE playlists 
    ADD COLUMN IF NOT EXISTS is_default BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS is_pms_template BOOLEAN DEFAULT FALSE;

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_playlists_is_default ON playlists(is_default) WHERE is_default = TRUE;
CREATE INDEX IF NOT EXISTS idx_playlists_is_pms_template ON playlists(is_pms_template) WHERE is_pms_template = TRUE;

-- Add unique constraint to ensure only one default playlist per organization
CREATE UNIQUE INDEX IF NOT EXISTS idx_playlists_one_default_per_org 
    ON playlists(organization_id) 
    WHERE is_default = TRUE;

-- Add comments
COMMENT ON COLUMN playlists.is_default IS 'If true, this is the default playlist for the organization';
COMMENT ON COLUMN playlists.is_pms_template IS 'If true, this playlist is used as PMS template for guest content';
