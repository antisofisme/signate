-- Migration: 082
-- Description: Add device_capabilities table for static device info (codecs, hardware, display)
-- Date: 2025-12-05
-- Purpose: Store static device capabilities sent once on startup (not repeated in heartbeats)

BEGIN;

-- =============================================================================
-- CREATE DEVICE CAPABILITIES TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS device_capabilities (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Foreign keys
    device_id INTEGER NOT NULL UNIQUE REFERENCES devices(id) ON DELETE CASCADE,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Screen & Display
    screen_width INTEGER NOT NULL,
    screen_height INTEGER NOT NULL,
    device_pixel_ratio FLOAT NOT NULL,
    display_refresh_rate INTEGER NOT NULL,

    -- Hardware
    hardware_concurrency INTEGER NOT NULL,  -- CPU cores
    device_memory_gb FLOAT,  -- Device RAM in GB (Chrome/Edge only, can be NULL)

    -- Video Codec Support
    codec_h264 BOOLEAN NOT NULL DEFAULT FALSE,
    codec_h265 BOOLEAN NOT NULL DEFAULT FALSE,
    codec_vp9 BOOLEAN NOT NULL DEFAULT FALSE,
    codec_av1 BOOLEAN NOT NULL DEFAULT FALSE,

    -- Audio Codec Support
    codec_aac BOOLEAN NOT NULL DEFAULT FALSE,
    codec_opus BOOLEAN NOT NULL DEFAULT FALSE,

    -- Graphics
    webgl_version VARCHAR(10) NOT NULL,  -- "none", "1.0", "2.0"
    webgl_renderer VARCHAR(200),
    webgl_vendor VARCHAR(200),

    -- Software
    user_agent TEXT NOT NULL,
    platform VARCHAR(50) NOT NULL,
    player_version VARCHAR(50) NOT NULL,

    -- Timestamps
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- =============================================================================
-- CREATE INDEXES
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_device_capabilities_device ON device_capabilities(device_id);
CREATE INDEX IF NOT EXISTS idx_device_capabilities_organization ON device_capabilities(organization_id);

-- =============================================================================
-- ADD COMMENTS
-- =============================================================================

COMMENT ON TABLE device_capabilities IS 'Stores static device capabilities (codecs, hardware, display) - sent once on startup';
COMMENT ON COLUMN device_capabilities.device_id IS 'Reference to device (unique - one record per device)';
COMMENT ON COLUMN device_capabilities.organization_id IS 'Organization for multi-tenancy filtering';
COMMENT ON COLUMN device_capabilities.hardware_concurrency IS 'Number of logical CPU cores (navigator.hardwareConcurrency)';
COMMENT ON COLUMN device_capabilities.device_memory_gb IS 'Device RAM in GB (navigator.deviceMemory - Chrome/Edge only)';
COMMENT ON COLUMN device_capabilities.codec_h264 IS 'H.264/AVC video codec support';
COMMENT ON COLUMN device_capabilities.codec_h265 IS 'H.265/HEVC video codec support';
COMMENT ON COLUMN device_capabilities.codec_vp9 IS 'VP9 video codec support';
COMMENT ON COLUMN device_capabilities.codec_av1 IS 'AV1 video codec support';
COMMENT ON COLUMN device_capabilities.codec_aac IS 'AAC audio codec support';
COMMENT ON COLUMN device_capabilities.codec_opus IS 'Opus audio codec support';
COMMENT ON COLUMN device_capabilities.webgl_version IS 'WebGL version: none, 1.0, or 2.0';
COMMENT ON COLUMN device_capabilities.recorded_at IS 'When capabilities were first recorded';
COMMENT ON COLUMN device_capabilities.updated_at IS 'When capabilities were last updated';

COMMIT;
