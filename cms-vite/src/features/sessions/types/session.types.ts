/**
 * Session Types
 * Type definitions for user session management
 */

// ============================================================================
// Core Types
// ============================================================================

export interface Session {
  id: number
  user_id: number
  token_jti?: string
  ip_address: string
  user_agent: string
  device_info?: DeviceInfo
  location?: LocationInfo
  is_current: boolean
  created_at: string
  last_activity: string
  last_activity_at?: string  // Backend uses this
  expires_at: string
}

export interface DeviceInfo {
  device_type?: 'desktop' | 'mobile' | 'tablet' | 'unknown'
  browser?: string
  browser_version?: string
  os?: string
  os_version?: string
  platform?: string
  local_ip?: string  // Local IP detected via WebRTC
  user_agent?: string
  [key: string]: unknown  // Allow additional fields from backend
}

export interface LocationInfo {
  country?: string
  country_code?: string
  region?: string
  city?: string
  timezone?: string
  isp?: string
}

// ============================================================================
// API Response Types
// ============================================================================

export interface SessionListResponse {
  sessions: Session[]
  total: number
  active_count: number
}

export interface SessionStatsResponse {
  total_sessions: number
  active_sessions: number
  sessions_by_device: {
    desktop: number
    mobile: number
    tablet: number
    unknown: number
  }
  sessions_by_country: Record<string, number>
  recent_sessions: Session[]
}

// ============================================================================
// API Request Types
// ============================================================================

export interface SessionFilters {
  user_id?: number
  is_active?: boolean
  device_type?: 'desktop' | 'mobile' | 'tablet'
  skip?: number
  limit?: number
}

export interface RevokeSessionRequest {
  session_id: number
  reason?: string
}

export interface RevokeAllSessionsRequest {
  except_current?: boolean
  reason?: string
}

// ============================================================================
// Session Activity
// ============================================================================

export interface SessionActivity {
  id: number
  session_id: string
  activity_type: SessionActivityType
  ip_address: string
  user_agent: string
  metadata?: Record<string, any>
  created_at: string
}

export type SessionActivityType =
  | 'login'
  | 'logout'
  | 'token_refresh'
  | 'password_change'
  | 'permission_change'
  | 'suspicious_activity'
  | 'api_request'

// ============================================================================
// Security Warnings
// ============================================================================

export interface SessionSecurityWarning {
  id: string
  session_id: string
  warning_type: SecurityWarningType
  severity: 'low' | 'medium' | 'high' | 'critical'
  message: string
  details?: Record<string, any>
  created_at: string
  acknowledged: boolean
}

export type SecurityWarningType =
  | 'new_device'
  | 'new_location'
  | 'unusual_activity'
  | 'multiple_failed_logins'
  | 'concurrent_sessions'
  | 'suspicious_ip'

// ============================================================================
// Helper Types
// ============================================================================

export interface SessionTimeInfo {
  created: string
  lastActive: string
  expires: string
  duration: string
  timeUntilExpiry: string
}

export interface SessionSecurity {
  isSecure: boolean
  hasWarnings: boolean
  warningCount: number
  riskLevel: 'low' | 'medium' | 'high'
}

// ============================================================================
// All Sessions Types (Admin View with User/Org Info)
// ============================================================================

export type SessionType = 'web' | 'api' | 'mobile' | 'device'

export type SessionStatus = 'active' | 'revoked' | 'expired'

export interface AllSession {
  id: number
  user_id: number
  organization_id: number | null  // Can be null for super admin
  ip_address: string
  user_agent?: string
  device_info?: Record<string, any>
  session_type: SessionType
  created_at: string
  last_activity_at: string
  expires_at: string
  revoked_at?: string | null  // When session was revoked
  status: SessionStatus  // active, revoked, or expired
  is_current?: boolean  // If this is the current session
  // User info
  username: string
  email: string
  full_name?: string
  role: string
  // Organization info
  organization_name?: string
}

export interface AllSessionsListResponse {
  items: AllSession[]
  total: number
  skip: number
  limit: number
}

export interface AllSessionsParams {
  skip?: number
  limit?: number
}
