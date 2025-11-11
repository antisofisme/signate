-- Migration 022: Add Device Health Metrics System
-- Phase 4: Remote Device Monitoring
-- Purpose: Track device health metrics (CPU, memory, disk, network) for monitoring

-- ============================================================================
-- TABLE: device_health_metrics
-- ============================================================================
CREATE TABLE IF NOT EXISTS device_health_metrics (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- System metrics
    cpu_usage DECIMAL(5,2), -- Percentage (0-100)
    memory_usage DECIMAL(5,2), -- Percentage (0-100)
    memory_total_mb INTEGER, -- Total memory in MB
    memory_used_mb INTEGER, -- Used memory in MB
    disk_usage DECIMAL(5,2), -- Percentage (0-100)
    disk_total_gb INTEGER, -- Total disk in GB
    disk_used_gb INTEGER, -- Used disk in GB

    -- Network metrics
    network_latency_ms INTEGER, -- Latency to backend in milliseconds
    network_download_mbps DECIMAL(10,2), -- Download speed in Mbps
    network_upload_mbps DECIMAL(10,2), -- Upload speed in Mbps
    connection_quality VARCHAR(20), -- 'excellent', 'good', 'fair', 'poor'

    -- Display metrics
    display_resolution VARCHAR(20), -- e.g., "1920x1080"
    display_refresh_rate INTEGER, -- Hz
    gpu_usage DECIMAL(5,2), -- Percentage (0-100)

    -- Player metrics
    player_version VARCHAR(50), -- Player app version
    player_uptime_hours INTEGER, -- Hours since player started
    content_errors_count INTEGER DEFAULT 0, -- Number of content loading errors
    last_error_message TEXT,
    last_error_at TIMESTAMP WITH TIME ZONE,

    -- Health status
    overall_status VARCHAR(20) DEFAULT 'healthy', -- 'healthy', 'warning', 'critical', 'offline'
    alert_triggered BOOLEAN DEFAULT FALSE,
    alert_message TEXT,

    -- Additional data
    metadata JSONB DEFAULT '{}', -- Additional metrics in JSON format

    -- Timestamps
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_overall_status CHECK (overall_status IN ('healthy', 'warning', 'critical', 'offline')),
    CONSTRAINT valid_connection_quality CHECK (connection_quality IN ('excellent', 'good', 'fair', 'poor') OR connection_quality IS NULL)
);

-- Create indexes for performance
CREATE INDEX idx_device_health_device_id ON device_health_metrics(device_id);
CREATE INDEX idx_device_health_organization_id ON device_health_metrics(organization_id);
CREATE INDEX idx_device_health_recorded_at ON device_health_metrics(recorded_at);
CREATE INDEX idx_device_health_overall_status ON device_health_metrics(overall_status);
CREATE INDEX idx_device_health_alert_triggered ON device_health_metrics(alert_triggered);

-- Composite index for latest metrics by device
CREATE INDEX idx_device_health_device_latest
ON device_health_metrics(device_id, recorded_at DESC);

-- ============================================================================
-- STORED FUNCTIONS
-- ============================================================================

