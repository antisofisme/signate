-- ============================================================================
-- 010_add_device_logs_and_speed_tests.sql
-- Add device logs and speed tests tables
-- ============================================================================

-- Device logs table
CREATE TABLE IF NOT EXISTS device_logs (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_device_logs_device ON device_logs(device_id);
CREATE INDEX IF NOT EXISTS idx_device_logs_timestamp ON device_logs(timestamp);

-- Device speed tests table  
CREATE TABLE IF NOT EXISTS device_speed_tests (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    download_speed NUMERIC(10,2),
    upload_speed NUMERIC(10,2),
    ping INTEGER,
    test_server VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_device_speed_tests_device ON device_speed_tests(device_id);
CREATE INDEX IF NOT EXISTS idx_device_speed_tests_created ON device_speed_tests(created_at);