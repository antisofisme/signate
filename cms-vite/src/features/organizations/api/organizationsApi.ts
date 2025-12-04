/**
 * Organizations API Service
 *
 * LAYER 3: DATA ACCESS
 * Handles all organization-related API calls
 */

import { apiClient } from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import type {
  Organization,
  CreateOrganizationRequest,
  UpdateOrganizationRequest,
  OrganizationListData,
  OrganizationResponse,
  OrganizationListResponse,
  OrganizationQuota,
  QuotaCheckResult,
  UpdateQuotaRequest,
  RegeneratePinResponse,
  UpdatePinRequest,
} from '../types/organization';

interface OrganizationListFilters {
  active_only?: boolean;
  sort_by?: string;
  sort_dir?: 'asc' | 'desc';
}

export const organizationsApi = {
  /**
   * Get all organizations
   * @param filters - Optional filters (activeOnly, sort_by, sort_dir)
   * @returns List of organizations with stats
   */
  list: async (filters: OrganizationListFilters = {}): Promise<OrganizationListData> => {
    const params = new URLSearchParams();
    if (filters.active_only) {
      params.append('active_only', 'true');
    }
    if (filters.sort_by) {
      params.append('sort_by', filters.sort_by);
    }
    if (filters.sort_dir) {
      params.append('sort_dir', filters.sort_dir);
    }

    const queryString = params.toString();
    const url = queryString
      ? `${API_ENDPOINTS.ORGANIZATIONS.LIST}?${queryString}`
      : API_ENDPOINTS.ORGANIZATIONS.LIST;

    const { data } = await apiClient.get<OrganizationListData>(url);
    return data;
  },

  /**
   * Get organization by ID
   * @param id - Organization ID
   * @returns Organization with stats
   */
  get: async (id: number): Promise<Organization> => {
    const { data } = await apiClient.get<Organization>(
      API_ENDPOINTS.ORGANIZATIONS.GET(id)
    );
    return data;
  },

  /**
   * Create new organization
   * @param orgData - Organization data
   * @returns Created organization with auto-generated PIN
   */
  create: async (
    orgData: CreateOrganizationRequest
  ): Promise<Organization> => {
    const { data } = await apiClient.post<Organization>(
      API_ENDPOINTS.ORGANIZATIONS.CREATE,
      orgData
    );
    return data;
  },

  /**
   * Update organization
   * @param id - Organization ID
   * @param orgData - Updated organization data
   * @returns Updated organization
   */
  update: async (
    id: number,
    orgData: UpdateOrganizationRequest
  ): Promise<Organization> => {
    const { data } = await apiClient.put<Organization>(
      API_ENDPOINTS.ORGANIZATIONS.UPDATE(id),
      orgData
    );
    return data;
  },

  /**
   * Delete organization (soft delete)
   * @param id - Organization ID
   */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(API_ENDPOINTS.ORGANIZATIONS.DELETE(id));
  },

  // ==========================================================================
  // QUOTA OPERATIONS
  // ==========================================================================

  /**
   * Get organization quota status
   * @param id - Organization ID
   * @returns Quota information with usage percentages
   */
  getQuota: async (id: number): Promise<OrganizationQuota> => {
    const { data } = await apiClient.get<OrganizationQuota>(
      API_ENDPOINTS.ORGANIZATIONS.QUOTA(id)
    );
    return data;
  },

  /**
   * Update organization quota limits
   * @param id - Organization ID
   * @param quotaData - New quota limits
   * @returns Updated quota information
   */
  updateQuota: async (
    id: number,
    quotaData: UpdateQuotaRequest
  ): Promise<OrganizationQuota> => {
    const { data } = await apiClient.put<OrganizationQuota>(
      API_ENDPOINTS.ORGANIZATIONS.UPDATE_QUOTA(id),
      quotaData
    );
    return data;
  },

  /**
   * Check if organization can add more devices
   * @param id - Organization ID
   * @returns Quota check result
   */
  checkDeviceQuota: async (id: number): Promise<QuotaCheckResult> => {
    const { data } = await apiClient.get<QuotaCheckResult>(
      API_ENDPOINTS.ORGANIZATIONS.CHECK_DEVICE_QUOTA(id)
    );
    return data;
  },

  /**
   * Check if organization can add more users
   * @param id - Organization ID
   * @returns Quota check result
   */
  checkUserQuota: async (id: number): Promise<QuotaCheckResult> => {
    const { data } = await apiClient.get<QuotaCheckResult>(
      API_ENDPOINTS.ORGANIZATIONS.CHECK_USER_QUOTA(id)
    );
    return data;
  },

  /**
   * Check if organization can add content with specified size
   * @param id - Organization ID
   * @param fileSizeBytes - File size in bytes
   * @returns Quota check result
   */
  checkContentQuota: async (
    id: number,
    fileSizeBytes: number
  ): Promise<QuotaCheckResult> => {
    const { data } = await apiClient.get<QuotaCheckResult>(
      `${API_ENDPOINTS.ORGANIZATIONS.CHECK_CONTENT_QUOTA(id)}?file_size_bytes=${fileSizeBytes}`
    );
    return data;
  },

  // ==========================================================================
  // PIN MANAGEMENT
  // ==========================================================================

  /**
   * Regenerate organization PIN with a new random PIN
   * @param id - Organization ID
   * @returns New PIN response
   */
  regeneratePin: async (id: number): Promise<RegeneratePinResponse> => {
    const { data } = await apiClient.post<RegeneratePinResponse>(
      API_ENDPOINTS.ORGANIZATIONS.REGENERATE_PIN(id)
    );
    return data;
  },

  /**
   * Update organization PIN with a custom PIN
   * @param id - Organization ID
   * @param pinData - New PIN data
   * @returns Updated PIN response
   */
  updatePin: async (
    id: number,
    pinData: UpdatePinRequest
  ): Promise<RegeneratePinResponse> => {
    const { data } = await apiClient.put<RegeneratePinResponse>(
      API_ENDPOINTS.ORGANIZATIONS.UPDATE_PIN(id),
      pinData
    );
    return data;
  },
};
