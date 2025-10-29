/**
 * Device Type Definitions
 *
 * Type definitions for device entities, API responses, and related data structures.
 */

/**
 * Device type enumeration
 */
export type DeviceType = 'tv' | 'monitor'

/**
 * Device status enumeration
 */
export type DeviceStatus = 'pending' | 'active' | 'inactive'

/**
 * Device filter types
 */
export type DeviceFilter = 'all' | 'pending' | 'active' | 'inactive' | 'browser' | 'app'

/**
 * Sort options for devices
 */
export type DeviceSortBy = 'newest' | 'oldest' | 'name_asc' | 'name_desc'

/**
 * Device entity from API
 */
export interface Device {
  /** Unique device identifier */
  id: number
  /** Device display name */
  device_name: string
  /** Device type (TV app or browser monitor) */
  device_type: DeviceType
  /** Current device status */
  status: DeviceStatus
  /** IP address of the device */
  ip_address: string | null
  /** Pairing/activation code for device registration */
  pairing_code: string | null
  /** Last heartbeat timestamp (ISO 8601) */
  last_seen: string | null
  /** Device creation timestamp (ISO 8601) */
  created_at: string
  /** Device last update timestamp (ISO 8601) */
  updated_at: string
  /** ID of currently assigned content */
  current_content_id: number | null
  /** Title of currently assigned content */
  current_content_title: string | null
  /** ID of currently assigned playlist */
  current_playlist_id: number | null
  /** Name of currently assigned playlist */
  current_playlist_name: string | null
  /** Platform information */
  platform?: string | null
  /** Additional metadata */
  metadata?: Record<string, unknown>
}

/**
 * Device API list response
 */
export interface DevicesListResponse {
  /** Array of devices */
  devices: Device[]
  /** Total device count */
  total: number
}

/**
 * Device registration data for TV
 */
export interface TVRegistrationData {
  /** Device display name */
  device_name: string
  /** Device type (must be 'tv') */
  device_type: 'tv'
  /** Optional platform information */
  platform?: string
}

/**
 * Device update data
 */
export interface DeviceUpdateData {
  /** New device name */
  device_name?: string
  /** New status */
  status?: DeviceStatus
  /** New metadata */
  metadata?: Record<string, unknown>
}

/**
 * Content source information in preview
 */
export interface ContentSource {
  /** Source type (direct assignment, playlist, etc.) */
  type: 'direct' | 'playlist' | 'tag'
  /** Source ID */
  id: number
  /** Source name */
  name: string
  /** Priority level */
  priority?: number
}

/**
 * Content item in preview sequence
 */
export interface PreviewContentItem {
  /** Content ID */
  id: number
  /** Content title */
  title: string
  /** Content type */
  type: 'image' | 'video'
  /** File URL */
  url: string
  /** Display duration in seconds */
  duration: number
  /** Content source information */
  source: ContentSource
  /** Order in sequence */
  order: number
}

/**
 * Preview warning/conflict information
 */
export interface PreviewWarning {
  /** Warning type */
  type: 'conflict' | 'missing' | 'duplicate'
  /** Warning message */
  message: string
  /** Related content IDs */
  content_ids?: number[]
}

/**
 * Device preview data from API
 */
export interface DevicePreviewData {
  /** Device ID */
  device_id: number
  /** Device name */
  device_name: string
  /** Content sequence to be played */
  content_sequence: PreviewContentItem[]
  /** Total duration in seconds */
  total_duration_seconds: number
  /** Estimated loops per hour */
  loops_per_hour: number
  /** Warnings or conflicts */
  warnings?: PreviewWarning[]
}

/**
 * Device log entry
 */
export interface DeviceLog {
  /** Log ID */
  id: number
  /** Device ID */
  device_id: number
  /** Log level */
  level: 'info' | 'warning' | 'error' | 'debug'
  /** Log message */
  message: string
  /** Log timestamp (ISO 8601) */
  timestamp: string
  /** Additional log metadata */
  metadata?: Record<string, unknown>
}

/**
 * Device logs response
 */
export interface DeviceLogsResponse {
  /** Array of log entries */
  logs: DeviceLog[]
  /** Total log count */
  total: number
}

/**
 * Device content assignment
 */
export interface DeviceContentAssignment {
  /** Device ID */
  device_id: number
  /** Content ID */
  content_id: number
  /** Assignment priority */
  priority?: number
  /** Playlist ID if from playlist */
  playlist_id?: number
}

/**
 * Device statistics for filters
 */
export interface DeviceStatItem {
  /** Stat label */
  label: string
  /** Stat value (count) */
  value: number
  /** Badge color */
  color: string
  /** Filter key for click handler */
  filterKey: DeviceFilter
}

/**
 * Speed test result
 */
export interface SpeedTestResult {
  /** Test ID */
  id: number
  /** Device ID */
  device_id: number
  /** Download speed in Mbps */
  download_mbps: number
  /** Upload speed in Mbps */
  upload_mbps: number
  /** Ping/latency in ms */
  ping_ms: number
  /** Test server location */
  server_location?: string
  /** Test timestamp (ISO 8601) */
  tested_at: string
}

/**
 * Speed test history response
 */
export interface SpeedTestHistoryResponse {
  /** Array of speed test results */
  tests: SpeedTestResult[]
  /** Total test count */
  total: number
  /** Average download speed */
  avg_download_mbps?: number
  /** Average upload speed */
  avg_upload_mbps?: number
  /** Average ping */
  avg_ping_ms?: number
}
