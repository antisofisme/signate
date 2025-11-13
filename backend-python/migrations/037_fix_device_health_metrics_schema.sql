-- Fix device_health_metrics table schema
-- Add missing columns for comprehensive health monitoring

ALTER TABLE device_health_metrics
    ADD COLUMN IF NOT EXISTS memory_total_mb INTEGER,
    ADD COLUMN IF NOT EXISTS memory_used_mb INTEGER,
    ADD COLUMN IF NOT EXISTS disk_total_gb INTEGER,
    ADD COLUMN IF NOT EXISTS disk_used_gb INTEGER,
    ADD COLUMN IF NOT EXISTS network_latency_ms INTEGER,
    ADD COLUMN IF NOT EXISTS network_download_mbps NUMERIC(10,2),
    ADD COLUMN IF NOT EXISTS network_upload_mbps NUMERIC(10,2),
    ADD COLUMN IF NOT EXISTS connection_quality VARCHAR(20),
    ADD COLUMN IF NOT EXISTS display_resolution VARCHAR(20),
    ADD COLUMN IF NOT EXISTS display_refresh_rate INTEGER,
    ADD COLUMN IF NOT EXISTS gpu_usage NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS player_version VARCHAR(50),
    ADD COLUMN IF NOT EXISTS player_uptime_hours INTEGER,
    ADD COLUMN IF NOT EXISTS content_errors_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS last_error_message TEXT,
    ADD COLUMN IF NOT EXISTS last_error_at TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS overall_status VARCHAR(20) DEFAULT 'healthy'::VARCHAR,
    ADD COLUMN IF NOT EXISTS alert_triggered BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS alert_message TEXT,
    ADD COLUMN IF NOT EXISTS metadata JSONB,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_device_health_metrics_overall_status ON device_health_metrics(overall_status);
CREATE INDEX IF NOT EXISTS idx_device_health_metrics_alert ON device_health_metrics(alert_triggered) WHERE alert_triggered = TRUE;

-- Add comments
COMMENT ON COLUMN device_health_metrics.memory_total_mb IS 'Total memory in MB';
COMMENT ON COLUMN device_health_metrics.memory_used_mb IS 'Used memory in MB';
COMMENT ON COLUMN device_health_metrics.overall_status IS 'Overall health status (healthy, warning, critical)';