-- Function: Get latest health metrics for a device
CREATE OR REPLACE FUNCTION get_latest_device_health(p_device_id INTEGER)
RETURNS TABLE (
    id INTEGER,
    cpu_usage DECIMAL(5,2),
    memory_usage DECIMAL(5,2),
    memory_total_mb INTEGER,
    memory_used_mb INTEGER,
    disk_usage DECIMAL(5,2),
    disk_total_gb INTEGER,
    disk_used_gb INTEGER,
    network_latency_ms INTEGER,
    network_download_mbps DECIMAL(10,2),
    network_upload_mbps DECIMAL(10,2),
    connection_quality VARCHAR(20),
    display_resolution VARCHAR(20),
    display_refresh_rate INTEGER,
    gpu_usage DECIMAL(5,2),
    player_version VARCHAR(50),
    player_uptime_hours INTEGER,
    content_errors_count INTEGER,
    last_error_message TEXT,
    last_error_at TIMESTAMP WITH TIME ZONE,
    overall_status VARCHAR(20),
    alert_triggered BOOLEAN,
    alert_message TEXT,
    metadata JSONB,
    recorded_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        dhm.id,
        dhm.cpu_usage,
        dhm.memory_usage,
        dhm.memory_total_mb,
        dhm.memory_used_mb,
        dhm.disk_usage,
        dhm.disk_total_gb,
        dhm.disk_used_gb,
        dhm.network_latency_ms,
        dhm.network_download_mbps,
        dhm.network_upload_mbps,
        dhm.connection_quality,
        dhm.display_resolution,
        dhm.display_refresh_rate,
        dhm.gpu_usage,
        dhm.player_version,
        dhm.player_uptime_hours,
        dhm.content_errors_count,
        dhm.last_error_message,
        dhm.last_error_at,
        dhm.overall_status,
        dhm.alert_triggered,
        dhm.alert_message,
        dhm.metadata,
        dhm.recorded_at
    FROM device_health_metrics dhm
    WHERE dhm.device_id = p_device_id
    ORDER BY dhm.recorded_at DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Function: Get health history for a device
CREATE OR REPLACE FUNCTION get_device_health_history(
    p_device_id INTEGER,
    p_hours INTEGER DEFAULT 24
)
RETURNS TABLE (
    id INTEGER,
    cpu_usage DECIMAL(5,2),
    memory_usage DECIMAL(5,2),
    disk_usage DECIMAL(5,2),
    network_latency_ms INTEGER,
    connection_quality VARCHAR(20),
    overall_status VARCHAR(20),
    recorded_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        dhm.id,
        dhm.cpu_usage,
        dhm.memory_usage,
        dhm.disk_usage,
        dhm.network_latency_ms,
        dhm.connection_quality,
        dhm.overall_status,
        dhm.recorded_at
    FROM device_health_metrics dhm
    WHERE dhm.device_id = p_device_id
      AND dhm.recorded_at >= NOW() - (p_hours || ' hours')::INTERVAL
    ORDER BY dhm.recorded_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Function: Check device health alerts
CREATE OR REPLACE FUNCTION check_device_health_alerts(p_device_id INTEGER)
RETURNS TABLE (
    alert_type VARCHAR(50),
    alert_level VARCHAR(20),
    alert_message TEXT,
    metric_value DECIMAL(10,2),
    threshold_value DECIMAL(10,2),
    recorded_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    WITH latest_metrics AS (
        SELECT * FROM get_latest_device_health(p_device_id)
    )
    SELECT
        'cpu_high'::VARCHAR(50) as alert_type,
        CASE
            WHEN lm.cpu_usage >= 90 THEN 'critical'::VARCHAR(20)
            WHEN lm.cpu_usage >= 80 THEN 'warning'::VARCHAR(20)
            ELSE 'info'::VARCHAR(20)
        END as alert_level,
        'High CPU usage detected'::TEXT as alert_message,
        lm.cpu_usage as metric_value,
        80.00 as threshold_value,
        lm.recorded_at
    FROM latest_metrics lm
    WHERE lm.cpu_usage >= 80

    UNION ALL

    SELECT
        'memory_high'::VARCHAR(50),
        CASE
            WHEN lm.memory_usage >= 90 THEN 'critical'::VARCHAR(20)
            WHEN lm.memory_usage >= 80 THEN 'warning'::VARCHAR(20)
            ELSE 'info'::VARCHAR(20)
        END,
        'High memory usage detected'::TEXT,
        lm.memory_usage,
        80.00,
        lm.recorded_at
    FROM latest_metrics lm
    WHERE lm.memory_usage >= 80

    UNION ALL

    SELECT
        'disk_high'::VARCHAR(50),
        CASE
            WHEN lm.disk_usage >= 90 THEN 'critical'::VARCHAR(20)
            WHEN lm.disk_usage >= 80 THEN 'warning'::VARCHAR(20)
            ELSE 'info'::VARCHAR(20)
        END,
        'High disk usage detected'::TEXT,
        lm.disk_usage,
        80.00,
        lm.recorded_at
    FROM latest_metrics lm
    WHERE lm.disk_usage >= 80

    UNION ALL

    SELECT
        'network_slow'::VARCHAR(50),
        CASE
            WHEN lm.network_latency_ms >= 500 THEN 'critical'::VARCHAR(20)
            WHEN lm.network_latency_ms >= 200 THEN 'warning'::VARCHAR(20)
            ELSE 'info'::VARCHAR(20)
        END,
        'High network latency detected'::TEXT,
        lm.network_latency_ms::DECIMAL(10,2),
        200.00,
        lm.recorded_at
    FROM latest_metrics lm
    WHERE lm.network_latency_ms >= 200;
END;
$$ LANGUAGE plpgsql;

-- Function: Get organization health summary
CREATE OR REPLACE FUNCTION get_organization_health_summary(p_organization_id INTEGER)
RETURNS TABLE (
    total_devices INTEGER,
    healthy_devices INTEGER,
    warning_devices INTEGER,
    critical_devices INTEGER,
    offline_devices INTEGER,
    avg_cpu_usage DECIMAL(5,2),
    avg_memory_usage DECIMAL(5,2),
    avg_disk_usage DECIMAL(5,2),
    devices_with_errors INTEGER
) AS $$
BEGIN
    RETURN QUERY
    WITH latest_health AS (
        SELECT DISTINCT ON (dhm.device_id)
            dhm.device_id,
            dhm.overall_status,
            dhm.cpu_usage,
            dhm.memory_usage,
            dhm.disk_usage,
            dhm.content_errors_count
        FROM device_health_metrics dhm
        WHERE dhm.organization_id = p_organization_id
        ORDER BY dhm.device_id, dhm.recorded_at DESC
    )
    SELECT
        COUNT(*)::INTEGER as total_devices,
        COUNT(*) FILTER (WHERE overall_status = 'healthy')::INTEGER as healthy_devices,
        COUNT(*) FILTER (WHERE overall_status = 'warning')::INTEGER as warning_devices,
        COUNT(*) FILTER (WHERE overall_status = 'critical')::INTEGER as critical_devices,
        COUNT(*) FILTER (WHERE overall_status = 'offline')::INTEGER as offline_devices,
        ROUND(AVG(cpu_usage), 2) as avg_cpu_usage,
        ROUND(AVG(memory_usage), 2) as avg_memory_usage,
        ROUND(AVG(disk_usage), 2) as avg_disk_usage,
        COUNT(*) FILTER (WHERE content_errors_count > 0)::INTEGER as devices_with_errors
    FROM latest_health;
END;
$$ LANGUAGE plpgsql;

-- Function: Clean up old health metrics (retention policy)
CREATE OR REPLACE FUNCTION cleanup_old_health_metrics(p_retention_days INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    DELETE FROM device_health_metrics
    WHERE recorded_at < NOW() - (p_retention_days || ' days')::INTERVAL;

    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    RETURN v_deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMMENTS
-- ============================================================================
COMMENT ON TABLE device_health_metrics IS 'Health metrics from devices for monitoring and alerting';
COMMENT ON COLUMN device_health_metrics.cpu_usage IS 'CPU usage percentage (0-100)';
COMMENT ON COLUMN device_health_metrics.memory_usage IS 'Memory usage percentage (0-100)';
COMMENT ON COLUMN device_health_metrics.disk_usage IS 'Disk usage percentage (0-100)';
COMMENT ON COLUMN device_health_metrics.network_latency_ms IS 'Network latency to backend in milliseconds';
COMMENT ON COLUMN device_health_metrics.overall_status IS 'Overall health status: healthy, warning, critical, offline';
COMMENT ON COLUMN device_health_metrics.alert_triggered IS 'Whether an alert was triggered for this metric';
COMMENT ON COLUMN device_health_metrics.player_uptime_hours IS 'Hours since player application started';
COMMENT ON COLUMN device_health_metrics.content_errors_count IS 'Number of content loading errors since last restart';
