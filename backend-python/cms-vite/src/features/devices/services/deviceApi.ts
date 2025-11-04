/**
 * Device API Service
 * API calls for device management
 */

import { apiClient } from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import type {
  Device,
  DeviceListResponse,
  ActivateDeviceRequest,
  UpdateDeviceRequest,
  DeviceFilters,
} from '../types/device';

export const deviceApi = {
  /**
   * List all devices for organization
   */
  async list(organizationId: number, filters?: DeviceFilters): Promise<DeviceListResponse> {
    const params = new URLSearchParams({
      organization_id: organizationId.toString(),
    });

    if (filters?.status) {
      params.append('status_filter', filters.status);
    }

    if (filters?.online_only) {
      params.append('online_only', 'true');
    }

    const response = await apiClient.get<DeviceListResponse>(
      `${API_ENDPOINTS.DEVICES.LIST}?${params.toString()}`
    );
    return response.data;
  },

  /**
   * Get device by ID
   */
  async get(deviceId: number): Promise<Device> {
    const response = await apiClient.get<Device>(API_ENDPOINTS.DEVICES.GET(deviceId));
    return response.data;
  },

  /**
   * Activate device with 6-digit code
   */
  async activate(request: ActivateDeviceRequest): Promise<Device> {
    const response = await apiClient.post<Device>(
      API_ENDPOINTS.DEVICES.ACTIVATE,
      request
    );
    return response.data;
  },

  /**
   * Update device settings
   */
  async update(deviceId: number, request: UpdateDeviceRequest): Promise<Device> {
    const response = await apiClient.put<Device>(
      API_ENDPOINTS.DEVICES.UPDATE(deviceId),
      request
    );
    return response.data;
  },

  /**
   * Delete device
   */
  async delete(deviceId: number): Promise<void> {
    await apiClient.delete(API_ENDPOINTS.DEVICES.DELETE(deviceId));
  },

  /**
   * Check activation status by code (for polling)
   */
  async checkActivation(code: string): Promise<{
    is_activated: boolean;
    device_id?: number;
    device_name?: string;
    message: string;
  }> {
    const response = await apiClient.get(API_ENDPOINTS.DEVICES.CHECK_ACTIVATION(code));
    return response.data;
  },
};
