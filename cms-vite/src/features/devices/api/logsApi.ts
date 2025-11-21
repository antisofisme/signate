/**
 * Device Logs API Service
 *
 * LAYER 3: DATA ACCESS
 * Handles device console logs and connection logs API calls
 */

import { apiClient } from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import type { DeviceLog, LogListResponse, LogFilters } from '../types/logs';

/**
 * Helper to unwrap API response - handles both interceptor-unwrapped and wrapped responses
 */
function unwrapResponse<T>(response: any): T {
  // If already unwrapped by interceptor (data is directly accessible)
  if (response.data && !('success' in response.data || 'data' in response.data)) {
    return response.data as T;
  }

  // If still wrapped (has data.data structure)
  if (response.data?.data) {
    return response.data.data as T;
  }

  // Fallback to response.data
  return response.data as T;
}

export const logsApi = {
  // ========================================
  // Console Logs
  // ========================================

  /**
   * Get device console logs with filters
   * @param deviceId - Device ID
   * @param filters - Filter options (log_level, limit, skip)
   * @returns List of device logs
   */
  getDeviceLogs: async (
    deviceId: number,
    filters?: LogFilters
  ): Promise<LogListResponse> => {
    const params = new URLSearchParams();

    if (filters?.log_level && filters.log_level !== 'all') {
      params.append('log_level', filters.log_level);
    }
    if (filters?.limit !== undefined) {
      params.append('limit', String(Math.min(500, Math.max(1, filters.limit))));
    }
    if (filters?.skip !== undefined) {
      params.append('skip', String(Math.max(0, filters.skip)));
    }

    const queryString = params.toString();
    const url = `${API_ENDPOINTS.DEVICES.LOGS(deviceId)}${queryString ? `?${queryString}` : ''}`;

    console.log('[LogsAPI] Fetching device logs:', url);
    const response = await apiClient.get(url);
    console.log('[LogsAPI] Response:', response.data);

    // Handle both unwrapped and wrapped responses
    if (response.data && 'logs' in response.data && 'total' in response.data) {
      console.log('[LogsAPI] Response already unwrapped by interceptor');
      return response.data as LogListResponse;
    }

    if (response.data?.data && 'logs' in response.data.data && 'total' in response.data.data) {
      console.log('[LogsAPI] Returning wrapped response data');
      return response.data.data;
    }

    console.error('[LogsAPI] Invalid response structure:', response.data);
    return { logs: [], total: 0 };
  },

  /**
   * Get latest N console logs
   * @param deviceId - Device ID
   * @param count - Number of latest logs (default: 20)
   * @returns Latest device logs
   */
  getLatestLogs: async (
    deviceId: number,
    count: number = 20
  ): Promise<LogListResponse> => {
    const url = `${API_ENDPOINTS.DEVICES.LOGS(deviceId)}/latest?count=${count}`;

    console.log('[LogsAPI] Fetching latest logs:', url);
    const response = await apiClient.get(url);

    // Handle both unwrapped and wrapped responses
    if (response.data && 'logs' in response.data && 'total' in response.data) {
      return response.data as LogListResponse;
    }

    if (response.data?.data && 'logs' in response.data.data && 'total' in response.data.data) {
      return response.data.data;
    }

    return { logs: [], total: 0 };
  },

  /**
   * Clear all device console logs
   * @param deviceId - Device ID
   * @returns Success status
   */
  clearDeviceLogs: async (deviceId: number): Promise<void> => {
    const url = API_ENDPOINTS.DEVICES.LOGS(deviceId);
    console.log('[LogsAPI] Clearing device logs:', url);
    await apiClient.delete(url);
  },

  // ========================================
  // Connection Logs (future implementation)
  // ========================================

  /**
   * Get device connection logs (placeholder for future implementation)
   * @param deviceId - Device ID
   * @param filters - Filter options
   * @returns Connection log entries
   */
  getConnectionLogs: async (
    deviceId: number,
    filters?: {
      event_type?: string;
      limit?: number;
      skip?: number;
    }
  ): Promise<{ logs: any[]; total: number }> => {
    // TODO: Implement when backend endpoint is ready
    console.warn('[LogsAPI] Connection logs endpoint not yet implemented');
    return { logs: [], total: 0 };
  },
};
