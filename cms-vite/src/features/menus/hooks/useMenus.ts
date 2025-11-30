/**
 * React Query Hooks for Menu Management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { menuApi } from '../api/menuApi';
import { getApiErrorMessage } from '@/shared/utils/types';
import type {
  MenuCreateRequest,
  MenuUpdateRequest,
  MenuListParams,
} from '../types/menu';

// Query Keys
export const menuKeys = {
  all: ['menus'] as const,
  lists: () => [...menuKeys.all, 'list'] as const,
  list: (params?: MenuListParams) => [...menuKeys.lists(), params] as const,
  details: () => [...menuKeys.all, 'detail'] as const,
  detail: (id: number) => [...menuKeys.details(), id] as const,
  items: (menuId: number) => [...menuKeys.detail(menuId), 'items'] as const,
  importHistory: (menuId: number) => [...menuKeys.detail(menuId), 'import-history'] as const,
};

// ========== Menu Queries ==========

/**
 * Hook to list menus
 */
export const useMenus = (params?: MenuListParams) => {
  return useQuery({
    queryKey: menuKeys.list(params),
    queryFn: () => menuApi.list(params),
  });
};

/**
 * Hook to get single menu
 */
export const useMenu = (id: number, enabled: boolean = true) => {
  return useQuery({
    queryKey: menuKeys.detail(id),
    queryFn: () => menuApi.get(id),
    enabled: enabled && !!id,
  });
};

// ========== Menu Mutations ==========

/**
 * Hook to create menu
 */
export const useCreateMenu = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: MenuCreateRequest) => menuApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: menuKeys.lists() });
      toast.success('Menu created successfully');
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to create menu'));
    },
  });
};

/**
 * Hook to update menu
 */
export const useUpdateMenu = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: MenuUpdateRequest }) =>
      menuApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: menuKeys.lists() });
      queryClient.invalidateQueries({ queryKey: menuKeys.detail(variables.id) });
      toast.success('Menu updated successfully');
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to update menu'));
    },
  });
};

/**
 * Hook to delete menu
 */
export const useDeleteMenu = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => menuApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: menuKeys.lists() });
      toast.success('Menu deleted successfully');
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to delete menu'));
    },
  });
};

/**
 * Hook to delete menu with PIN verification
 * Note: PIN verification is done separately in the modal, this just deletes after verification
 */
export const useDeleteMenuWithPIN = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => menuApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: menuKeys.lists() });
      toast.success('Menu deleted successfully');
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to delete menu'));
    },
  });
};

/**
 * Hook to regenerate QR code
 */
export const useRegenerateQRCode = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (menuId: number) => menuApi.regenerateQRCode(menuId),
    onSuccess: (_, menuId) => {
      queryClient.invalidateQueries({ queryKey: menuKeys.detail(menuId) });
      toast.success('QR code regenerated successfully');
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to regenerate QR code'));
    },
  });
};
