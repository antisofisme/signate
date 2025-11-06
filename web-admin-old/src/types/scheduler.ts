/**
 * Scheduler Type Definitions
 *
 * Type definitions for scheduler service, device schedules, and related data structures.
 */

/**
 * Scheduler service status
 */
export type SchedulerServiceStatus = 'running' | 'stopped' | 'error'

/**
 * Scheduler status response from API
 */
export interface SchedulerStatus {
  /** Service running status */
  status: SchedulerServiceStatus
  /** Last scheduler run timestamp (ISO 8601) */
  last_run: string | null
  /** Next scheduled run timestamp (ISO 8601) */
  next_run: string | null
  /** Number of devices being monitored */
  devices_count: number
  /** Total refresh operations performed */
  total_refreshes: number
  /** Service uptime in seconds */
  uptime_seconds?: number
  /** Any error message if status is 'error' */
  error_message?: string | null
}

/**
 * Device schedule information
 */
export interface DeviceSchedule {
  /** Device ID */
  device_id: number
  /** Device name */
  device_name: string
  /** Device status */
  device_status: 'pending' | 'active' | 'inactive'
  /** Next content refresh deadline (ISO 8601) */
  next_deadline: string | null
  /** Seconds until next deadline */
  seconds_until_deadline: number | null
  /** Current content being played */
  current_content: {
    /** Content ID */
    id: number | null
    /** Content title */
    title: string | null
    /** Content type */
    type: 'image' | 'video' | null
  } | null
  /** Current playlist being played */
  current_playlist: {
    /** Playlist ID */
    id: number | null
    /** Playlist name */
    name: string | null
  } | null
  /** Last refresh timestamp (ISO 8601) */
  last_refresh: string | null
  /** Whether device is online (based on heartbeat) */
  is_online: boolean
}

/**
 * Refresh result for a single device
 */
export interface DeviceRefreshResult {
  /** Device ID */
  device_id: number
  /** Device name */
  device_name: string
  /** Whether refresh was successful */
  success: boolean
  /** Number of content items refreshed */
  items_refreshed: number
  /** Error message if failed */
  error_message?: string | null
  /** Timestamp of refresh operation (ISO 8601) */
  refreshed_at: string
}

/**
 * Bulk refresh result for multiple devices
 */
export interface BulkRefreshResult {
  /** Total devices attempted */
  total_devices: number
  /** Number of successful refreshes */
  successful: number
  /** Number of failed refreshes */
  failed: number
  /** Individual device results */
  results: DeviceRefreshResult[]
  /** Timestamp of bulk refresh operation (ISO 8601) */
  refreshed_at: string
}

/**
 * Countdown timer state
 */
export interface CountdownState {
  /** Days remaining */
  days: number
  /** Hours remaining */
  hours: number
  /** Minutes remaining */
  minutes: number
  /** Seconds remaining */
  seconds: number
  /** Total seconds remaining */
  totalSeconds: number
  /** Whether deadline has passed */
  isExpired: boolean
}
