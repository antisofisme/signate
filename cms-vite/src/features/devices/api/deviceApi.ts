/**
 * Device API Service
 *
 * LAYER 3: DATA ACCESS
 * Handles all device management API calls
 */

import { apiClient } from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import type {
  Device,
  DeviceLog,
  DeviceCommand,
  MonitorRegisterRequest,
  TVRegisterRequest,
  ActivateDeviceRequest,
} from '../types/device';

interface ListResponse {
  success: boolean;
  data: {
    total: number;
    items: Device[];
  };
}

interface DetailResponse {
  success: boolean;
  data: Device;
}

interface LogsResponse {
  success: boolean;
  data: {
    total: number;
    items: DeviceLog[];
  };
}

interface CommandsResponse {
  success: boolean;
  data: {
    total: number;
    items: DeviceCommand[];
  };
}

interface CommandResponse {
  success: boolean;
  data: DeviceCommand;
}

interface ActivationCheckResponse {
  success: boolean;
  data: {
    is_valid: boolean;
    device?: Device;
  };
}

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

export const deviceApi = {
  // ========================================
  // CRUD Operations
  // ========================================

  /**
   * Get all devices with optional filters
   * @param filters - Filter options (scope, status, device_type, skip, limit)
   * @returns List of devices
   */
  list: async (filters?: {
    scope?: string;
    status?: string;
    device_type?: string;
    skip?: number;
    limit?: number;
  }): Promise<{ total: number; items: Device[] }> => {
    try {
      const params = new URLSearchParams();

      if (filters?.scope) {
        params.append('scope', filters.scope);
      }
      if (filters?.status) {
        params.append('status', filters.status);
      }
      if (filters?.device_type) {
        params.append('device_type', filters.device_type);
      }
      if (filters?.skip !== undefined) {
        params.append('skip', String(filters.skip));
      }
      if (filters?.limit !== undefined) {
        params.append('limit', String(filters.limit));
      }

      const queryString = params.toString();
      const url = `${API_ENDPOINTS.DEVICES.LIST}${queryString ? `?${queryString}` : ''}`;

      console.log('[DeviceAPI] Fetching:', url);
      const response = await apiClient.get<ListResponse>(url);
      console.log('[DeviceAPI] Response:', response.data);

      // Handle both unwrapped and wrapped responses
      if (response.data && 'total' in response.data && 'items' in response.data) {
        console.log('[DeviceAPI] Response already unwrapped by interceptor');
        return response.data as { total: number; items: Device[] };
      }

      if (response.data?.data && 'total' in response.data.data && 'items' in response.data.data) {
        console.log('[DeviceAPI] Returning wrapped response data');
        return response.data.data;
      }

      console.error('[DeviceAPI] Invalid response structure:', response.data);
      return { total: 0, items: [] };
    } catch (error) {
      console.error('[DeviceAPI] List error:', error);
      return { total: 0, items: [] };
    }
  },

  /**
   * Get device by ID
   * @param id - Device ID
   * @returns Device details
   */
  get: async (id: number): Promise<Device> => {
    const response = await apiClient.get<DetailResponse>(
      API_ENDPOINTS.DEVICES.GET(id)
    );
    return unwrapResponse<Device>(response);
  },

  /**
   * Update device
   * @param id - Device ID
   * @param deviceData - Updated device data
   * @returns Updated device
   */
  update: async (
    id: number,
    deviceData: Partial<Device>
  ): Promise<Device> => {
    const response = await apiClient.put<DetailResponse>(
      API_ENDPOINTS.DEVICES.UPDATE(id),
      deviceData
    );
    return unwrapResponse<Device>(response);
  },

  /**
   * Delete device
   * @param id - Device ID
   * @returns Success status
   */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(API_ENDPOINTS.DEVICES.DELETE(id));
  },

  // ========================================
  // Device Registration & Activation
  // ========================================

  /**
   * Activate a TV device (WebOS/native)
   * @param registerData - TV activation data (unique_code + device_name)
   * @returns Activated device
   */
  tvRegister: async (registerData: TVRegisterRequest): Promise<Device> => {
    const response = await apiClient.post<DetailResponse>(
      API_ENDPOINTS.DEVICES.ACTIVATE,
      registerData
    );
    return unwrapResponse<Device>(response);
  },

  /**
   * Activate a monitor device (browser-based)
   * @param registerData - Monitor activation data (unique_code + device_name)
   * @returns Activated device
   */
  monitorRegister: async (registerData: MonitorRegisterRequest): Promise<Device> => {
    const response = await apiClient.post<DetailResponse>(
      API_ENDPOINTS.DEVICES.ACTIVATE,
      registerData
    );
    return unwrapResponse<Device>(response);
  },

  /**
   * Activate device with code
   * @param activateData - Activation code
   * @returns Activated device
   */
  activate: async (activateData: ActivateDeviceRequest): Promise<Device> => {
    const response = await apiClient.post<DetailResponse>(
      API_ENDPOINTS.DEVICES.ACTIVATE,
      activateData
    );
    return unwrapResponse<Device>(response);
  },

  /**
   * Check activation code validity
   * @param code - 6-digit activation code
   * @returns Validation result
   */
  checkActivation: async (code: string): Promise<{ is_valid: boolean; device?: Device }> => {
    const response = await apiClient.get<ActivationCheckResponse>(
      API_ENDPOINTS.DEVICES.CHECK_ACTIVATION(code)
    );
    return unwrapResponse<{ is_valid: boolean; device?: Device }>(response);
  },

  // ========================================
  // Device Monitoring
  // ========================================

  /**
   * Send heartbeat to update device status
   * @param deviceId - Device ID
   * @returns Success status
   */
  heartbeat: async (deviceId: number): Promise<void> => {
    await apiClient.post(API_ENDPOINTS.DEVICES.HEARTBEAT(deviceId), { device_id: deviceId });
  },

  /**
   * Get device logs
   * @param id - Device ID
   * @param filters - Filter options (event_type, skip, limit)
   * @returns List of device logs
   */
  getLogs: async (
    id: number,
    filters?: {
      event_type?: string;
      skip?: number;
      limit?: number;
    }
  ): Promise<{ total: number; items: DeviceLog[] }> => {
    const params = new URLSearchParams();

    if (filters?.event_type) {
      params.append('event_type', filters.event_type);
    }
    if (filters?.skip !== undefined) {
      params.append('skip', String(filters.skip));
    }
    if (filters?.limit !== undefined) {
      params.append('limit', String(filters.limit));
    }

    const queryString = params.toString();
    const url = `${API_ENDPOINTS.DEVICES.LOGS(id)}${queryString ? `?${queryString}` : ''}`;

    const response = await apiClient.get<LogsResponse>(url);

    // Handle both unwrapped and wrapped responses
    if (response.data && 'total' in response.data && 'items' in response.data) {
      return response.data as { total: number; items: DeviceLog[] };
    }

    if (response.data?.data) {
      return response.data.data;
    }

    return { total: 0, items: [] };
  },

  // ========================================
  // Remote Commands
  // ========================================

  /**
   * Get device commands
   * @param id - Device ID
   * @param filters - Filter options (status, skip, limit)
   * @returns List of device commands
   */
  getCommands: async (
    id: number,
    filters?: {
      status?: string;
      skip?: number;
      limit?: number;
    }
  ): Promise<{ total: number; items: DeviceCommand[] }> => {
    const params = new URLSearchParams();

    if (filters?.status) {
      params.append('status', filters.status);
    }
    if (filters?.skip !== undefined) {
      params.append('skip', String(filters.skip));
    }
    if (filters?.limit !== undefined) {
      params.append('limit', String(filters.limit));
    }

    const queryString = params.toString();
    const url = `${API_ENDPOINTS.DEVICES.COMMANDS(id)}${queryString ? `?${queryString}` : ''}`;

    const response = await apiClient.get<CommandsResponse>(url);

    // Handle both unwrapped and wrapped responses
    if (response.data && 'total' in response.data && 'items' in response.data) {
      return response.data as { total: number; items: DeviceCommand[] };
    }

    if (response.data?.data) {
      return response.data.data;
    }

    return { total: 0, items: [] };
  },

  /**
   * Send command to device
   * @param id - Device ID
   * @param commandData - Command type and parameters
   * @returns Created command
   */
  sendCommand: async (
    id: number,
    commandData: {
      command_type: 'reboot' | 'screenshot' | 'volume' | 'brightness' | 'refresh';
      parameters?: Record<string, any>;
    }
  ): Promise<DeviceCommand> => {
    const response = await apiClient.post<CommandResponse>(
      API_ENDPOINTS.DEVICES.SEND_COMMAND(id),
      commandData
    );
    return unwrapResponse<DeviceCommand>(response);
  },

  // ========================================
  // Device Assignments
  // ========================================

  /**
   * Get tags assigned to device
   * @param id - Device ID
   * @returns List of assigned tags
   */
  getTags: async (id: number): Promise<{ total: number; items: any[] }> => {
    const response = await apiClient.get(`/api/v1/devices/${id}/tags`);
    return unwrapResponse<{ total: number; items: any[] }>(response);
  },

  /**
   * Assign tag to device
   * @param id - Device ID
   * @param tagId - Tag ID
   * @returns Assignment result
   */
  assignTag: async (id: number, tagId: number): Promise<any> => {
    const response = await apiClient.post(`/api/v1/devices/${id}/tags`, { tag_id: tagId });
    return unwrapResponse<any>(response);
  },

  /**
   * Unassign tag from device
   * @param id - Device ID
   * @param tagId - Tag ID
   */
  unassignTag: async (id: number, tagId: number): Promise<void> => {
    await apiClient.delete(`/api/v1/devices/${id}/tags/${tagId}`);
  },

  /**
   * Get content assigned to device
   * @param id - Device ID
   * @returns List of assigned content
   */
  getContents: async (id: number): Promise<{ total: number; items: any[] }> => {
    const response = await apiClient.get(`/api/v1/devices/${id}/contents`);
    return unwrapResponse<{ total: number; items: any[] }>(response);
  },

  /**
   * Assign content to device
   * @param id - Device ID
   * @param contentId - Content ID
   * @param priority - Assignment priority
   * @param expiresAt - Optional expiry timestamp
   * @param schedule - Optional schedule JSON
   * @returns Assignment result
   */
  assignContent: async (
    id: number,
    contentId: number,
    priority?: number,
    expiresAt?: string,
    schedule?: Record<string, any>
  ): Promise<any> => {
    const payload: any = {
      content_id: contentId,
      priority: priority || 1,
    };

    if (expiresAt) {
      payload.expires_at = expiresAt;
    }

    if (schedule) {
      payload.schedule = schedule;
    }

    const response = await apiClient.post(`/api/v1/devices/${id}/contents`, payload);
    return unwrapResponse<any>(response);
  },

  /**
   * Unassign content from device
   * @param id - Device ID
   * @param contentId - Content ID
   */
  unassignContent: async (id: number, contentId: number): Promise<void> => {
    await apiClient.delete(`/api/v1/devices/${id}/contents/${contentId}`);
  },

  /**
   * Get playlists assigned to device
   * @param id - Device ID
   * @returns List of assigned playlists
   */
  getPlaylists: async (id: number): Promise<{ total: number; items: any[] }> => {
    const response = await apiClient.get(`/api/v1/devices/${id}/playlists`);
    return unwrapResponse<{ total: number; items: any[] }>(response);
  },

  /**
   * Assign playlist to device
   * @param id - Device ID
   * @param playlistId - Playlist ID
   * @returns Assignment result
   */
  assignPlaylist: async (id: number, playlistId: number): Promise<any> => {
    const response = await apiClient.post(`/api/v1/devices/${id}/playlists`, {
      playlist_id: playlistId,
    });
    return unwrapResponse<any>(response);
  },

  /**
   * Unassign playlist from device
   * @param id - Device ID
   * @param playlistId - Playlist ID
   */
  unassignPlaylist: async (id: number, playlistId: number): Promise<void> => {
    await apiClient.delete(`/api/v1/devices/${id}/playlists/${playlistId}`);
  },

  // ========================================
  // Speed Tests
  // ========================================

  /**
   * Get speed test history for device
   * Reads from connection_logs with event_type=speed_test filter
   * @param id - Device ID
   * @returns Speed test history transformed to SpeedTest format
   */
  getSpeedTests: async (id: number): Promise<{ total: number; items: any[] }> => {
    // Speed tests are stored in connection_logs with event_type='speed_test'
    console.log('[DeviceAPI] Fetching speed tests for device:', id);
    const response = await apiClient.get(
      `${API_ENDPOINTS.DEVICES.CONNECTION_LOGS(id)}?event_type=speed_test&limit=100`
    );
    console.log('[DeviceAPI] Speed test response:', response.data);

    // Handle both wrapped and unwrapped responses
    let data: { total: number; items: any[] };
    if (response.data && 'total' in response.data && 'items' in response.data) {
      data = response.data;
    } else if (response.data?.data) {
      data = response.data.data;
    } else {
      data = { total: 0, items: [] };
    }
    console.log('[DeviceAPI] Parsed speed test data:', data);

    // Transform connection log format to speed test format
    const items = (data.items || []).map((log: any) => ({
      id: log.id,
      device_id: log.device_id,
      download_speed: log.download_speed_mbps || 0,
      upload_speed: log.upload_speed_mbps || 0,
      latency: log.latency_ms || 0,
      jitter: log.metadata?.jitter || null,
      packet_loss: log.metadata?.packet_loss || null,
      quality: calculateQuality(log.download_speed_mbps || 0, log.upload_speed_mbps || 0),
      tested_at: log.logged_at,
    }));

    return { total: data.total || items.length, items };
  },
};

/**
 * Calculate speed test quality based on speeds
 */
function calculateQuality(download: number, upload: number): 'good' | 'fair' | 'poor' {
  if (download >= 25 && upload >= 10) return 'good';
  if (download >= 10 && upload >= 5) return 'fair';
  return 'poor';
}
