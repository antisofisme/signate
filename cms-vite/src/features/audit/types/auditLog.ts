/**
 * Audit Log Types
 *
 * LAYER 3: DOMAIN
 * Type definitions for audit logging
 */

export interface AuditLog {
  id: number;
  user_id: number | null;
  username?: string;
  organization_id: number | null;
  organization_name?: string;
  action: string;
  resource_type: string;
  resource_id: number | null;
  details: Record<string, any> | null;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
}

export interface AuditLogListResponse {
  logs: AuditLog[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface AuditLogFilters {
  user_id?: number;
  organization_id?: number;
  action?: string;
  resource_type?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  per_page?: number;
  sort_by?: string;
  sort_dir?: 'asc' | 'desc';
}

export const RESOURCE_TYPES = [
  'user',
  'organization',
  'device',
  'content',
  'auth',
] as const;

export const ACTION_CATEGORIES = {
  user: ['user.create', 'user.update', 'user.delete', 'user.change_password'],
  organization: ['organization.create', 'organization.update', 'organization.delete'],
  device: ['device.create', 'device.update', 'device.delete', 'device.activate'],
  content: ['content.upload', 'content.delete', 'content.assign'],
  auth: ['auth.login', 'auth.logout', 'auth.register'],
} as const;
