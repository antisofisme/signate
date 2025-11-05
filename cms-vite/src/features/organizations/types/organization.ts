/**
 * Organization Domain Types
 */

import type { SuccessResponse } from '@/lib/api/responseTypes';

export interface Organization {
  id: number;
  name: string;
  organization_pin: string;
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
