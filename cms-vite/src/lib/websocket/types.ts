/**
 * WebSocket Types
 * Type definitions for WebSocket messages and events
 */

// ============================================================================
// Message Types
// ============================================================================

export type WebSocketMessageType =
  | 'device:status'
  | 'device:connected'
  | 'device:disconnected'
  | 'device:heartbeat'
  | 'playback:start'
  | 'playback:end'
  | 'playback:update'
  | 'content:sync'
  | 'playlist:sync'
  | 'command:ack'
  | 'command:complete'
  | 'command:error'
  | 'analytics:update'
  | 'system:notification'
  | 'error'
  | 'ping'
  | 'pong'

// ============================================================================
// Base Message Structure
// ============================================================================

export interface WebSocketMessage<T = any> {
  type: WebSocketMessageType
  data: T
  timestamp: string
  device_id?: number
  user_id?: number
}

// ============================================================================
// Device Events
// ============================================================================

export interface DeviceStatusData {
  device_id: number
  status: 'online' | 'offline' | 'error'
  last_seen: string
  ip_address?: string
}

export interface DeviceHeartbeatData {
  device_id: number
  timestamp: string
  system_info?: {
    cpu_usage?: number
    memory_usage?: number
    disk_usage?: number
    uptime?: number
  }
}

// ============================================================================
// Playback Events
// ============================================================================

export interface PlaybackStartData {
  device_id: number
  content_id: number
  playlist_id?: number
  started_at: string
}

export interface PlaybackEndData {
  device_id: number
  content_id: number
  playlist_id?: number
  ended_at: string
  duration: number
}

export interface PlaybackUpdateData {
  device_id: number
  content_id: number
  current_position: number
  total_duration: number
  state: 'playing' | 'paused' | 'buffering'
}

// ============================================================================
// Command Events
// ============================================================================

export interface CommandAckData {
  command_id: string
  device_id: number
  acknowledged_at: string
}

export interface CommandCompleteData {
  command_id: string
  device_id: number
  completed_at: string
  result?: any
}

export interface CommandErrorData {
  command_id: string
  device_id: number
  error: string
  occurred_at: string
}

// ============================================================================
// Sync Events
// ============================================================================

export interface ContentSyncData {
  device_id: number
  content_ids: number[]
  sync_status: 'started' | 'in_progress' | 'completed' | 'failed'
  progress?: number
}

export interface PlaylistSyncData {
  device_id: number
  playlist_id: number
  sync_status: 'started' | 'completed' | 'failed'
}

// ============================================================================
// Analytics Events
// ============================================================================

export interface AnalyticsUpdateData {
  type: 'device' | 'content' | 'playlist'
  data: {
    total_devices?: number
    online_devices?: number
    total_plays?: number
    total_duration?: number
    [key: string]: any
  }
}

// ============================================================================
// System Events
// ============================================================================

export interface SystemNotificationData {
  level: 'info' | 'warning' | 'error' | 'success'
  title: string
  message: string
  action_url?: string
}

// ============================================================================
// WebSocket Client Config
// ============================================================================

export interface WebSocketConfig {
  url: string
  reconnect?: boolean
  reconnectInterval?: number
  maxReconnectAttempts?: number
  heartbeatInterval?: number
  debug?: boolean
}

// ============================================================================
// WebSocket Client State
// ============================================================================

export type WebSocketState = 'connecting' | 'connected' | 'disconnected' | 'error'

// ============================================================================
// Event Handlers
// ============================================================================

export type WebSocketEventHandler<T = any> = (data: T) => void

export interface WebSocketEventHandlers {
  onOpen?: () => void
  onClose?: (event: CloseEvent) => void
  onError?: (error: Event) => void
  onMessage?: (message: WebSocketMessage) => void
}
