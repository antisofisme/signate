/**
 * Device Commands API Service
 *
 * LAYER 3: DATA ACCESS
 * Handles all device command API calls
 */

import { apiClient } from '@/lib/api/client';
import type {
  DeviceCommand,
  SendCommandRequest,
  BulkSendCommandRequest,
  CommandListResponse,
  PendingCommandsResponse,
  CommandExecutionRequest,
  CommandFailureRequest,
} from '../types/commands';

interface CommandResponse {
  success: boolean;
  data: DeviceCommand;
}

interface CommandsResponse {
  success: boolean;
  data: CommandListResponse;
}

interface PendingResponse {
  success: boolean;
  data: PendingCommandsResponse;
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

export const deviceCommandApi = {
  /**
   * Send command to device (CMS)
   * @param deviceId - Device ID
   * @param command - Command details
   * @returns Created command
   */
  sendCommand: async (
    deviceId: number,
    command: SendCommandRequest
  ): Promise<DeviceCommand> => {
    try {
      const response = await apiClient.post<CommandResponse>(
        `/api/v1/devices/${deviceId}/commands`,
        command
      );
      return unwrapResponse<DeviceCommand>(response);
    } catch (error) {
      console.error('[CommandAPI] Send command error:', error);
      throw error;
    }
  },

  /**
   * Send command to multiple devices (CMS)
   * @param request - Bulk command request
   * @returns Result with success count
   */
  sendBulkCommand: async (request: BulkSendCommandRequest): Promise<any> => {
    try {
      const response = await apiClient.post(
        '/api/v1/devices/commands/bulk',
        request
      );
      return unwrapResponse<any>(response);
    } catch (error) {
      console.error('[CommandAPI] Send bulk command error:', error);
      throw error;
    }
  },

  /**
   * Get command history for device (CMS)
   * @param deviceId - Device ID
   * @param filters - Filter options
   * @returns Command history
   */
  getCommands: async (
    deviceId: number,
    filters?: {
      status?: string;
      skip?: number;
      limit?: number;
    }
  ): Promise<CommandListResponse> => {
    try {
      const params = new URLSearchParams();

      if (filters?.status) {
        params.append('status_filter', filters.status);
      }
      if (filters?.skip !== undefined) {
        params.append('skip', String(filters.skip));
      }
      if (filters?.limit !== undefined) {
        params.append('limit', String(filters.limit));
      }

      const queryString = params.toString();
      const url = `/api/v1/devices/${deviceId}/commands${queryString ? `?${queryString}` : ''}`;

      const response = await apiClient.get<CommandsResponse>(url);

      // Handle both unwrapped and wrapped responses
      const data = response.data;
      if (data && 'total' in data && 'items' in data) {
        return data as CommandListResponse;
      }

      if (data?.data && 'total' in data.data && 'items' in data.data) {
        return data.data;
      }

      return { total: 0, items: [] };
    } catch (error) {
      console.error('[CommandAPI] Get commands error:', error);
      return { total: 0, items: [] };
    }
  },

  /**
   * Get pending commands for device (Player)
   * @param deviceId - Device ID
   * @returns Pending commands
   */
  getPendingCommands: async (deviceId: number): Promise<PendingCommandsResponse> => {
    try {
      const response = await apiClient.get<PendingResponse>(
        `/api/v1/devices/${deviceId}/commands/pending`
      );
      return unwrapResponse<PendingCommandsResponse>(response);
    } catch (error) {
      console.error('[CommandAPI] Get pending commands error:', error);
      return { commands: [], count: 0 };
    }
  },

  /**
   * Mark command as executed (Player)
   * @param deviceId - Device ID
   * @param commandId - Command ID
   * @param result - Execution result
   */
  markExecuted: async (
    deviceId: number,
    commandId: number,
    result?: CommandExecutionRequest
  ): Promise<void> => {
    try {
      await apiClient.post(
        `/api/v1/devices/${deviceId}/commands/${commandId}/execute`,
        result || { result: { status: 'success' } }
      );
    } catch (error) {
      console.error('[CommandAPI] Mark executed error:', error);
      throw error;
    }
  },

  /**
   * Mark command as failed (Player)
   * @param deviceId - Device ID
   * @param commandId - Command ID
   * @param failure - Failure details
   */
  markFailed: async (
    deviceId: number,
    commandId: number,
    failure: CommandFailureRequest
  ): Promise<void> => {
    try {
      await apiClient.post(
        `/api/v1/devices/commands/${commandId}/failed`,
        failure
      );
    } catch (error) {
      console.error('[CommandAPI] Mark failed error:', error);
      throw error;
    }
  },

  /**
   * Quick reset command (CMS)
   * @param deviceId - Device ID
   * @param reason - Reason for reset
   * @returns Created command
   */
  sendResetCommand: async (
    deviceId: number,
    reason?: string
  ): Promise<DeviceCommand> => {
    try {
      const response = await apiClient.post<CommandResponse>(
        `/api/v1/devices/${deviceId}/commands/reset?reason=${encodeURIComponent(reason || 'manual_reset')}`
      );
      return unwrapResponse<DeviceCommand>(response);
    } catch (error) {
      console.error('[CommandAPI] Send reset command error:', error);
      throw error;
    }
  },
};
