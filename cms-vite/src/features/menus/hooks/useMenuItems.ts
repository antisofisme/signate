/**
 * React Query Hooks for Menu Items Management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from '@/shared/utils/toast';
import { menuApi } from '../api/menuApi';
import { menuKeys } from './useMenus';
import { getApiErrorMessage } from '@/shared/utils/types';
import type {
  MenuItemCreateRequest,
  MenuItemUpdateRequest,
  MenuItemListParams,
} from '../types/menu';

// ========== Menu Item Queries ==========

/**
 * Hook to list menu items
 */
export const useMenuItems = (menuId: number, params?: MenuItemListParams) => {
  return useQuery({
    queryKey: [...menuKeys.items(menuId), params],
    queryFn: () => menuApi.listItems(menuId, params),
    enabled: !!menuId,
  });
};

// ========== Menu Item Mutations ==========

/**
 * Hook to add menu item
 */
export const useAddMenuItem = (menuId: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: MenuItemCreateRequest) => menuApi.addItem(menuId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: menuKeys.items(menuId) });
      queryClient.invalidateQueries({ queryKey: menuKeys.detail(menuId) });
      toast.success('Item added successfully');
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to add item'));
    },
  });
};

/**
 * Hook to update menu item
 */
export const useUpdateMenuItem = (menuId: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ itemId, data }: { itemId: number; data: MenuItemUpdateRequest }) =>
      menuApi.updateItem(menuId, itemId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: menuKeys.items(menuId) });
      queryClient.invalidateQueries({ queryKey: menuKeys.detail(menuId) });
      toast.success('Item updated successfully');
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to update item'));
    },
  });
};

/**
 * Hook to delete menu item
 */
export const useDeleteMenuItem = (menuId: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (itemId: number) => menuApi.deleteItem(menuId, itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: menuKeys.items(menuId) });
      queryClient.invalidateQueries({ queryKey: menuKeys.detail(menuId) });
      toast.success('Item deleted successfully');
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to delete item'));
    },
  });
};

// ========== Bulk Update Helper ==========

export type BulkUpdateStatus = 'idle' | 'saving' | 'success' | 'error';

export interface BulkUpdateProgress {
  id: number;
  status: BulkUpdateStatus;
}

export interface BulkUpdateResult {
  success: number;
  failed: number;
  errors: Array<{ id: number; error: string }>;
}

/**
 * Hook for bulk updating menu items
 * Uses sequential PATCH calls with progress tracking
 */
export const useBulkUpdateMenuItems = (menuId: number) => {
  const queryClient = useQueryClient();

  const bulkUpdate = async (
    items: Array<{ id: number; data: MenuItemUpdateRequest }>,
    onProgress?: (progress: BulkUpdateProgress) => void
  ): Promise<BulkUpdateResult> => {
    const results: BulkUpdateResult = {
      success: 0,
      failed: 0,
      errors: [],
    };

    for (const item of items) {
      onProgress?.({ id: item.id, status: 'saving' });

      try {
        await menuApi.updateItem(menuId, item.id, item.data);
        onProgress?.({ id: item.id, status: 'success' });
        results.success++;
      } catch (error) {
        onProgress?.({ id: item.id, status: 'error' });
        results.failed++;
        results.errors.push({
          id: item.id,
          error: getApiErrorMessage(error, 'Update failed'),
        });
      }
    }

    // Invalidate queries after all updates
    await queryClient.invalidateQueries({ queryKey: menuKeys.items(menuId) });
    await queryClient.invalidateQueries({ queryKey: menuKeys.detail(menuId) });

    // Show summary toast
    if (results.failed === 0) {
      toast.success(`Successfully updated ${results.success} items`);
    } else if (results.success === 0) {
      toast.error(`Failed to update all ${results.failed} items`);
    } else {
      toast.warning(
        `Updated ${results.success} items, ${results.failed} failed`
      );
    }

    return results;
  };

  return { bulkUpdate };
};
