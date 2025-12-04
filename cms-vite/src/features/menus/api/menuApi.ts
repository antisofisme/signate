/**
 * Menu API Client
 */

import { apiClient } from '@/lib/api/client';
import type {
  Menu,
  MenuItem,
  MenuCreateRequest,
  MenuUpdateRequest,
  MenuListResponse,
  MenuListParams,
  MenuItemCreateRequest,
  MenuItemUpdateRequest,
  MenuItemListResponse,
  MenuItemListParams,
  MenuImportResult,
  MenuImportHistory,
  MenuMedia,
  MenuMediaFilters,
  MenuMediaListResponse,
  MenuMediaDuplicatesResponse,
  // Category types
  MenuCategory,
  MenuCategoryCreateRequest,
  MenuCategoryUpdateRequest,
  MenuCategoryListResponse,
  MenuCategoryReorderRequest,
  // Item Media types
  MenuItemMedia,
  MenuItemMediaAddRequest,
  MenuItemMediaListResponse,
  MenuItemMediaBulkSetRequest,
  MenuItemMediaReorderRequest,
  // PIN types
  PINVerifyRequest,
  PINVerifyResponse,
} from '../types/menu';

const BASE_URL = '/api/v1/menus';

/**
 * Helper to unwrap API response - handles both interceptor-unwrapped and wrapped responses
 */
function unwrapResponse<T>(response: any): T {
  // If already unwrapped by interceptor (data is directly accessible without 'success' wrapper)
  if (response.data && !('success' in response.data) && !('data' in response.data)) {
    return response.data as T;
  }

  // If still wrapped (has data.data structure)
  if (response.data?.data) {
    return response.data.data as T;
  }

  // Fallback to response.data
  return response.data as T;
}

