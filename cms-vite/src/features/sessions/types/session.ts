/**
 * Session Domain Types
 * Generated from backend-python/services/session/dtos.py
 */

export type SessionType = 'web' | 'api' | 'mobile' | 'device';

export interface Session {
  id: number;
  user_id: number;
  organization_id: number;
  ip_address: string;
  user_agent?: string;
  device_info?: Record<string, any>;
  session_type: SessionType;
  created_at: string;
  last_activity_at: string;
  expires_at: string;
  revoked_at?: string;
  is_active: boolean;
}

export interface SessionListResponse {
  sessions: Session[];
  total: number;
  active: number;
  expired: number;
  revoked: number;
}

export interface SessionStatsResponse {
  total: number;
  active: number;
  expired: number;
  revoked: number;
  by_type?: Record<string, number>;
  by_organization?: Record<number, number>;
}

export interface SessionRevokeResponse {
  success: boolean;
  sessions_revoked: number;
  message: string;
}

// Request types
export interface SessionCreateRequest {
  user_id: number;
  organization_id: number;
  access_token: string;
  refresh_token?: string;
  ip_address: string;
  user_agent?: string;
  device_info?: Record<string, any>;
  session_type?: SessionType;
  expires_in_minutes?: number;
}

export interface SessionRevokeRequest {
  session_id?: number;
  revoke_all?: boolean;
}

export interface SessionFilterParams {
  user_id?: number;
  organization_id?: number;
  session_type?: SessionType;
  active_only?: boolean;
  include_revoked?: boolean;
  include_expired?: boolean;
  ip_address?: string;
  limit?: number;
}
