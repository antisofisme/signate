// ============================================================================
// Analytics Type Definitions
// ============================================================================

/**
 * Date range for analytics queries
 */
export interface DateRange {
  /** Start date (ISO string or Date) */
  start: string | Date
  /** End date (ISO string or Date) */
  end: string | Date
}

/**
 * Overview metrics for dashboard
 */
export interface AnalyticsOverview {
  /** Total content views */
  total_views: number
  /** Unique viewer count */
  unique_viewers: number
  /** Number of active devices */
  active_devices: number
  /** Total number of devices */
  total_devices: number
  /** Average view duration in seconds */
  avg_view_duration: number
  /** Total content items */
  total_content: number
  /** Error count in period */
  error_count: number
  /** System uptime percentage */
  uptime_percentage: number
}

/**
 * Device status breakdown
 */
export interface DeviceStatusData {
  /** Number of online devices */
  online: number
  /** Number of offline devices */
  offline: number
  /** Number of devices with errors */
  error: number
  /** Number of pending devices */
  pending: number
}

/**
 * Content performance metrics
 */
export interface ContentPerformance {
  /** Content ID */
  id: string
  /** Content title */
  title: string
  /** Content type (image, video, web, etc.) */
  type: string
  /** Total views */
  views: number
  /** Unique viewers */
  unique_viewers: number
  /** Average view duration */
  avg_duration: number
  /** Thumbnail URL */
  thumbnail?: string
  /** Last played timestamp */
  last_played?: string
}

/**
 * System health metrics
 */
export interface SystemHealth {
  /** CPU usage percentage */
  cpu_usage: number
  /** Memory usage percentage */
  memory_usage: number
  /** Disk usage percentage */
  disk_usage: number
  /** Network bandwidth in MB/s */
  bandwidth: number
  /** Database connection count */
  db_connections: number
  /** API response time in ms */
  api_response_time: number
}

/**
 * Time series data point
 */
export interface TimeSeriesDataPoint {
  /** Date/time label */
  date: string
  /** Number of views */
  views: number
  /** Number of unique viewers */
  unique_viewers: number
  /** Additional metric values */
  [key: string]: string | number
}

/**
 * Error rate data
 */
export interface ErrorRateData {
  /** Hour timestamp */
  hour: string
  /** Error count */
  errors: number
  /** Total requests */
  requests: number
  /** Error rate percentage */
  error_rate: number
}

/**
 * Heatmap data for viewing patterns
 */
export interface HeatmapData {
  /** Hour of day (0-23) */
  hour: number
  /** Day of week (0-6) */
  day: number
  /** View count */
  value: number
}

/**
 * Device analytics data
 */
export interface DeviceAnalytics {
  /** Device ID */
  device_id: string
  /** Device name */
  device_name: string
  /** Location */
  location?: string
  /** Total views */
  views: number
  /** Uptime percentage */
  uptime: number
  /** Last seen timestamp */
  last_seen: string
  /** Status */
  status: 'online' | 'offline' | 'error'
}

/**
 * Complete dashboard data
 */
export interface DashboardData {
  /** Overview metrics */
  overview: AnalyticsOverview
  /** Device status breakdown */
  devices: DeviceStatusData
  /** Top performing content */
  topContent: ContentPerformance[]
  /** System health metrics */
  systemHealth: SystemHealth
  /** Time series trends */
  trends: TimeSeriesDataPoint[]
  /** Error rate data */
  errors: ErrorRateData[]
  /** Viewing pattern heatmap */
  heatmap: HeatmapData[]
  /** Device analytics */
  deviceAnalytics: DeviceAnalytics[]
  /** Last updated timestamp */
  last_updated: string
}

/**
 * Report generation request
 */
export interface ReportGenerateRequest {
  /** Report format */
  format: 'pdf' | 'excel' | 'csv'
  /** Date range */
  date_range: DateRange
  /** Report type */
  report_type: 'daily' | 'weekly' | 'monthly' | 'custom'
  /** Sections to include */
  sections: ReportSection[]
  /** Filters */
  filters?: ReportFilters
}

/**
 * Report section
 */
export type ReportSection =
  | 'overview'
  | 'content'
  | 'devices'
  | 'system'
  | 'errors'
  | 'trends'

/**
 * Report filters
 */
export interface ReportFilters {
  /** Filter by device IDs */
  device_ids?: string[]
  /** Filter by content IDs */
  content_ids?: string[]
  /** Filter by tag IDs */
  tag_ids?: string[]
  /** Filter by location */
  location?: string
}

/**
 * Report metadata
 */
export interface Report {
  /** Report ID */
  id: string
  /** Report title */
  title: string
  /** Report format */
  format: 'pdf' | 'excel' | 'csv'
  /** Generation status */
  status: 'pending' | 'processing' | 'completed' | 'failed'
  /** File size in bytes */
  file_size?: number
  /** Download URL */
  download_url?: string
  /** Created at timestamp */
  created_at: string
  /** Completed at timestamp */
  completed_at?: string
  /** Error message if failed */
  error_message?: string
}

/**
 * Chart data type for Recharts
 */
export interface ChartData {
  /** X-axis label */
  name: string
  /** Y-axis value(s) */
  [key: string]: string | number
}

/**
 * Analytics query parameters
 */
export interface AnalyticsQueryParams {
  /** Date range */
  start_date?: string
  end_date?: string
  /** Grouping interval */
  interval?: 'hour' | 'day' | 'week' | 'month'
  /** Filter by device ID */
  device_id?: string
  /** Filter by content ID */
  content_id?: string
  /** Filter by tag ID */
  tag_id?: string
  /** Limit for top results */
  limit?: number
}

/**
 * Real-time analytics event
 */
export interface AnalyticsEvent {
  /** Event type */
  type: 'view' | 'error' | 'device_status' | 'system_health'
  /** Event timestamp */
  timestamp: string
  /** Event data */
  data: Record<string, unknown>
}

/**
 * Export options
 */
export interface ExportOptions {
  /** Export format */
  format: 'pdf' | 'excel' | 'csv'
  /** Include charts */
  include_charts?: boolean
  /** Page orientation for PDF */
  orientation?: 'portrait' | 'landscape'
  /** File name */
  filename?: string
}
