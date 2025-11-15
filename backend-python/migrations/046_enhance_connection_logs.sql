-- Migration: 046
-- Description: Add dedicated columns for frequently queried connection log fields
-- Date: 2025-01-16

BEGIN;

-- Add dedicated columns for network info
ALTER TABLE device_connection_logs
  ADD COLUMN connection_type VARCHAR(20),
  ADD COLUMN effective_type VARCHAR(10),
  ADD COLUMN rtt_ms INTEGER;

-- Add dedicated columns for server info  
ALTER TABLE device_connection_logs
  ADD COLUMN endpoint VARCHAR(200),
  ADD COLUMN http_status INTEGER;

-- Add dedicated columns for speed test info
ALTER TABLE device_connection_logs
  ADD COLUMN test_trigger VARCHAR(10),
  ADD COLUMN test_duration_ms INTEGER;

-- Add indexes for analytics queries
CREATE INDEX idx_device_logs_connection_type ON device_connection_logs(connection_type) WHERE connection_type IS NOT NULL;
CREATE INDEX idx_device_logs_effective_type ON device_connection_logs(effective_type) WHERE effective_type IS NOT NULL;
CREATE INDEX idx_device_logs_http_status ON device_connection_logs(http_status) WHERE http_status IS NOT NULL;
CREATE INDEX idx_device_logs_test_trigger ON device_connection_logs(test_trigger) WHERE test_trigger IS NOT NULL;

-- Add check constraints
ALTER TABLE device_connection_logs
  ADD CONSTRAINT check_connection_type 
    CHECK (connection_type IS NULL OR connection_type IN ('wifi', 'ethernet', 'cellular', 'bluetooth', 'wimax', 'other', 'none', 'unknown')),
  ADD CONSTRAINT check_effective_type
    CHECK (effective_type IS NULL OR effective_type IN ('slow-2g', '2g', '3g', '4g', '5g', 'unknown')),
  ADD CONSTRAINT check_test_trigger
    CHECK (test_trigger IS NULL OR test_trigger IN ('auto', 'manual')),
  ADD CONSTRAINT check_rtt_ms
    CHECK (rtt_ms IS NULL OR rtt_ms >= 0),
  ADD CONSTRAINT check_test_duration_ms
    CHECK (test_duration_ms IS NULL OR test_duration_ms >= 0);

-- Add comments
COMMENT ON COLUMN device_connection_logs.connection_type IS 'Network connection type (wifi, ethernet, cellular, etc)';
COMMENT ON COLUMN device_connection_logs.effective_type IS 'Effective network type (4g, 3g, 2g, etc)';
COMMENT ON COLUMN device_connection_logs.rtt_ms IS 'Round-trip time in milliseconds';
COMMENT ON COLUMN device_connection_logs.endpoint IS 'API endpoint accessed';
COMMENT ON COLUMN device_connection_logs.http_status IS 'HTTP status code';
COMMENT ON COLUMN device_connection_logs.test_trigger IS 'How speed test was triggered (auto/manual)';
COMMENT ON COLUMN device_connection_logs.test_duration_ms IS 'Speed test duration in milliseconds';

COMMIT;
