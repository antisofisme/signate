/**
 * Analytics Domain Types
 * Generated from backend-python/services/analytics/dtos.py
 */

// ============================================================================
// Request Types
// ============================================================================

export interface AnalyticsQueryRequest {
  start_date?: string;
  end_date?: string;
  limit?: number;
}

export interface TimelineQueryRequest {
  start_date?: string;
  end_date?: string;
  interval?: string;
}

export interface PlaybackLogRequest {
  content_id: number;
  device_id: number;
  playlist_id?: number;
  organization_id: number;
  expected_duration?: number;
  device_info?: Record<string, any>;
  playback_quality?: string;
}

export interface PlaybackEndRequest {
  duration_seconds: number;
  completed?: boolean;
  error_count?: number;
  error_details?: Record<string, any>;
}

// ============================================================================
// Response Types
// ============================================================================

export interface ContentPerformance {
  content_id: number;
  title: string;
  content_type: string;
  total_plays: number;
  completed_plays: number;
  avg_duration_seconds?: number;
  last_played_at?: string;
  unique_devices: number;
  completion_rate?: number;
}

export interface DeviceEngagement {
  device_id: number;
  device_name: string;
  total_plays: number;
  unique_content: number;
  last_playback_at?: string;
  total_watch_time_seconds: number;
  total_watch_time_hours: number;
}

export interface PlaybackStats {
  total_plays: number;
  completed_plays: number;
  unique_content: number;
  unique_devices: number;
  total_watch_time_seconds: number;
  total_watch_time_hours: number;
  completion_rate: number;
  period_start: string;
  period_end: string;
}

export interface TimelineDataPoint {
  period: string;
  total_plays: number;
  completed_plays: number;
  unique_content: number;
  unique_devices: number;
  total_watch_time_seconds: number;
}

export interface PlaybackTimeline {
  data: TimelineDataPoint[];
  interval: string;
  start_date: string;
  end_date: string;
}

export interface PlaybackLog {
  id: number;
  content_id: number;
  device_id: number;
  playlist_id?: number;
  organization_id: number;
  started_at: string;
  ended_at?: string;
  duration_seconds?: number;
  expected_duration?: number;
  completed: boolean;
  playback_quality?: string;
  error_count: number;
  created_at: string;
}

export interface AnalyticsDashboard {
  stats: PlaybackStats;
  top_content: ContentPerformance[];
  top_devices: DeviceEngagement[];
}
