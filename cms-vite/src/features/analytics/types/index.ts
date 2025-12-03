/**
 * Analytics Feature Types
 * Type definitions for analytics and reporting
 */

export interface PlaybackStats {
  total_plays: number
  completed_plays: number
  unique_content: number
  unique_devices: number
  total_watch_time_seconds: number
  total_watch_time_hours: number
  completion_rate: number
  period_start: string
  period_end: string
}

export interface ContentPerformance {
  content_id: number
  title: string
  content_type: string
  total_plays: number
  completed_plays: number
  unique_devices: number
  avg_duration_seconds?: number
  last_played_at?: string
  completion_rate?: number
  engagement_score?: number
}

export interface DeviceEngagement {
  device_id: number
  device_name: string
  total_plays: number
  unique_content: number
  total_watch_time_seconds: number
  last_playback_at?: string
  watch_time_hours?: number
  avg_plays_per_content?: number
  is_active?: boolean
}

export interface TimelineDataPoint {
  date: string
  plays: number
  completed: number
  devices: number
  watch_time: number
}

export interface AnalyticsDashboard {
  stats: PlaybackStats
  top_content: ContentPerformance[]
  top_devices: DeviceEngagement[]
}

export interface AnalyticsQueryParams {
  start_date?: string
  end_date?: string
  limit?: number
}

export interface TimelineQueryParams extends AnalyticsQueryParams {
  interval?: 'day' | 'week' | 'month'
}

export interface PlaybackLogRequest {
  device_id: number
  organization_id: number
  playlist_id?: number
  expected_duration?: number
  device_info?: Record<string, any>
  playback_quality?: string
}

export interface PlaybackEndRequest {
  duration_seconds: number
  completed?: boolean
}

export interface PlaybackLogResponse {
  id: number
  content_id: number
  device_id: number
  playlist_id?: number
  organization_id: number
  started_at: string
  ended_at?: string
  duration_seconds?: number
  expected_duration?: number
  completed: boolean
  device_info?: Record<string, any>
  playback_quality?: string
  error_count: number
  error_details?: Record<string, any>
  created_at: string
}

// ============================================================================
// MENU ANALYTICS TYPES (REAL DATA from menu_views table)
// ============================================================================

export interface MenuViewTrendPoint {
  date: string
  views: number
  contact_clicks: number
  mobile: number
  tablet: number
  desktop: number
  unknown: number
}

export interface TopMenuAnalytics {
  menu_id: number
  menu_name: string
  menu_type: string
  total_views: number
  contact_clicks: number
  mobile_views: number
  tablet_views: number
  desktop_views: number
}

export interface PopularHour {
  hour: number
  views: number
  percentage: number
}

export interface MenuAnalyticsTrend {
  period_start: string
  period_end: string
  total_views: number
  total_contact_clicks: number
  views_by_device: {
    mobile: number
    tablet: number
    desktop: number
    unknown: number
  }
  daily_trend: MenuViewTrendPoint[]
  top_menus: TopMenuAnalytics[]
  popular_hours: PopularHour[]
}

// ============================================================================
// DEVICE HEALTH ANALYTICS TYPES (REAL DATA from device_health_metrics table)
// ============================================================================

export interface DeviceHealthTrendPoint {
  date: string
  avg_cpu_usage: number
  avg_memory_usage: number
  avg_disk_usage: number
  avg_network_latency_ms: number | null
  devices_reporting: number
}

export interface DeviceHealthSummary {
  device_id: number
  device_name: string
  latest_cpu_usage: number | null
  latest_memory_usage: number | null
  latest_disk_usage: number | null
  health_score: number
  status: 'healthy' | 'warning' | 'critical'
  last_reported_at: string | null
}

export interface DeviceHealthTrend {
  period_start: string
  period_end: string
  fleet_health_score: number
  devices_healthy: number
  devices_warning: number
  devices_critical: number
  avg_cpu_usage: number
  avg_memory_usage: number
  avg_disk_usage: number
  daily_trend: DeviceHealthTrendPoint[]
  device_summaries: DeviceHealthSummary[]
}
