/**
 * Device Assignments API Service
 *
 * Handles all device assignment operations:
 * - Playlist assignments
 * - Content assignments (with expiry support)
 * - Tag assignments
 * - Bulk operations
 */

import { apiClient } from '@/lib/api/client';
import type {
  PlaylistAssignment,
  ContentAssignment,
  TagAssignment,
  AssignContentRequest,
  AssignPlaylistRequest,
  AssignTagRequest,
  BulkAssignPlaylistRequest,
  AssignmentsListResponse,
  AssignmentResponse,
  BulkAssignmentResponse,
} from '../types/assignment';

/**
 * Helper to unwrap API response
 */
function unwrapResponse<T>(response: any): T {
  // If already unwrapped by interceptor
  if (response.data && !('success' in response.data || 'data' in response.data)) {
    return response.data as T;
  }

  // If still wrapped
  if (response.data?.data) {
    return response.data.data as T;
  }

  return response.data as T;
}

export const deviceAssignmentsApi = {
  // ========================================
  // Playlist Assignments
  // ========================================

  /**
   * Get playlists assigned to device
   * @param deviceId - Device ID
   * @returns List of assigned playlists
   */
  getDevicePlaylists: async (deviceId: number): Promise<{ total: number; items: PlaylistAssignment[] }> => {
    const response = await apiClient.get<AssignmentsListResponse<PlaylistAssignment>>(
      `/api/v1/devices/${deviceId}/playlists`
    );
    return unwrapResponse<{ total: number; items: PlaylistAssignment[] }>(response);
  },

  /**
   * Assign playlist to device
   * @param deviceId - Device ID
   * @param data - Playlist assignment data
   * @returns Assignment result
   */
  assignPlaylistToDevice: async (
    deviceId: number,
    data: AssignPlaylistRequest
  ): Promise<PlaylistAssignment> => {
    const response = await apiClient.post<AssignmentResponse<PlaylistAssignment>>(
      `/api/v1/devices/${deviceId}/playlists`,
      data
    );
    return unwrapResponse<PlaylistAssignment>(response);
  },

  /**
   * Unassign playlist from device
   * @param deviceId - Device ID
   * @param playlistId - Playlist ID to unassign
   */
  unassignPlaylistFromDevice: async (deviceId: number, playlistId: number): Promise<void> => {
    await apiClient.delete(`/api/v1/devices/${deviceId}/playlists/${playlistId}`);
  },

  /**
   * Bulk assign playlist to multiple devices
   * @param playlistId - Playlist ID
   * @param data - Device IDs to assign to
   * @returns Bulk assignment result
   */
  bulkAssignPlaylistToDevices: async (
    playlistId: number,
    data: BulkAssignPlaylistRequest
  ): Promise<{ assigned: number; failed: number; errors?: string[] }> => {
    const response = await apiClient.post<BulkAssignmentResponse>(
      `/api/v1/playlists/${playlistId}/devices`,
      data
    );
    return unwrapResponse<{ assigned: number; failed: number; errors?: string[] }>(response);
  },

  // ========================================
  // Content Assignments
  // ========================================

  /**
   * Get content assigned to device
   * @param deviceId - Device ID
   * @returns List of assigned content
   */
  getDeviceContents: async (deviceId: number): Promise<{ total: number; items: ContentAssignment[] }> => {
    const response = await apiClient.get<AssignmentsListResponse<ContentAssignment>>(
      `/api/v1/devices/${deviceId}/contents`
    );
    return unwrapResponse<{ total: number; items: ContentAssignment[] }>(response);
  },

  /**
   * Assign content to device with optional expiry
   * @param deviceId - Device ID
   * @param data - Content assignment data (content_id, priority, schedule, expires_at)
   * @returns Assignment result
   */
  assignContentToDevice: async (
    deviceId: number,
    data: AssignContentRequest
  ): Promise<ContentAssignment> => {
    const response = await apiClient.post<AssignmentResponse<ContentAssignment>>(
      `/api/v1/devices/${deviceId}/contents`,
      data
    );
    return unwrapResponse<ContentAssignment>(response);
  },

  /**
   * Unassign content from device
   * @param deviceId - Device ID
   * @param contentId - Content ID to unassign
   */
  unassignContentFromDevice: async (deviceId: number, contentId: number): Promise<void> => {
    await apiClient.delete(`/api/v1/devices/${deviceId}/contents/${contentId}`);
  },

  // ========================================
  // Tag Assignments
  // ========================================

  /**
   * Get tags assigned to device
   * @param deviceId - Device ID
   * @returns List of assigned tags
   */
  getDeviceTags: async (deviceId: number): Promise<{ total: number; items: TagAssignment[] }> => {
    const response = await apiClient.get<AssignmentsListResponse<TagAssignment>>(
      `/api/v1/devices/${deviceId}/tags`
    );
    return unwrapResponse<{ total: number; items: TagAssignment[] }>(response);
  },

  /**
   * Assign tag to device
   * @param deviceId - Device ID
   * @param data - Tag assignment data
   * @returns Assignment result
   */
  assignTagToDevice: async (deviceId: number, data: AssignTagRequest): Promise<TagAssignment> => {
    const response = await apiClient.post<AssignmentResponse<TagAssignment>>(
      `/api/v1/devices/${deviceId}/tags`,
      data
    );
    return unwrapResponse<TagAssignment>(response);
  },

  /**
   * Unassign tag from device
   * @param deviceId - Device ID
   * @param tagId - Tag ID to unassign
   */
  unassignTagFromDevice: async (deviceId: number, tagId: number): Promise<void> => {
    await apiClient.delete(`/api/v1/devices/${deviceId}/tags/${tagId}`);
  },
};
