/**
 * React Query Hooks for Menu Categories Management
 * Per-menu categories attached to specific menu
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { menuApi } from '../api/menuApi';
import { menuKeys } from './useMenus';
import { getApiErrorMessage } from '@/shared/utils/types';
import type {
  MenuCategoryCreateRequest,
  MenuCategoryUpdateRequest,
  MenuCategoryReorderRequest,
} from '../types/menu';

// Query Keys for categories
export const categoryKeys = {
  all: (menuId: number) => [...menuKeys.detail(menuId), 'categories'] as const,
};

// ========== Category Queries ==========

/**
 * Hook to list categories for a menu
 */
export const useMenuCategories = (menuId: number, enabled: boolean = true) => {
  return useQuery({
    queryKey: categoryKeys.all(menuId),
    queryFn: () => menuApi.listCategories(menuId),
    enabled: enabled && !!menuId,
  });
};

// ========== Category Mutations ==========

/**
 * Hook to create a category for a menu
 */
export const useCreateMenuCategory = (menuId: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: MenuCategoryCreateRequest) => menuApi.createCategory(menuId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: categoryKeys.all(menuId) });
      toast.success('Category created successfully');
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to create category'));
    },
  });
};

/**
 * Hook to update a category
 */
export const useUpdateMenuCategory = (menuId: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ categoryId, data }: { categoryId: number; data: MenuCategoryUpdateRequest }) =>
      menuApi.updateCategory(menuId, categoryId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: categoryKeys.all(menuId) });
      toast.success('Category updated successfully');
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to update category'));
    },
  });
};

/**
 * Hook to delete a category
 */
export const useDeleteMenuCategory = (menuId: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (categoryId: number) => menuApi.deleteCategory(menuId, categoryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: categoryKeys.all(menuId) });
      toast.success('Category deleted successfully');
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to delete category'));
    },
  });
};

/**
 * Hook to reorder categories
 */
export const useReorderMenuCategories = (menuId: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: MenuCategoryReorderRequest) => menuApi.reorderCategories(menuId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: categoryKeys.all(menuId) });
      toast.success('Categories reordered successfully');
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to reorder categories'));
    },
  });
};
