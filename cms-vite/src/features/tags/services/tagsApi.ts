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
    const response = await apiClient.get<{success: boolean; data: Tag}>(API_ENDPOINTS.TAGS.GET(id));
    return response.data.data;
  },

  /**
   * Get tag with usage statistics
   * @param id - Tag ID
   * @returns Tag with device and content counts
   */
  getUsage: async (id: number): Promise<TagWithUsage> => {
    const response = await apiClient.get<{success: boolean; data: {tag: Tag; usage: {device_count: number; content_count: number}}}>(
      API_ENDPOINTS.TAGS.USAGE(id)
    );
    return {
      ...response.data.data.tag,
      device_count: response.data.data.usage.device_count,
      content_count: response.data.data.usage.content_count
    };
  },

  /**
   * Create new tag
   * @param tagData - Tag data
   * @returns Created tag
   */
  create: async (tagData: CreateTagRequest): Promise<Tag> => {
    const response = await apiClient.post<{success: boolean; data: Tag}>(
      API_ENDPOINTS.TAGS.CREATE,
      tagData
    );
    return response.data.data;
  },

  /**
   * Update tag
   * @param id - Tag ID
   * @param tagData - Updated tag data
   * @returns Updated tag
   */
  update: async (id: number, tagData: UpdateTagRequest): Promise<Tag> => {
    const response = await apiClient.put<{success: boolean; data: Tag}>(
      API_ENDPOINTS.TAGS.UPDATE(id),
      tagData
    );
    return response.data.data;
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
};
