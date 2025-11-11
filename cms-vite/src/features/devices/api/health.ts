/**
 * Device Health API Service
 *
 * LAYER 3: DATA ACCESS
 * Handles all device health monitoring API calls
 */

import { apiClient } from '@/lib/api/client';
import type {
  DeviceHealthMetrics,
  DeviceHealthWithAlerts,
  HealthHistoryResponse,
  OrganizationHealthSummary,
  RecordHealthMetricsRequest,
} from '../types/health';

interface HealthResponse {
  success: boolean;
  data: DeviceHealthMetrics;
}

interface HealthWithAlertsResponse {
  success: boolean;
  data: DeviceHealthWithAlerts;
}

interface HistoryResponse {
  success: boolean;
  data: HealthHistoryResponse;
}

interface OrgSummaryResponse {
  success: boolean;
  data: OrganizationHealthSummary;
}

/**
 * Helper to unwrap API response
 */
function unwrapResponse<T>(response: any): T {
  // If already unwrapped by interceptor
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

export const deviceHealthApi = {
  /**
   * Get latest health metrics with alerts (CMS)
   * @param deviceId - Device ID
   * @returns Latest health metrics and active alerts
   */
  getHealth: async (deviceId: number): Promise<DeviceHealthWithAlerts> => {
    try {
      const response = await apiClient.get<HealthWithAlertsResponse>(
        `/api/v1/devices/${deviceId}/health`
      );
      return unwrapResponse<DeviceHealthWithAlerts>(response);
    } catch (error) {
      console.error('[HealthAPI] Get health error:', error);
      throw error;
    }
  },

  /**
   * Get latest health metrics only (CMS)
   * @param deviceId - Device ID
   * @returns Latest health metrics
   */
  getLatestHealth: async (deviceId: number): Promise<DeviceHealthMetrics | null> => {
    try {
      const response = await apiClient.get<HealthResponse>(
        `/api/v1/devices/${deviceId}/health/latest`
      );
      const data = unwrapResponse<DeviceHealthMetrics | null>(response);
      return data;
    } catch (error) {
      console.error('[HealthAPI] Get latest health error:', error);
      return null;
    }
  },

  /**
   * Get health history for charting (CMS)
   * @param deviceId - Device ID
   * @param hours - Hours of history (default: 24, max: 168)
   * @returns Historical health metrics
   */
  getHealthHistory: async (
    deviceId: number,
    hours: number = 24
  ): Promise<HealthHistoryResponse> => {
    try {
      const response = await apiClient.get<HistoryResponse>(
        `/api/v1/devices/${deviceId}/health/history?hours=${hours}`
      );
      return unwrapResponse<HealthHistoryResponse>(response);
    } catch (error) {
      console.error('[HealthAPI] Get health history error:', error);
      return { history: [], count: 0 };
    }
  },

  /**
   * Get health alerts only (CMS)
   * @param deviceId - Device ID
   * @returns Active health alerts
   */
  getAlerts: async (deviceId: number): Promise<any[]> => {
    try {
      const response = await apiClient.get(`/api/v1/devices/${deviceId}/health/alerts`);
      return unwrapResponse<any[]>(response);
    } catch (error) {
      console.error('[HealthAPI] Get alerts error:', error);
      return [];
    }
  },

  /**
   * Get organization health summary (CMS)
   * @param organizationId - Organization ID
   * @returns Organization-wide health statistics
   */
  getOrganizationSummary: async (
    organizationId: number
  ): Promise<OrganizationHealthSummary> => {
    try {
      const response = await apiClient.get<OrgSummaryResponse>(
        `/api/v1/organizations/${organizationId}/health/summary`
      );
      return unwrapResponse<OrganizationHealthSummary>(response);
    } catch (error) {
      console.error('[HealthAPI] Get org summary error:', error);
      // Return empty summary on error
      return {
        total_devices: 0,
        healthy_devices: 0,
        warning_devices: 0,
        critical_devices: 0,
        offline_devices: 0,
        devices_with_errors: 0,
      };
    }
  },

  /**
   * Record health metrics (Player - included for completeness)
   * @param deviceId - Device ID
   * @param metrics - Health metrics to record
   * @returns Recorded health metric
   */
  recordHealth: async (
    deviceId: number,
    metrics: RecordHealthMetricsRequest
  ): Promise<DeviceHealthMetrics> => {
    try {
      const response = await apiClient.post<HealthResponse>(
        `/api/v1/devices/${deviceId}/health`,
        metrics
      );
      return unwrapResponse<DeviceHealthMetrics>(response);
    } catch (error) {
      console.error('[HealthAPI] Record health error:', error);
      throw error;
    }
  },
};
