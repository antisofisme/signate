-- Migration 008: Create Device Support Tables
-- Created: 2025-01-07
-- Description: Device commands, logs, and speed tests for monitoring and remote management

-- ============================================================================
-- 1. DEVICE_COMMANDS TABLE (Remote Command Queue)
-- ============================================================================
CREATE TABLE IF NOT EXISTS device_commands (
    id SERIAL PRIMARY KEY,

    -- Target device
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Command details
    command_type VARCHAR(50) NOT NULL CHECK (command_type IN ('reset', 'refresh', 'reload', 'speed_test', 'update_content', 'reboot', 'screenshot', 'volume', 'brightness')),
    parameters JSONB,  -- Command-specific parameters
    reason VARCHAR(200),  -- Why command was issued

    -- Command status
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'executed', 'failed', 'expired')),
    sent_at TIMESTAMP WITH TIME ZONE,
    executed_at TIMESTAMP WITH TIME ZONE,
    error_message VARCHAR(500),

    -- Audit & expiration
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    expires_at TIMESTAMP WITH TIME ZONE,  -- Auto-expire after 7 days
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes for command queue performance
CREATE INDEX IF NOT EXISTS idx_commands_device ON device_commands(device_id);
CREATE INDEX IF NOT EXISTS idx_commands_status ON device_commands(status);
CREATE INDEX IF NOT EXISTS idx_commands_expires ON device_commands(expires_at);
CREATE INDEX IF NOT EXISTS idx_commands_organization ON device_commands(organization_id);
CREATE INDEX IF NOT EXISTS idx_commands_device_status ON device_commands(device_id, status);

-- ============================================================================
-- 2. DEVICE_LOGS TABLE (Remote Debugging)
-- ============================================================================
CREATE TABLE IF NOT EXISTS device_logs (
    id SERIAL PRIMARY KEY,

    -- Target device
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Log details
    log_level VARCHAR(20) NOT NULL CHECK (log_level IN ('log', 'info', 'warn', 'error', 'debug')),
    message TEXT NOT NULL,
    source VARCHAR(500),  -- File/function where log originated
    stack_trace TEXT,  -- For errors

    -- Metadata
    user_agent VARCHAR(500),
    url VARCHAR(1000),  -- Current page URL when logged

    -- Timestamp
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes for log retrieval
CREATE INDEX IF NOT EXISTS idx_logs_device ON device_logs(device_id);
CREATE INDEX IF NOT EXISTS idx_logs_level ON device_logs(log_level);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON device_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_logs_organization ON device_logs(organization_id);
CREATE INDEX IF NOT EXISTS idx_logs_device_level_timestamp ON device_logs(device_id, log_level, timestamp DESC);

-- ============================================================================
-- 3. DEVICE_SPEED_TESTS TABLE (Network Monitoring)
-- ============================================================================
CREATE TABLE IF NOT EXISTS device_speed_tests (
    id SERIAL PRIMARY KEY,

    -- Target device
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Speed test results
    download_speed NUMERIC(10, 2),  -- Mbps
    upload_speed NUMERIC(10, 2),    -- Mbps
    latency INTEGER,                -- Ping in milliseconds
    jitter INTEGER,                 -- Network jitter in ms
    packet_loss NUMERIC(5, 2),      -- Loss percentage (0.00-100.00)

    -- Network details
    dns_server VARCHAR(45),         -- DNS server IP used
    server_endpoint VARCHAR(255),   -- Speed test server used
    quality VARCHAR(20) CHECK (quality IN ('good', 'fair', 'poor')),

    -- Test metadata
    test_duration_ms INTEGER,       -- How long test took
    error_message TEXT,             -- If test partially failed

    -- Timestamp
    tested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes for speed test history
CREATE INDEX IF NOT EXISTS idx_speed_device ON device_speed_tests(device_id);
CREATE INDEX IF NOT EXISTS idx_speed_tested ON device_speed_tests(tested_at DESC);
CREATE INDEX IF NOT EXISTS idx_speed_organization ON device_speed_tests(organization_id);
CREATE INDEX IF NOT EXISTS idx_speed_device_tested ON device_speed_tests(device_id, tested_at DESC);
CREATE INDEX IF NOT EXISTS idx_speed_quality ON device_speed_tests(quality);

-- ============================================================================
-- 4. ADD INDEX TO PLAYLIST_DEVICES (Performance Optimization)
-- ============================================================================
-- Note: playlist_devices table already exists from migration 005
-- We're just adding an index for better device-to-playlist lookup performance

CREATE INDEX IF NOT EXISTS idx_playlist_devices_device ON playlist_devices(device_id);

-- ============================================================================
-- COMMENTS (Documentation)
-- ============================================================================

-- Device Commands
COMMENT ON TABLE device_commands IS 'Remote command queue for device management';
COMMENT ON COLUMN device_commands.command_type IS 'Type of command: reset (clear & reload), refresh (cache clear), reload (page reload), speed_test, update_content, reboot, screenshot, volume, brightness';
COMMENT ON COLUMN device_commands.parameters IS 'JSON parameters for command execution (e.g., {"level": 75} for volume)';
COMMENT ON COLUMN device_commands.status IS 'Command lifecycle: pending → sent → executed/failed/expired';
COMMENT ON COLUMN device_commands.expires_at IS 'Command auto-expires after 7 days if not executed';

-- Device Logs
COMMENT ON TABLE device_logs IS 'Remote console logs from devices for debugging';
COMMENT ON COLUMN device_logs.log_level IS 'Log severity: log (general), info, warn, error, debug';
COMMENT ON COLUMN device_logs.source IS 'Code location where log originated (file:line)';
COMMENT ON COLUMN device_logs.stack_trace IS 'Error stack trace for debugging';

-- Device Speed Tests
COMMENT ON TABLE device_speed_tests IS 'Network speed test results history';
COMMENT ON COLUMN device_speed_tests.download_speed IS 'Download speed in Mbps';
COMMENT ON COLUMN device_speed_tests.upload_speed IS 'Upload speed in Mbps';
COMMENT ON COLUMN device_speed_tests.latency IS 'Network latency (ping) in milliseconds';
COMMENT ON COLUMN device_speed_tests.quality IS 'Test result quality: good (>=25 Mbps down), fair (>=10 Mbps), poor (<10 Mbps)';

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify all tables created
SELECT
    table_name,
    (SELECT count(*) FROM information_schema.columns WHERE c.table_name = t.table_name) as column_count
FROM information_schema.tables t
CROSS JOIN LATERAL (SELECT table_name FROM unnest(ARRAY['device_commands', 'device_logs', 'device_speed_tests']) AS table_name) c
WHERE t.table_name IN ('device_commands', 'device_logs', 'device_speed_tests')
ORDER BY table_name;

-- Verify indexes created
SELECT
    tablename,
    indexname
FROM pg_indexes
WHERE tablename IN ('device_commands', 'device_logs', 'device_speed_tests', 'playlist_devices')
ORDER BY tablename, indexname;

-- Count existing records (should be 0 for new tables)
SELECT 'device_commands' as table_name, count(*) as record_count FROM device_commands
UNION ALL
SELECT 'device_logs', count(*) FROM device_logs
UNION ALL
SELECT 'device_speed_tests', count(*) FROM device_speed_tests;
