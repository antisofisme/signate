-- ============================================================================
-- Migration 022: Device Health Metrics - PHASE 4
-- ============================================================================
-- Purpose: Track device health metrics over time for monitoring
-- Impact: New table for time-series health data
-- Risk: Low - Only adds new table, time-series data can grow large
-- Phase: 4 - Device Management
-- Created: 2025-11-10
-- ============================================================================

BEGIN;

-- ============================================================================
-- Step 1: Device Health Metrics Table (Time-Series)
-- ============================================================================

CREATE TABLE IF NOT EXISTS device_health_metrics (
  id SERIAL PRIMARY KEY,
  device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
  organization_id INTEGER NOT NULL REFERENCES organizations(id),

  -- System metrics
  cpu_usage DECIMAL(5,2),      -- Percentage (0-100)
  memory_usage DECIMAL(5,2),   -- Percentage (0-100)
  disk_usage DECIMAL(5,2),     -- Percentage (0-100)
  temperature DECIMAL(5,2),    -- Celsius

  -- Network metrics
  network_status VARCHAR(20),  -- 'online', 'offline', 'unstable'
  bandwidth_up INTEGER,        -- Kbps
  bandwidth_down INTEGER,      -- Kbps
  latency INTEGER,             -- ms

  -- Display metrics
  display_status VARCHAR(20),  -- 'on', 'off', 'standby'
  resolution VARCHAR(20),      -- '1920x1080'
  refresh_rate INTEGER,        -- Hz

  -- Browser metrics
  browser_version VARCHAR(100),
  user_agent TEXT,

  -- Timestamps
  recorded_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- Step 2: Indexes for Performance (Time-Series Optimized)
-- ============================================================================

-- Primary query pattern: get latest metrics for a device
CREATE INDEX idx_device_health_device_time ON device_health_metrics(device_id, recorded_at DESC);

-- Organization-wide queries
CREATE INDEX idx_device_health_org ON device_health_metrics(organization_id);

-- Time-based queries
CREATE INDEX idx_device_health_time ON device_health_metrics(recorded_at DESC);

-- Query pattern: find devices with high CPU/memory usage
CREATE INDEX idx_device_health_cpu ON device_health_metrics(cpu_usage DESC) WHERE cpu_usage > 80;
CREATE INDEX idx_device_health_memory ON device_health_metrics(memory_usage DESC) WHERE memory_usage > 80;

-- ============================================================================
-- Step 3: Helper Functions
-- ============================================================================

-- Function to get latest metrics for a device
CREATE OR REPLACE FUNCTION get_latest_device_health(p_device_id INTEGER)
RETURNS TABLE (
  cpu_usage DECIMAL,
  memory_usage DECIMAL,
  disk_usage DECIMAL,
  temperature DECIMAL,
  network_status VARCHAR,
  latency INTEGER,
  display_status VARCHAR,
  recorded_at TIMESTAMP
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    dhm.cpu_usage,
    dhm.memory_usage,
    dhm.disk_usage,
    dhm.temperature,
    dhm.network_status,
    dhm.latency,
    dhm.display_status,
    dhm.recorded_at
  FROM device_health_metrics dhm
  WHERE dhm.device_id = p_device_id
  ORDER BY dhm.recorded_at DESC
  LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Function to get metrics history for a device
CREATE OR REPLACE FUNCTION get_device_health_history(
  p_device_id INTEGER,
  p_hours INTEGER DEFAULT 24
)
RETURNS TABLE (
  cpu_usage DECIMAL,
  memory_usage DECIMAL,
  disk_usage DECIMAL,
  temperature DECIMAL,
  latency INTEGER,
  recorded_at TIMESTAMP
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    dhm.cpu_usage,
    dhm.memory_usage,
    dhm.disk_usage,
    dhm.temperature,
    dhm.latency,
    dhm.recorded_at
  FROM device_health_metrics dhm
  WHERE dhm.device_id = p_device_id
    AND dhm.recorded_at >= NOW() - (p_hours || ' hours')::INTERVAL
  ORDER BY dhm.recorded_at ASC;
END;
$$ LANGUAGE plpgsql;

-- Function to get average metrics for time period
CREATE OR REPLACE FUNCTION get_device_health_average(
  p_device_id INTEGER,
  p_hours INTEGER DEFAULT 24
)
RETURNS TABLE (
  avg_cpu DECIMAL,
  avg_memory DECIMAL,
  avg_disk DECIMAL,
  avg_temp DECIMAL,
  avg_latency DECIMAL
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    ROUND(AVG(dhm.cpu_usage), 2),
    ROUND(AVG(dhm.memory_usage), 2),
    ROUND(AVG(dhm.disk_usage), 2),
    ROUND(AVG(dhm.temperature), 2),
    ROUND(AVG(dhm.latency), 2)
  FROM device_health_metrics dhm
  WHERE dhm.device_id = p_device_id
    AND dhm.recorded_at >= NOW() - (p_hours || ' hours')::INTERVAL;
END;
$$ LANGUAGE plpgsql;

-- Function to check for health alerts
CREATE OR REPLACE FUNCTION check_device_health_alerts(p_device_id INTEGER)
RETURNS TABLE (
  alert_type VARCHAR,
  severity VARCHAR,
  message TEXT,
  value DECIMAL
) AS $$
DECLARE
  v_latest RECORD;
BEGIN
  -- Get latest metrics
  SELECT * INTO v_latest
  FROM get_latest_device_health(p_device_id);

  -- CPU alert
  IF v_latest.cpu_usage > 90 THEN
    RETURN QUERY SELECT 'cpu'::VARCHAR, 'critical'::VARCHAR,
      'CPU usage critically high'::TEXT, v_latest.cpu_usage;
  ELSIF v_latest.cpu_usage > 80 THEN
    RETURN QUERY SELECT 'cpu'::VARCHAR, 'warning'::VARCHAR,
      'CPU usage high'::TEXT, v_latest.cpu_usage;
  END IF;

  -- Memory alert
  IF v_latest.memory_usage > 90 THEN
    RETURN QUERY SELECT 'memory'::VARCHAR, 'critical'::VARCHAR,
      'Memory usage critically high'::TEXT, v_latest.memory_usage;
  ELSIF v_latest.memory_usage > 80 THEN
    RETURN QUERY SELECT 'memory'::VARCHAR, 'warning'::VARCHAR,
      'Memory usage high'::TEXT, v_latest.memory_usage;
  END IF;

  -- Disk alert
  IF v_latest.disk_usage > 95 THEN
    RETURN QUERY SELECT 'disk'::VARCHAR, 'critical'::VARCHAR,
      'Disk space critically low'::TEXT, v_latest.disk_usage;
  ELSIF v_latest.disk_usage > 85 THEN
    RETURN QUERY SELECT 'disk'::VARCHAR, 'warning'::VARCHAR,
      'Disk space low'::TEXT, v_latest.disk_usage;
  END IF;

  -- Temperature alert
  IF v_latest.temperature > 85 THEN
    RETURN QUERY SELECT 'temperature'::VARCHAR, 'critical'::VARCHAR,
      'Temperature critically high'::TEXT, v_latest.temperature;
  ELSIF v_latest.temperature > 75 THEN
    RETURN QUERY SELECT 'temperature'::VARCHAR, 'warning'::VARCHAR,
      'Temperature high'::TEXT, v_latest.temperature;
  END IF;

  -- Network alert
  IF v_latest.network_status = 'offline' THEN
    RETURN QUERY SELECT 'network'::VARCHAR, 'critical'::VARCHAR,
      'Device offline'::TEXT, 0::DECIMAL;
  ELSIF v_latest.network_status = 'unstable' THEN
    RETURN QUERY SELECT 'network'::VARCHAR, 'warning'::VARCHAR,
      'Network connection unstable'::TEXT, 0::DECIMAL;
  END IF;

  -- Latency alert
  IF v_latest.latency > 1000 THEN
    RETURN QUERY SELECT 'latency'::VARCHAR, 'warning'::VARCHAR,
      'High network latency'::TEXT, v_latest.latency::DECIMAL;
  END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up old health data (keep last 30 days)
CREATE OR REPLACE FUNCTION cleanup_old_health_metrics()
RETURNS INTEGER AS $$
DECLARE
  v_deleted_count INTEGER;
BEGIN
  DELETE FROM device_health_metrics
  WHERE recorded_at < NOW() - INTERVAL '30 days';

  GET DIAGNOSTICS v_deleted_count = ROW_COUNT;

  RETURN v_deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Step 4: Materialized View for Organization Health Summary
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_organization_health_summary AS
SELECT
  d.organization_id,
  COUNT(DISTINCT d.id) AS total_devices,
  COUNT(DISTINCT CASE WHEN dhm.network_status = 'online' THEN d.id END) AS online_devices,
  COUNT(DISTINCT CASE WHEN dhm.cpu_usage > 80 THEN d.id END) AS high_cpu_devices,
  COUNT(DISTINCT CASE WHEN dhm.memory_usage > 80 THEN d.id END) AS high_memory_devices,
  COUNT(DISTINCT CASE WHEN dhm.temperature > 75 THEN d.id END) AS high_temp_devices,
  ROUND(AVG(dhm.cpu_usage), 2) AS avg_cpu_usage,
  ROUND(AVG(dhm.memory_usage), 2) AS avg_memory_usage,
  ROUND(AVG(dhm.latency), 2) AS avg_latency,
  MAX(dhm.recorded_at) AS last_updated
FROM devices d
LEFT JOIN LATERAL (
  SELECT *
  FROM device_health_metrics
  WHERE device_id = d.id
  ORDER BY recorded_at DESC
  LIMIT 1
) dhm ON TRUE
GROUP BY d.organization_id;

-- Create index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_org_health_org ON mv_organization_health_summary(organization_id);

-- Refresh function
CREATE OR REPLACE FUNCTION refresh_organization_health_summary()
RETURNS VOID AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY mv_organization_health_summary;
END;
$$ LANGUAGE plpgsql;

COMMIT;

-- ============================================================================
-- ROLLBACK PROCEDURE
-- ============================================================================
-- To rollback this migration:
-- BEGIN;
-- DROP MATERIALIZED VIEW IF EXISTS mv_organization_health_summary CASCADE;
-- DROP TABLE IF EXISTS device_health_metrics CASCADE;
-- DROP FUNCTION IF EXISTS get_latest_device_health(INTEGER);
-- DROP FUNCTION IF EXISTS get_device_health_history(INTEGER, INTEGER);
-- DROP FUNCTION IF EXISTS get_device_health_average(INTEGER, INTEGER);
-- DROP FUNCTION IF EXISTS check_device_health_alerts(INTEGER);
-- DROP FUNCTION IF EXISTS cleanup_old_health_metrics();
-- DROP FUNCTION IF EXISTS refresh_organization_health_summary();
-- COMMIT;
-- ============================================================================
