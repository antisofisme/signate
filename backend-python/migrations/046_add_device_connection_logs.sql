-- Migration: 046
-- Description: Add device_connection_logs table for player connection activity monitoring
-- Date: 2025-01-15
-- Author: System
-- Purpose: Store network/server connection logs and speed test results from player devices

BEGIN;

-- Create device_connection_logs table
CREATE TABLE device_connection_logs (
  -- Primary key
  id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,

  -- Foreign key to devices
  device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,

  -- Log data
  logged_at TIMESTAMP WITH TIME ZONE NOT NULL,
  event_type VARCHAR(50) NOT NULL CHECK (event_type IN ('network', 'server', 'speed_test')),
  status VARCHAR(20) NOT NULL,

  -- Optional metrics
  latency_ms INTEGER CHECK (latency_ms >= 0),
  error_message TEXT,
  download_speed_mbps NUMERIC(10, 2) CHECK (download_speed_mbps >= 0),
  upload_speed_mbps NUMERIC(10, 2) CHECK (upload_speed_mbps >= 0),
  metadata JSONB,

  -- Audit trail
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Create indexes for fast queries
CREATE INDEX idx_device_logs_device ON device_connection_logs(device_id);
CREATE INDEX idx_device_logs_time ON device_connection_logs(logged_at DESC);
CREATE INDEX idx_device_logs_type ON device_connection_logs(event_type);
CREATE INDEX idx_device_logs_device_time ON device_connection_logs(device_id, logged_at DESC);

-- Add table comment
COMMENT ON TABLE device_connection_logs IS 'Connection activity logs from player devices - tracks network status, server connectivity, and speed test results';

-- Add column comments
COMMENT ON COLUMN device_connection_logs.device_id IS 'Reference to the device that generated this log';
COMMENT ON COLUMN device_connection_logs.logged_at IS 'Timestamp when the event occurred on the player device';
COMMENT ON COLUMN device_connection_logs.event_type IS 'Type of event: network (browser online/offline), server (API connectivity), speed_test (network performance)';
COMMENT ON COLUMN device_connection_logs.status IS 'Event status: online, offline, connected, disconnected, tested';
COMMENT ON COLUMN device_connection_logs.latency_ms IS 'Network latency in milliseconds (for server and speed_test events)';
COMMENT ON COLUMN device_connection_logs.error_message IS 'Error details if the event indicates a failure';
COMMENT ON COLUMN device_connection_logs.download_speed_mbps IS 'Download speed in Mbps (for speed_test events only)';
COMMENT ON COLUMN device_connection_logs.upload_speed_mbps IS 'Upload speed in Mbps (for speed_test events only)';
COMMENT ON COLUMN device_connection_logs.metadata IS 'Additional event metadata in JSON format';
COMMENT ON COLUMN device_connection_logs.created_at IS 'Timestamp when this record was inserted into the database';

COMMIT;
