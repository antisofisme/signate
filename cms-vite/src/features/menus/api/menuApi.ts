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
};
