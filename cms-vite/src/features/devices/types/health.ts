/**
 * Device Health Types
 * Based on backend DTOs from services/device/dtos.py
 */

export type HealthStatus = 'healthy' | 'warning' | 'critical';
export type AlertLevel = 'info' | 'warning' | 'critical';
export type ConnectionQuality = 'excellent' | 'good' | 'fair' | 'poor';

export interface DeviceHealthMetrics {
  id: number;
  device_id: number;
  organization_id: number;

  // System metrics
  cpu_usage?: number;
  memory_usage?: number;
  memory_total_mb?: number;
  memory_used_mb?: number;
  disk_usage?: number;
  disk_total_gb?: number;
  disk_used_gb?: number;

  // Network metrics
  network_latency_ms?: number;
  network_download_mbps?: number;
  network_upload_mbps?: number;
  connection_quality?: ConnectionQuality;

  // Display metrics
  display_resolution?: string;
  display_refresh_rate?: number;
  gpu_usage?: number;

  // Player metrics
  player_version?: string;
  player_uptime_hours?: number;
  content_errors_count: number;
  last_error_message?: string;
  last_error_at?: string;

  // Health status
  overall_status: HealthStatus;
  alert_triggered: boolean;
  alert_message?: string;

  // Metadata
  metadata: Record<string, any>;
  recorded_at: string;
}

export interface HealthAlert {
  alert_type: string;
  alert_level: AlertLevel;
  alert_message: string;
  metric_value: number;
  threshold_value: number;
  recorded_at: string;
}

export interface DeviceHealthWithAlerts {
  health?: DeviceHealthMetrics;
  alerts: HealthAlert[];
}

export interface HealthHistoryResponse {
  history: DeviceHealthMetrics[];
  count: number;
}

export interface OrganizationHealthSummary {
  total_devices: number;
  healthy_devices: number;
  warning_devices: number;
  critical_devices: number;
  offline_devices: number;
  avg_cpu_usage?: number;
  avg_memory_usage?: number;
  avg_disk_usage?: number;
  devices_with_errors: number;
}

export interface RecordHealthMetricsRequest {
  // System metrics
  cpu_usage?: number;
  memory_usage?: number;
  memory_total_mb?: number;
  memory_used_mb?: number;
  disk_usage?: number;
  disk_total_gb?: number;
  disk_used_gb?: number;

  // Network metrics
  network_latency_ms?: number;
  network_download_mbps?: number;
  network_upload_mbps?: number;

  // Display metrics
  display_resolution?: string;
  display_refresh_rate?: number;
  gpu_usage?: number;

  // Player metrics
  player_version?: string;
  player_uptime_hours?: number;
  content_errors_count?: number;
  last_error_message?: string;

  // Additional metadata
  metadata?: Record<string, any>;
}
