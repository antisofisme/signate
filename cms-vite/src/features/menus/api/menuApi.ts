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

export const menuApi = {
  // ========== Menu CRUD ==========

  /**
   * List all menus for current organization
   */
  list: async (params?: MenuListParams): Promise<MenuListResponse> => {
    const response = await apiClient.get(BASE_URL, { params });
    return response.data.data;
  },

  /**
   * Create new menu
   */
  create: async (data: MenuCreateRequest): Promise<Menu> => {
    const response = await apiClient.post(BASE_URL, data);
    return response.data.data;
  },

  /**
   * Get single menu by ID
   */
  get: async (id: number): Promise<Menu> => {
    const response = await apiClient.get(`${BASE_URL}/${id}`);
    return response.data.data;
  },

  /**
   * Update menu
   */
  update: async (id: number, data: MenuUpdateRequest): Promise<Menu> => {
    const response = await apiClient.patch(`${BASE_URL}/${id}`, data);
    return response.data.data;
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
    return response.data.data;
  },

  /**
   * Add item to menu
   */
  addItem: async (menuId: number, data: MenuItemCreateRequest): Promise<MenuItem> => {
    const response = await apiClient.post(`${BASE_URL}/${menuId}/items`, data);
    return response.data.data;
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
    return response.data.data;
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

    return response.data.data;
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
    return response.data.data.items;
  },

  // ========== QR Code ==========

  /**
   * Regenerate QR code for menu
   */
  regenerateQRCode: async (menuId: number): Promise<Menu> => {
    const response = await apiClient.post(`${BASE_URL}/${menuId}/regenerate-qr`);
    return response.data.data;
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
