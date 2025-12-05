-- Migration: 085
-- Description: Add performance metrics columns to device_health_metrics table
-- Purpose: Track FPS, long tasks, CPU pressure, TTFB, page load time (Phase 4)
-- Date: 2025-12-05

BEGIN;

-- Add performance metrics columns to device_health_metrics table
ALTER TABLE device_health_metrics
ADD COLUMN IF NOT EXISTS fps_current INTEGER,
ADD COLUMN IF NOT EXISTS long_tasks_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS cpu_pressure VARCHAR(20),
ADD COLUMN IF NOT EXISTS ttfb_ms INTEGER,
ADD COLUMN IF NOT EXISTS page_load_time_ms INTEGER;

-- Add comments for documentation
COMMENT ON COLUMN device_health_metrics.fps_current IS 'Current frames per second (measured via requestAnimationFrame)';
COMMENT ON COLUMN device_health_metrics.long_tasks_count IS 'Number of long tasks (>50ms) detected via PerformanceObserver';
COMMENT ON COLUMN device_health_metrics.cpu_pressure IS 'CPU pressure state from Compute Pressure API: nominal/fair/serious/critical';
COMMENT ON COLUMN device_health_metrics.ttfb_ms IS 'Time to First Byte in milliseconds (Navigation Timing API)';
COMMENT ON COLUMN device_health_metrics.page_load_time_ms IS 'Total page load time in milliseconds';

-- Add check constraint for cpu_pressure values
ALTER TABLE device_health_metrics
ADD CONSTRAINT chk_cpu_pressure_values
CHECK (cpu_pressure IS NULL OR cpu_pressure IN ('nominal', 'fair', 'serious', 'critical'));

COMMIT;
