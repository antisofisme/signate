/**
 * API Type Definitions
 *
 * Comprehensive TypeScript interfaces for all API responses and data structures
 * Used across the application for type safety and IDE autocomplete
 */

// ============================================================================
// Common Types
// ============================================================================

/** Standard API response wrapper */
export interface ApiResponse<T> {
  success: boolean
  data: T
  meta: {
    timestamp: string
    request_id: string
    version: string
  }
}

/** Generic error response */
export interface ApiError {
  detail: string
  status?: number
}

/** Pagination metadata */
export interface PaginationMeta {
  total: number
  page: number
  per_page: number
  total_pages: number
}

// ============================================================================
// Device Types
// ============================================================================

/** Device types */
export type DeviceType = 'tv' | 'monitor'

/** Device status */
export type DeviceStatus = 'active' | 'pending' | 'inactive'

/** Device platform */
export type DevicePlatform = 'WebOS' | 'Tizen' | 'Chrome' | 'Firefox' | 'Safari' | 'Edge' | 'Unknown'

/** Device data structure */
export interface Device {
  id: number
  device_name: string
  device_type: DeviceType
  status: DeviceStatus
  platform?: DevicePlatform | string
  ip_address?: string
  unique_code?: string
  last_seen?: string | null
  created_at: string
  updated_at: string
  tag_ids?: number[]
  tags?: Tag[]
}

/** Devices list response */
export interface DevicesResponse {
  devices: Device[]
  total: number
}

/** Device update payload */
export interface DeviceUpdatePayload {
  device_name?: string
  status?: DeviceStatus
  tag_ids?: number[]
}

// ============================================================================
// Content Types
// ============================================================================

/** Content type */
export type ContentType = 'image' | 'video' | 'widget'

/** Content item structure */
export interface ContentItem {
  id: number
  title: string
  description?: string
  content_type: ContentType
  file_path: string
  file_url?: string
  thumbnail_url?: string
  anthias_url?: string
  anthias_asset_id?: string
  mime_type?: string
  duration: number
  file_size?: number
  is_active: boolean
  created_at: string
  updated_at: string
  order?: number
  // Media metadata
  resolution?: string
  codec?: string
  fps?: number
  bitrate?: number
  video_duration?: number
  audio_codec?: string
  audio_bitrate?: number
  audio_sample_rate?: number
  // Video segment timing
  video_start_time?: number
  video_end_time?: number | null
}

/** Content list response */
export interface ContentResponse {
  items: ContentItem[]
  total: number
}

/** Content assignment */
export interface ContentAssignment {
  id: number
  device_id?: number
  tag_id?: number
  device_name?: string
  tag_name?: string
  priority: number
  display_order?: number
  created_at: string
  assigned_at?: string
}

/** Content assignments mapping */
export interface ContentAssignmentsMap {
  [contentId: number]: ContentAssignment[]
}

// ============================================================================
// Tag Types
// ============================================================================

/** Tag structure */
export interface Tag {
  id: number
  tag_name: string
  description?: string
  color: string
  device_count: number
  created_at: string
  updated_at: string
}

/** Tags list response */
export interface TagsResponse {
  items: Tag[]
  total: number
}

/** Tag create/update payload */
export interface TagPayload {
  tag_name: string
  description?: string
  color: string
}

// ============================================================================
// Playlist Types
// ============================================================================

/** Playlist item in playlist */
export interface PlaylistContentItem {
  id: number
  content_id: number
  order: number
  content?: ContentItem
}

/** Playlist structure */
export interface Playlist {
  id: number
  name: string
  description?: string
  is_active: boolean
  created_at: string
  updated_at: string
  items?: PlaylistContentItem[]
  item_count?: number
}

/** Playlists list response */
export interface PlaylistsResponse {
  items: Playlist[]
  total: number
}

/** Playlist create/update payload */
export interface PlaylistPayload {
  name: string
  description?: string
  is_active?: boolean
  content_ids?: number[]
}

// ============================================================================
// Authentication Types
// ============================================================================

/** Login credentials */
export interface LoginCredentials {
  username: string
  password: string
}

/** Login response */
export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in?: number
}

/** User info */
export interface User {
  id: number
  username: string
  email?: string
  is_admin: boolean
  created_at: string
}

// ============================================================================
// Activity Log Types
// ============================================================================

/** Activity type */
export type ActivityType =
  | 'device_registered'
  | 'device_approved'
  | 'device_deleted'
  | 'device_updated'
  | 'content_uploaded'
  | 'content_deleted'
  | 'content_updated'
  | 'playlist_created'
  | 'playlist_updated'
  | 'playlist_deleted'
  | 'tag_created'
  | 'tag_updated'
  | 'tag_deleted'

/** Activity log entry */
export interface ActivityLog {
  id: number
  activity_type: ActivityType
  description: string
  details?: Record<string, unknown>
  user_id?: number
  created_at: string
}

/** Activity logs response */
export interface ActivityLogsResponse {
  items: ActivityLog[]
  total: number
}

// ============================================================================
// Speed Test Types
// ============================================================================

/** Speed test result */
export interface SpeedTestResult {
  id: number
  device_id: number
  download_speed: number
  upload_speed: number
  ping: number
  jitter?: number
  packet_loss?: number
  tested_at: string
  created_at: string
}

/** Speed test history response */
export interface SpeedTestHistoryResponse {
  items: SpeedTestResult[]
  total: number
}

// ============================================================================
// WebSocket Types
// ============================================================================

/** WebSocket message type */
export type WebSocketMessageType = 'dashboard_update' | 'device_status' | 'heartbeat'

/** WebSocket event */
export type WebSocketEvent = ActivityType | 'heartbeat'

/** WebSocket message structure */
export interface WebSocketMessage {
  type: WebSocketMessageType
  event: WebSocketEvent
  data?: unknown
  timestamp?: string
}

// ============================================================================
// Dashboard Statistics Types
// ============================================================================

/** Dashboard stat card configuration */
export interface DashboardStat {
  name: string
  value: number
  subtitle: string
  icon: React.ComponentType<{ className?: string }>
  color: StatColor
}

/** Stat card color variants */
export type StatColor = 'blue' | 'green' | 'purple' | 'orange' | 'indigo' | 'teal'

/** Device statistics */
export interface DeviceStatistics {
  tvDevices: number
  monitorDevices: number
  activeDevices: number
  pendingDevices: number
  onlineDevices: number
}

// ============================================================================
// Form Types
// ============================================================================

/** Generic form field change event */
export type FormChangeEvent = React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>

/** Generic form submit event */
export type FormSubmitEvent = React.FormEvent<HTMLFormElement>

// ============================================================================
// Utility Types
// ============================================================================

/** Make all properties optional recursively */
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P]
}

/** Extract array element type */
export type ArrayElement<T> = T extends (infer U)[] ? U : never
