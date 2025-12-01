/**
 * Tags API Service
 *
 * LAYER 3: DATA ACCESS
 * Handles all tag management API calls
 */

import { apiClient } from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import type {
  Tag,
  TagWithUsage,
  CreateTagRequest,
  UpdateTagRequest,
  TagListFilters,
} from '../types/tag';

export const tagsApi = {
  /**
   * Get all tags with optional sorting
   * @param filters - Filter and sort options
   * @returns List of tags
   */
  list: async (filters?: TagListFilters): Promise<Tag[]> => {
    const params = new URLSearchParams();

    if (filters?.sort_by) {
      params.append('sort_by', filters.sort_by);
    }

    const queryString = params.toString();
    const url = `${API_ENDPOINTS.TAGS.LIST}${queryString ? `?${queryString}` : ''}`;

    const response = await apiClient.get<{success: boolean; data: Tag[]; total: number}>(url);
    return response.data.data;
  },

  /**
   * Get tag by ID
   * @param id - Tag ID
   * @returns Tag details
   */
  get: async (id: number): Promise<Tag> => {
    const response = await apiClient.get<Tag>(API_ENDPOINTS.TAGS.GET(id));
    // Interceptor already unwraps { success, data } to just data
    return response.data;
  },

  /**
   * Get tag with usage statistics
   * @param id - Tag ID
   * @returns Tag with device and content counts
   */
  getUsage: async (id: number): Promise<TagWithUsage> => {
    const response = await apiClient.get<{tag: Tag; usage: {device_count: number; content_count: number}}>(
      API_ENDPOINTS.TAGS.USAGE(id)
    );
    // Interceptor already unwraps { success, data } to just data
    return {
      tag: response.data.tag,
      usage: response.data.usage
    };
  },

  /**
   * Create new tag
   * @param tagData - Tag data
   * @returns Created tag
   */
  create: async (tagData: CreateTagRequest): Promise<Tag> => {
    const response = await apiClient.post<Tag>(
      API_ENDPOINTS.TAGS.CREATE,
      tagData
    );
    // Interceptor already unwraps { success, data } to just data
    return response.data;
  },

  /**
   * Update tag
   * @param id - Tag ID
   * @param tagData - Updated tag data
   * @returns Updated tag
   */
  update: async (id: number, tagData: UpdateTagRequest): Promise<Tag> => {
    const response = await apiClient.put<Tag>(
      API_ENDPOINTS.TAGS.UPDATE(id),
      tagData
    );
    // Interceptor already unwraps { success, data } to just data
    return response.data;
  },

  /**
   * Delete tag
   * @param id - Tag ID
   * @param force - Force delete even if in use
   */
  delete: async (id: number, force: boolean = false): Promise<void> => {
    const params = force ? '?force=true' : '';
    await apiClient.delete(`${API_ENDPOINTS.TAGS.DELETE(id)}${params}`);
  },

  /**
   * Assign tag to a single content item
   * @param tagId - Tag ID
   * @param contentId - Content ID
   */
  assignToContent: async (tagId: number, contentId: number): Promise<{success: boolean; message: string}> => {
    const response = await apiClient.post<{success: boolean; message: string}>(
      API_ENDPOINTS.TAGS.ASSIGN_TO_CONTENT(tagId),
      { content_id: contentId }
    );
    return response.data;
  },

  /**
   * Bulk assign tag to multiple content items
   * @param tagId - Tag ID
   * @param contentIds - Array of content IDs
   */
  assignToContents: async (tagId: number, contentIds: number[]): Promise<{
    success: boolean;
    assigned: number;
    skipped: number;
    failed: number;
    message: string;
  }> => {
    const response = await apiClient.post<{
      success: boolean;
      assigned: number;
      skipped: number;
      failed: number;
      message: string;
    }>(
      API_ENDPOINTS.TAGS.ASSIGN_TO_CONTENTS(tagId),
      { content_ids: contentIds }
    );
    return response.data;
  },

  /**
   * Unassign tag from a single content item
   * @param tagId - Tag ID
   * @param contentId - Content ID
   */
  unassignFromContent: async (tagId: number, contentId: number): Promise<{success: boolean; message: string}> => {
    const response = await apiClient.delete<{success: boolean; message: string}>(
      API_ENDPOINTS.TAGS.UNASSIGN_FROM_CONTENT(tagId),
      { data: { content_id: contentId } }
    );
    return response.data;
  },

  /**
   * Bulk unassign tag from multiple content items
   * @param tagId - Tag ID
   * @param contentIds - Array of content IDs
   */
  unassignFromContents: async (tagId: number, contentIds: number[]): Promise<{
    success: boolean;
    unassigned: number;
    not_found: number;
    message: string;
  }> => {
    const response = await apiClient.delete<{
      success: boolean;
      unassigned: number;
      not_found: number;
      message: string;
    }>(
      API_ENDPOINTS.TAGS.UNASSIGN_FROM_CONTENTS(tagId),
      { data: { content_ids: contentIds } }
    );
    return response.data;
  },

  /**
   * Get all tags assigned to a content item
   * @param contentId - Content ID
   * @returns List of tags
   */
  getContentTags: async (contentId: number): Promise<Tag[]> => {
    const response = await apiClient.get<{success: boolean; data: Tag[]; total: number}>(
      API_ENDPOINTS.TAGS.GET_CONTENT_TAGS(contentId)
    );
    return response.data.data;
  },

  // =========================================================================
  // DEVICE-TAG OPERATIONS
  // =========================================================================

  /**
   * Get all devices assigned to a tag
   * @param tagId - Tag ID
   * @returns List of devices
   */
  getTagDevices: async (tagId: number): Promise<{
    id: number;
    device_name: string;
    device_type: string;
    status: string;
    assigned_at: string;
  }[]> => {
    const response = await apiClient.get<{
      success: boolean;
      data: {
        id: number;
        device_name: string;
        device_type: string;
        status: string;
        assigned_at: string;
      }[];
      total: number;
    }>(API_ENDPOINTS.TAGS.GET_DEVICES(tagId));
    return response.data.data;
  },

  /**
   * Bulk assign tag to multiple devices
   * @param tagId - Tag ID
   * @param deviceIds - Array of device IDs
   */
  assignToDevices: async (tagId: number, deviceIds: number[]): Promise<{
    success: boolean;
    assigned: number;
    skipped: number;
    failed: number;
    message: string;
  }> => {
    const response = await apiClient.post<{
      success: boolean;
      assigned: number;
      skipped: number;
      failed: number;
      message: string;
    }>(
      API_ENDPOINTS.TAGS.ASSIGN_TO_DEVICES(tagId),
      { device_ids: deviceIds }
    );
    return response.data;
  },

  /**
   * Bulk unassign tag from multiple devices
   * @param tagId - Tag ID
   * @param deviceIds - Array of device IDs
   */
  unassignFromDevices: async (tagId: number, deviceIds: number[]): Promise<{
    success: boolean;
    unassigned: number;
    not_found: number;
    message: string;
  }> => {
    const response = await apiClient.delete<{
      success: boolean;
      unassigned: number;
      not_found: number;
      message: string;
    }>(
      API_ENDPOINTS.TAGS.UNASSIGN_FROM_DEVICES(tagId),
      { data: { device_ids: deviceIds } }
    );
    return response.data;
  },
};
