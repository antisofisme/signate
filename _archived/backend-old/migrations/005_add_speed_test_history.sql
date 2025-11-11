-- Migration: 005_add_speed_test_history.sql
-- Date: 2025-10-27
-- Description: Add speed test history tracking for device network monitoring

BEGIN;

-- Create device_speed_tests table
CREATE TABLE IF NOT EXISTS device_speed_tests (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,

    -- Speed metrics
    download_speed DECIMAL(10, 2) NOT NULL,  -- Mbps (e.g., 50.35)
    upload_speed DECIMAL(10, 2) NOT NULL,    -- Mbps (e.g., 25.10)
    latency INTEGER,                          -- Optional: ping latency in ms
    jitter INTEGER,                           -- Optional: jitter in ms
    packet_loss DECIMAL(5, 2),               -- Optional: packet loss percentage (0.00-100.00)

    -- DNS and quality metrics
    dns_server VARCHAR(45),                   -- IPv4 or IPv6 address
    quality VARCHAR(20) NOT NULL,             -- 'good', 'fair', 'poor'

    -- Test metadata
    tested_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    test_duration_ms INTEGER,                 -- How long the test took (for audit)

    -- Additional context
    server_endpoint VARCHAR(255),             -- Which server was used for testing
    error_message TEXT,                       -- If test partially failed

    CONSTRAINT check_quality_values CHECK (quality IN ('good', 'fair', 'poor')),
    CONSTRAINT check_speeds_positive CHECK (
        download_speed >= 0 AND
        upload_speed >= 0
    )
);

-- Performance indexes
CREATE INDEX idx_speed_tests_device_id ON device_speed_tests(device_id);
CREATE INDEX idx_speed_tests_tested_at ON device_speed_tests(tested_at DESC);
CREATE INDEX idx_speed_tests_device_tested ON device_speed_tests(device_id, tested_at DESC);
CREATE INDEX idx_speed_tests_quality ON device_speed_tests(quality);

-- Create view for latest test per device (performance optimization)
CREATE OR REPLACE VIEW device_latest_speed_test AS
SELECT DISTINCT ON (device_id)
    id,
    device_id,
    download_speed,
    upload_speed,
    latency,
    jitter,
    packet_loss,
    dns_server,
    quality,
    tested_at,
    test_duration_ms
FROM device_speed_tests
ORDER BY device_id, tested_at DESC;

COMMIT;
