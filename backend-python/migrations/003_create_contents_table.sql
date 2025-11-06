-- ============================================================================
-- Migration: Create Contents Table
-- Description: Content management with custom storage system (NO Anthias!)
-- Created: 2025-01-06
-- ============================================================================

-- Create contents table
CREATE TABLE IF NOT EXISTS contents (
    -- Identity
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    content_type VARCHAR(20) NOT NULL,

    -- File Storage (Custom System - Local Filesystem)
    file_path VARCHAR(500) NOT NULL,
    file_url VARCHAR(500) NOT NULL,
    storage_key VARCHAR(255) NOT NULL UNIQUE,
    file_hash VARCHAR(64) NOT NULL,

    -- Display Settings
    duration INTEGER DEFAULT 10 NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,

    -- File Metadata
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_extension VARCHAR(20) NOT NULL,

    -- Media Properties (Image/Video)
    resolution VARCHAR(50),
    width INTEGER,
    height INTEGER,
    codec VARCHAR(50),
    fps FLOAT,
    bitrate INTEGER,

    -- Video/Audio Specific
    media_duration FLOAT,
    video_start_time FLOAT DEFAULT 0.0 NOT NULL,
    video_end_time FLOAT,
    audio_codec VARCHAR(50),
    audio_bitrate INTEGER,
    audio_sample_rate INTEGER,
    audio_channels INTEGER DEFAULT 2 NOT NULL,

    -- Transcoding (HLS for video)
    transcoding_status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    transcoding_job_id VARCHAR(200),
    transcoding_progress INTEGER DEFAULT 0 NOT NULL,
    transcoding_error TEXT,
    hls_master_playlist_path VARCHAR(500),
    hls_master_playlist_url VARCHAR(500),
    hls_variants JSONB,

    -- Thumbnail
    thumbnail_path VARCHAR(500),
    thumbnail_url VARCHAR(500),
    thumbnail_generated_at TIMESTAMP WITH TIME ZONE,

    -- Upload Status
    upload_status VARCHAR(20) DEFAULT 'pending' NOT NULL,

    -- Multi-tenant (organization-scoped)
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    uploaded_by INTEGER REFERENCES users(id) ON DELETE SET NULL,

    -- Audit Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Organization + Active Status (for listing active content)
CREATE INDEX idx_content_org_active ON contents(organization_id, is_active);

-- Organization + Content Type (for filtering by type)
CREATE INDEX idx_content_org_type ON contents(organization_id, content_type);

-- Organization + Created Date (for sorting)
CREATE INDEX idx_content_org_created ON contents(organization_id, created_at);

-- File Hash + Organization (for deduplication check)
CREATE INDEX idx_content_hash_org ON contents(file_hash, organization_id);

-- Storage Key (for file operations)
CREATE INDEX idx_content_storage_key ON contents(storage_key);

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON TABLE contents IS 'Content files with custom storage system (images, videos, audio)';
COMMENT ON COLUMN contents.storage_key IS 'Unique storage path: {type}s/{year}/{month}/org_{id}/{uuid}.{ext}';
COMMENT ON COLUMN contents.file_hash IS 'SHA256 hash for deduplication within organization';
COMMENT ON COLUMN contents.hls_variants IS 'JSON array of HLS quality variants (e.g., [{"quality": "720p", "path": "..."}])';
COMMENT ON COLUMN contents.transcoding_status IS 'Status: pending, processing, completed, failed';
COMMENT ON COLUMN contents.upload_status IS 'Status: pending, completed, failed';

-- ============================================================================
-- Migration Complete
-- ============================================================================

-- To run this migration on server:
-- docker exec -i signage-postgres psql -U signage_user -d signage_db < backend-python/migrations/003_create_contents_table.sql
