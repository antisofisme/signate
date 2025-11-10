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
