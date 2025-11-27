/**
 * React Query Hooks for Menu Items Management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
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
