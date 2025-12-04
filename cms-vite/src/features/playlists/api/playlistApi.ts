/**
 * Playlist API Service
 *
 * LAYER 3: DATA ACCESS
 * Handles all playlist management API calls
 */

import { apiClient } from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import { logger } from '@/shared/utils/logger';
import type {
  Playlist,
  PlaylistContent,
  CreatePlaylistRequest,
  UpdatePlaylistRequest,
  AddContentRequest,
  ReorderContentRequest,
  AssignDevicesRequest,
  PlaylistAssignmentsResponse,
  BulkOperationResponse,
  RemoveOperationResponse,
} from '../types/playlist';

interface ListResponse {
  success: boolean;
  data: {
    total: number;
    items: Playlist[];
  };
}

interface DetailResponse {
  success: boolean;
  data: Playlist;
}

interface ContentListResponse {
  success: boolean;
  data: {
    total: number;
    items: PlaylistContent[];
  };
}

interface AssignmentsResponse {
  success: boolean;
  data: PlaylistAssignmentsResponse;
}

interface BulkResponse {
  success: boolean;
  data: BulkOperationResponse;
}

interface RemoveResponse {
  success: boolean;
  data: RemoveOperationResponse;
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

export const playlistApi = {
  // ========================================
  // CRUD Operations
  // ========================================

  /**
   * Get all playlists with optional filters
   * @param filters - Filter options (is_active, skip, limit, sort_by, sort_dir)
   * @returns List of playlists
   */
  list: async (filters?: {
    is_active?: boolean;
    skip?: number;
    limit?: number;
    sort_by?: string;
    sort_dir?: 'asc' | 'desc' | null;
  }): Promise<{ total: number; items: Playlist[] }> => {
    try {
      const params = new URLSearchParams();

      if (filters?.is_active !== undefined) {
        params.append('is_active', String(filters.is_active));
      }
      if (filters?.skip !== undefined) {
        params.append('skip', String(filters.skip));
      }
      if (filters?.limit !== undefined) {
        params.append('limit', String(filters.limit));
      }
      // Sorting
      if (filters?.sort_by) {
        params.append('sort_by', filters.sort_by);
      }
      if (filters?.sort_dir) {
        params.append('sort_dir', filters.sort_dir);
      }

      const queryString = params.toString();
      const url = `${API_ENDPOINTS.PLAYLISTS.LIST}${queryString ? `?${queryString}` : ''}`;

      logger.debug('[PlaylistAPI] Fetching:', url);
      const response = await apiClient.get<ListResponse>(url);
      logger.debug('[PlaylistAPI] Response:', response.data);

      // Handle both unwrapped and wrapped responses
      // Interceptor unwraps if no 'total' found at top level
      if (response.data && 'total' in response.data && 'items' in response.data) {
        logger.debug('[PlaylistAPI] Response already unwrapped by interceptor');
        return response.data as { total: number; items: Playlist[] };
      }

      // Handle wrapped response
      if (response.data?.data && 'total' in response.data.data && 'items' in response.data.data) {
        logger.debug('[PlaylistAPI] Returning wrapped response data');
        return response.data.data;
      }

      logger.error('[PlaylistAPI] Invalid response structure:', response.data);
      return { total: 0, items: [] };
    } catch (error) {
      logger.error('[PlaylistAPI] List error:', error);
      return { total: 0, items: [] };
    }
  },

  /**
   * Get playlist by ID
   * @param id - Playlist ID
   * @returns Playlist details with stats
   */
  get: async (id: number): Promise<Playlist> => {
    const response = await apiClient.get<DetailResponse>(
      API_ENDPOINTS.PLAYLISTS.GET(id)
    );
    return unwrapResponse<Playlist>(response);
  },

  /**
   * Create new playlist
   * @param playlistData - Playlist data
   * @returns Created playlist
   */
  create: async (playlistData: CreatePlaylistRequest): Promise<Playlist> => {
    const response = await apiClient.post<DetailResponse>(
      API_ENDPOINTS.PLAYLISTS.CREATE,
      playlistData
    );
    return unwrapResponse<Playlist>(response);
  },

  /**
   * Update playlist
   * @param id - Playlist ID
   * @param playlistData - Updated playlist data
   * @returns Updated playlist
   */
  update: async (
    id: number,
    playlistData: UpdatePlaylistRequest
  ): Promise<Playlist> => {
    const response = await apiClient.patch<DetailResponse>(
      API_ENDPOINTS.PLAYLISTS.UPDATE(id),
      playlistData
    );
    return unwrapResponse<Playlist>(response);
  },

  /**
   * Delete playlist
   * @param id - Playlist ID
   * @returns Success status
   */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(API_ENDPOINTS.PLAYLISTS.DELETE(id));
  },