export const menuApi = {
  // ========== Menu CRUD ==========

  /**
   * List all menus for current organization
   */
  list: async (params?: MenuListParams): Promise<MenuListResponse> => {
    const response = await apiClient.get(BASE_URL, { params });
    return unwrapResponse<MenuListResponse>(response);
  },

  /**
   * Create new menu
   */
  create: async (data: MenuCreateRequest): Promise<Menu> => {
    const response = await apiClient.post(BASE_URL, data);
    return unwrapResponse<Menu>(response);
  },

  /**
   * Get single menu by ID
   */
  get: async (id: number): Promise<Menu> => {
    const response = await apiClient.get(`${BASE_URL}/${id}`);
    return unwrapResponse<Menu>(response);
  },

  /**
   * Update menu
   */
  update: async (id: number, data: MenuUpdateRequest): Promise<Menu> => {
    const response = await apiClient.patch(`${BASE_URL}/${id}`, data);
    return unwrapResponse<Menu>(response);
  },

  /**
   * Delete menu (soft delete)
   */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`${BASE_URL}/${id}`);
  },

  // ========== Menu Items ==========

  /**
   * List items for menu
   */
  listItems: async (
    menuId: number,
    params?: MenuItemListParams
  ): Promise<MenuItemListResponse> => {
    const response = await apiClient.get(`${BASE_URL}/${menuId}/items`, { params });
    return unwrapResponse<MenuItemListResponse>(response);
  },

  /**
   * Add item to menu
   */
  addItem: async (menuId: number, data: MenuItemCreateRequest): Promise<MenuItem> => {
    const response = await apiClient.post(`${BASE_URL}/${menuId}/items`, data);
    return unwrapResponse<MenuItem>(response);
  },

  /**
   * Update menu item
   */
  updateItem: async (
    menuId: number,
    itemId: number,
    data: MenuItemUpdateRequest
  ): Promise<MenuItem> => {
    const response = await apiClient.patch(`${BASE_URL}/${menuId}/items/${itemId}`, data);
    return unwrapResponse<MenuItem>(response);
  },

  /**
   * Delete menu item
   */
  deleteItem: async (menuId: number, itemId: number): Promise<void> => {
    await apiClient.delete(`${BASE_URL}/${menuId}/items/${itemId}`);
  },

  // ========== Excel Import/Export ==========

  /**
   * Import menu items from Excel file
   */
  importExcel: async (
    menuId: number,
    file: File,
    replaceExisting: boolean = false
  ): Promise<MenuImportResult> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post(
      `${BASE_URL}/${menuId}/import?replace_existing=${replaceExisting}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    return unwrapResponse<MenuImportResult>(response);
  },

  /**
   * Download Excel template
   */
  downloadTemplate: async (): Promise<Blob> => {
    const response = await apiClient.get(`${BASE_URL}/excel-template`, {
      responseType: 'blob',
    });
    return response.data;
  },

  /**
   * Export menu to Excel
   */
  exportMenu: async (menuId: number): Promise<Blob> => {
    const response = await apiClient.get(`${BASE_URL}/${menuId}/export`, {
      responseType: 'blob',
    });
    return response.data;
  },

  /**
   * Get import history for menu
   */
  getImportHistory: async (menuId: number): Promise<MenuImportHistory[]> => {
    const response = await apiClient.get(`${BASE_URL}/${menuId}/import-history`);
    const data = unwrapResponse<{ items: MenuImportHistory[] }>(response);
    return data.items;
  },

  // ========== QR Code ==========

  /**
   * Regenerate QR code for menu
   */
  regenerateQRCode: async (menuId: number): Promise<Menu> => {
    const response = await apiClient.post(`${BASE_URL}/${menuId}/regenerate-qr`);
    return unwrapResponse<Menu>(response);
  },

  /**
   * Download QR code image
   */
  downloadQRCode: async (menuId: number): Promise<Blob> => {
    const response = await apiClient.get(`${BASE_URL}/${menuId}/qr-code`, {
      responseType: 'blob',
    });
    return response.data;
  },

  // ========== Menu Media ==========

  /**
   * List menu media with filters and pagination
   */
  listMedia: async (filters?: MenuMediaFilters): Promise<MenuMediaListResponse> => {
    const params = new URLSearchParams();
    if (filters?.skip !== undefined) params.append('skip', filters.skip.toString());
    if (filters?.limit !== undefined) params.append('limit', filters.limit.toString());
    if (filters?.search) params.append('search', filters.search);
    if (filters?.is_active !== undefined) params.append('is_active', filters.is_active.toString());
    // Sorting
    if (filters?.sort_by) params.append('sort_by', filters.sort_by);
    if (filters?.sort_dir) params.append('sort_dir', filters.sort_dir);
    // Cache-busting
    params.append('_t', Date.now().toString());

    const response = await apiClient.get(`/api/v1/menu-media?${params.toString()}`);
    return unwrapResponse<MenuMediaListResponse>(response);
  },

  /**
   * List deleted menu media (Recycle Bin)
   */
  listDeletedMedia: async (filters?: MenuMediaFilters): Promise<MenuMediaListResponse> => {
    const params = new URLSearchParams();
    if (filters?.skip !== undefined) params.append('skip', filters.skip.toString());
    if (filters?.limit !== undefined) params.append('limit', filters.limit.toString());
    if (filters?.search) params.append('search', filters.search);
    // Cache-busting
    params.append('_t', Date.now().toString());

    const response = await apiClient.get(`/api/v1/menu-media/deleted?${params.toString()}`);
    return unwrapResponse<MenuMediaListResponse>(response);
  },

  /**
   * Upload menu media
   */
  uploadMedia: async (file: File, title?: string, altText?: string): Promise<MenuMedia> => {
    const formData = new FormData();
    formData.append('file', file);
    if (title) formData.append('title', title);
    if (altText) formData.append('alt_text', altText);

    const response = await apiClient.post('/api/v1/menu-media', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return unwrapResponse<MenuMedia>(response);
  },

  /**
   * Update menu media
   */
  updateMedia: async (
    id: number,
    data: { title?: string; alt_text?: string }
  ): Promise<MenuMedia> => {
    const response = await apiClient.patch(`/api/v1/menu-media/${id}`, data);
    return unwrapResponse<MenuMedia>(response);
  },

  /**
   * Delete menu media (soft delete - move to recycle bin)
   */
  deleteMedia: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/v1/menu-media/${id}`);
  },

  /**
   * Restore menu media from recycle bin
   */
  restoreMedia: async (id: number): Promise<MenuMedia> => {
    const response = await apiClient.post(`/api/v1/menu-media/${id}/restore`);
    return unwrapResponse<MenuMedia>(response);
  },

  /**
   * Permanently delete menu media
   */
  permanentDeleteMedia: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/v1/menu-media/${id}/permanent`);
  },

  /**
   * Bulk permanent delete menu media
   */
  bulkPermanentDeleteMedia: async (ids: number[]): Promise<{ deleted_count: number }> => {
    const response = await apiClient.post('/api/v1/menu-media/bulk-permanent-delete', ids);
    return unwrapResponse<{ deleted_count: number }>(response);
  },

  /**
   * Get duplicate menu media (files with same hash)
   */
  getDuplicateMedia: async (): Promise<MenuMediaDuplicatesResponse> => {
    const response = await apiClient.get('/api/v1/menu-media/duplicates');
    return unwrapResponse<MenuMediaDuplicatesResponse>(response);
  },

  // ========== PIN Verification ==========

  /**
   * Verify organization PIN
   */
  verifyPIN: async (pin: string): Promise<PINVerifyResponse> => {
    const response = await apiClient.post(`${BASE_URL}/verify-pin`, { pin });
    return unwrapResponse<PINVerifyResponse>(response);
  },

  /**
   * Delete menu with PIN verification
   */
  deleteWithPIN: async (menuId: number, pin: string): Promise<void> => {
    await apiClient.delete(`${BASE_URL}/${menuId}/with-pin`, {
      data: { pin },
    });
  },

  // ========== Menu Categories (Per-Menu) ==========

  /**
   * List categories for a menu
   */
  listCategories: async (menuId: number): Promise<MenuCategoryListResponse> => {
    const response = await apiClient.get(`${BASE_URL}/${menuId}/categories`);
    return unwrapResponse<MenuCategoryListResponse>(response);
  },

  /**
   * Create a category for a menu
   */
  createCategory: async (
    menuId: number,
    data: MenuCategoryCreateRequest
  ): Promise<MenuCategory> => {
    const response = await apiClient.post(`${BASE_URL}/${menuId}/categories`, data);
    return unwrapResponse<MenuCategory>(response);
  },

  /**
   * Update a menu category
   */
  updateCategory: async (
    menuId: number,
    categoryId: number,
    data: MenuCategoryUpdateRequest
  ): Promise<MenuCategory> => {
    const response = await apiClient.patch(
      `${BASE_URL}/${menuId}/categories/${categoryId}`,
      data
    );
    return unwrapResponse<MenuCategory>(response);
  },

  /**
   * Delete a menu category
   */
  deleteCategory: async (menuId: number, categoryId: number): Promise<void> => {
    await apiClient.delete(`${BASE_URL}/${menuId}/categories/${categoryId}`);
  },

  /**
   * Reorder categories for a menu
   */
  reorderCategories: async (
    menuId: number,
    data: MenuCategoryReorderRequest
  ): Promise<MenuCategoryListResponse> => {
    const response = await apiClient.post(
      `${BASE_URL}/${menuId}/categories/reorder`,
      data
    );
    return unwrapResponse<MenuCategoryListResponse>(response);
  },

  // ========== Menu Item Media (Multiple Media per Item) ==========

  /**
   * List all media for a menu item
   */
  listItemMedia: async (
    menuId: number,
    itemId: number
  ): Promise<MenuItemMediaListResponse> => {
    const response = await apiClient.get(
      `${BASE_URL}/${menuId}/items/${itemId}/media`
    );
    return unwrapResponse<MenuItemMediaListResponse>(response);
  },

  /**
   * Add media to a menu item
   */
  addItemMedia: async (
    menuId: number,
    itemId: number,
    data: MenuItemMediaAddRequest
  ): Promise<MenuItemMedia> => {
    const response = await apiClient.post(
      `${BASE_URL}/${menuId}/items/${itemId}/media`,
      data
    );
    return unwrapResponse<MenuItemMedia>(response);
  },

  /**
   * Remove media from a menu item
   */
  removeItemMedia: async (
    menuId: number,
    itemId: number,
    mediaId: number
  ): Promise<void> => {
    await apiClient.delete(
      `${BASE_URL}/${menuId}/items/${itemId}/media/${mediaId}`
    );
  },

  /**
   * Bulk set media for a menu item (replaces existing)
   */
  bulkSetItemMedia: async (
    menuId: number,
    itemId: number,
    data: MenuItemMediaBulkSetRequest
  ): Promise<MenuItemMediaListResponse> => {
    const response = await apiClient.post(
      `${BASE_URL}/${menuId}/items/${itemId}/media/bulk`,
      data
    );
    return unwrapResponse<MenuItemMediaListResponse>(response);
  },

  /**
   * Set a media as primary for a menu item
   */
  setItemPrimaryMedia: async (
    menuId: number,
    itemId: number,
    mediaId: number
  ): Promise<{ message: string }> => {
    const response = await apiClient.post(
      `${BASE_URL}/${menuId}/items/${itemId}/media/${mediaId}/set-primary`
    );
    return unwrapResponse<{ message: string }>(response);
  },

  /**
   * Reorder media for a menu item
   */
  reorderItemMedia: async (
    menuId: number,
    itemId: number,
    data: MenuItemMediaReorderRequest
  ): Promise<MenuItemMediaListResponse> => {
    const response = await apiClient.post(
      `${BASE_URL}/${menuId}/items/${itemId}/media/reorder`,
      data
    );
    return unwrapResponse<MenuItemMediaListResponse>(response);
  },
};
