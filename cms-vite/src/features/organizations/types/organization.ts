/**
 * Organization Domain Types
 */

import type { SuccessResponse } from '@/lib/api/responseTypes';

export interface Organization {
  id: number;
  name: string;
  organization_pin?: string; // REMOVED: Organization PIN (No-PIN flow)
  description?: string;
  address?: string;
  contact_email?: string;
  contact_phone?: string;
  logo_url?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  // Stats from backend
  user_count?: number;
  device_count?: number;
}

export interface CreateOrganizationRequest {
  name: string;
  organization_pin?: string; // Optional, 8-digit, auto-generated if not provided
  description?: string;
  address?: string;
  contact_email?: string;
  contact_phone?: string;
  logo_url?: string;
}

export interface UpdateOrganizationRequest {
  name: string;
  description?: string;
  address?: string;
  contact_email?: string;
  contact_phone?: string;
  logo_url?: string;
  is_active: boolean;
}

export interface OrganizationListData {
  organizations: Organization[];
  total: number;
  active: number;
}

export type OrganizationResponse = SuccessResponse<Organization>;
export type OrganizationListResponse = SuccessResponse<OrganizationListData>;

// ============================================================================
// QUOTA TYPES
// ============================================================================

export interface QuotaInfo {
  max: number;
  current: number;
  available: number;
  percentage_used: number;
}

export interface StorageQuotaInfo {
  max_items: number;
  current_items: number;
  available_items: number;
  max_size_gb: number;
  current_size_gb: number;
  available_size_gb: number;
  items_percentage_used: number;
  size_percentage_used: number;
}

export interface OrganizationQuota {
  devices: QuotaInfo;
  users: QuotaInfo;
  content: StorageQuotaInfo;
  playlists: QuotaInfo;
  total_percentage_used: number;
  warnings: string[];
}

export interface QuotaCheckResult {
  allowed: boolean;
  reason?: string;
  current: number;
  max: number;
  available: number;
}

export interface UpdateQuotaRequest {
  max_devices?: number;
  max_users?: number;
  max_content_size_gb?: number;
  max_content_items?: number;
  max_playlists?: number;
}

export type OrganizationQuotaResponse = SuccessResponse<OrganizationQuota>;
export type QuotaCheckResponse = SuccessResponse<QuotaCheckResult>;

// ============================================================================
// PIN MANAGEMENT TYPES
// ============================================================================

export interface RegeneratePinResponse {
  organization_id: number;
  new_pin: string;
  message: string;
}

export interface UpdatePinRequest {
  new_pin: string;
}