  /**
   * Duplicate playlist with all its contents
   * @param id - Playlist ID to duplicate
   * @param newName - Optional custom name for the new playlist
   * @returns Duplicated playlist
   */
  duplicate: async (id: number, newName?: string): Promise<Playlist> => {
    const response = await apiClient.post<DetailResponse>(
      API_ENDPOINTS.PLAYLISTS.DUPLICATE(id),
      { new_name: newName }
    );
    return unwrapResponse<Playlist>(response);
  },

  // ========================================
  // Content Management
  // ========================================

  /**
   * Get playlist content items
   * @param id - Playlist ID
   * @returns List of content items
   */
  getContent: async (
    id: number
  ): Promise<{ total: number; items: PlaylistContent[] }> => {
    const response = await apiClient.get<ContentListResponse>(
      API_ENDPOINTS.PLAYLISTS.GET_CONTENT(id)
    );

    // Handle both unwrapped and wrapped responses
    if (response.data && 'total' in response.data && 'items' in response.data) {
      return response.data as { total: number; items: PlaylistContent[] };
    }

    if (response.data?.data) {
      return response.data.data;
    }

    return { total: 0, items: [] };
  },

  /**
   * Add content to playlist
   * @param id - Playlist ID
   * @param contentData - Content IDs to add
   * @returns Bulk operation result
   */
  addContent: async (
    id: number,
    contentData: AddContentRequest
  ): Promise<BulkOperationResponse> => {
    const response = await apiClient.post<BulkResponse>(
      API_ENDPOINTS.PLAYLISTS.ADD_CONTENT(id),
      contentData
    );
    return unwrapResponse<BulkOperationResponse>(response);
  },

  /**
   * Remove content from playlist
   * @param playlistId - Playlist ID
   * @param itemId - Content item ID
   * @returns Remove operation result
   */
  removeContent: async (
    playlistId: number,
    itemId: number
  ): Promise<RemoveOperationResponse> => {
    const response = await apiClient.delete<RemoveResponse>(
      API_ENDPOINTS.PLAYLISTS.REMOVE_CONTENT(playlistId, itemId)
    );
    return unwrapResponse<RemoveOperationResponse>(response);
  },

  /**
   * Reorder playlist content
   * @param id - Playlist ID
   * @param reorderData - New content order
   * @returns Success status
   */
  reorderContent: async (
    id: number,
    reorderData: ReorderContentRequest
  ): Promise<void> => {
    await apiClient.patch(
      API_ENDPOINTS.PLAYLISTS.REORDER_CONTENT(id),
      reorderData
    );
  },

  // ========================================
  // Assignment Management
  // ========================================

  /**
   * Get playlist assignments (devices only)
   * NOTE: Tag assignments have been removed - Tags are NOT assigned to Playlists
   * @param id - Playlist ID
   * @returns List of assigned devices
   */
  getAssignments: async (id: number): Promise<PlaylistAssignmentsResponse> => {
    const response = await apiClient.get<AssignmentsResponse>(
      API_ENDPOINTS.PLAYLISTS.GET_ASSIGNMENTS(id)
    );
    return unwrapResponse<PlaylistAssignmentsResponse>(response);
  },

  /**
   * Assign playlist to devices
   * @param id - Playlist ID
   * @param assignData - Device IDs to assign
   * @returns Bulk operation result
   */
  assignDevices: async (
    id: number,
    assignData: AssignDevicesRequest
  ): Promise<BulkOperationResponse> => {
    const response = await apiClient.post<BulkResponse>(
      API_ENDPOINTS.PLAYLISTS.ASSIGN_DEVICES(id),
      assignData
    );
    return unwrapResponse<BulkOperationResponse>(response);
  },

  /**
   * Unassign playlist from devices
   * @param id - Playlist ID
   * @param unassignData - Device IDs to unassign
   * @returns Remove operation result
   */
  unassignDevices: async (
    id: number,
    unassignData: AssignDevicesRequest
  ): Promise<RemoveOperationResponse> => {
    const response = await apiClient.delete<RemoveResponse>(
      API_ENDPOINTS.PLAYLISTS.UNASSIGN_DEVICES(id),
      { data: unassignData }
    );
    return unwrapResponse<RemoveOperationResponse>(response);
  },

};
