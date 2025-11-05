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
} from '../types/organization';

export const organizationsApi = {
  /**
   * Get all organizations
   * @param activeOnly - Filter for active organizations only
   * @returns List of organizations with stats
   */
  list: async (activeOnly = false): Promise<OrganizationListData> => {
    const params = new URLSearchParams();
    if (activeOnly) {
      params.append('active_only', 'true');
    }

    const { data } = await apiClient.get<OrganizationListData>(
      `${API_ENDPOINTS.ORGANIZATIONS.LIST}?${params.toString()}`
    );
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
};
