/**
 * React Query Hooks for Menu Media Management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from '@/shared/utils/toast';
import { menuApi } from '../api/menuApi';
import { getApiErrorMessage } from '@/shared/utils/types';
import { useSelectedOrgId } from '@/shared/hooks/useOrgQuery';
import { useAuthStore } from '@/lib/stores/authStore';
import type { MenuMediaFilters } from '../types/menu';

// Query keys
export const menuMediaKeys = {
  all: ['menu-media'] as const,
  lists: (orgId?: number) => [...menuMediaKeys.all, 'list', orgId] as const,
  list: (orgId?: number, filters?: MenuMediaFilters) => [...menuMediaKeys.lists(orgId), filters] as const,
  deletedLists: (orgId?: number) => [...menuMediaKeys.all, 'deleted', orgId] as const,
  deleted: (orgId?: number, filters?: MenuMediaFilters) => [...menuMediaKeys.deletedLists(orgId), filters] as const,
  detail: (id: number) => [...menuMediaKeys.all, 'detail', id] as const,
  duplicates: (orgId?: number) => [...menuMediaKeys.all, 'duplicates', orgId] as const,
};

/**
 * Hook to list menu media with filters and pagination
 */
export const useMenuMediaList = (filters?: MenuMediaFilters) => {
  const orgId = useSelectedOrgId();
  const hasHydrated = useAuthStore((state) => state._hasHydrated);

  return useQuery({
    queryKey: menuMediaKeys.list(orgId, filters),
    queryFn: () => menuApi.listMedia(filters),
    staleTime: 0,
    gcTime: 0,
    refetchOnMount: true,
    enabled: hasHydrated && !!orgId,
  });
};

/**
 * Hook to list deleted menu media (Recycle Bin)
 */
export const useDeletedMenuMediaList = (filters?: MenuMediaFilters) => {
  const orgId = useSelectedOrgId();
  const hasHydrated = useAuthStore((state) => state._hasHydrated);

  return useQuery({
    queryKey: menuMediaKeys.deleted(orgId, filters),
    queryFn: () => menuApi.listDeletedMedia(filters),
    staleTime: 0,
    gcTime: 0,
    refetchOnMount: true,
    enabled: hasHydrated && !!orgId,
  });
};

/**
 * Hook to upload menu media
 */
export const useUploadMenuMedia = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ file, title, altText }: { file: File; title?: string; altText?: string }) =>
      menuApi.uploadMedia(file, title, altText),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: menuMediaKeys.all });
      toast.success('Image uploaded successfully');
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to upload image'));
    },
  });
};

/**
 * Hook to update menu media
 */
export const useUpdateMenuMedia = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: { title?: string; alt_text?: string } }) =>
      menuApi.updateMedia(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: menuMediaKeys.all });
      toast.success('Image updated successfully');
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to update image'));
    },
  });
};

/**
 * Hook to delete menu media (soft delete - move to recycle bin)
 */
export const useDeleteMenuMedia = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => menuApi.deleteMedia(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: menuMediaKeys.all });
      toast.success('Image moved to recycle bin');
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to delete image'));
    },
  });
};

/**
 * Hook to restore menu media from recycle bin
 */
export const useRestoreMenuMedia = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => menuApi.restoreMedia(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: menuMediaKeys.all });
      toast.success('Image restored successfully');
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to restore image'));
    },
  });
};

/**
 * Hook to permanently delete menu media
 */
export const usePermanentDeleteMenuMedia = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => menuApi.permanentDeleteMedia(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: menuMediaKeys.all });
      toast.success('Image permanently deleted');
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to permanently delete image'));
    },
  });
};

/**
 * Hook to bulk permanent delete menu media
 */
export const useBulkPermanentDeleteMenuMedia = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (ids: number[]) => menuApi.bulkPermanentDeleteMedia(ids),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: menuMediaKeys.all });
      toast.success(`${data.deleted_count} images permanently deleted`);
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to delete images'));
    },
  });
};

/**
 * Hook to get duplicate menu media (files with same hash)
 */
export const useDuplicateMenuMedia = () => {
  const orgId = useSelectedOrgId();
  const hasHydrated = useAuthStore((state) => state._hasHydrated);

  return useQuery({
    queryKey: menuMediaKeys.duplicates(orgId),
    queryFn: () => menuApi.getDuplicateMedia(),
    staleTime: 30000, // 30 seconds
    enabled: hasHydrated && !!orgId,
  });
};

// Legacy hook for backward compatibility
export const useMenuMedia = useMenuMediaList;

// ========== Menu Item Media Hooks ==========

import { menuKeys } from './useMenus';
import type { MenuItemMediaBulkSetRequest } from '../types/menu';

/**
 * Hook to fetch media for a specific menu item
 */
export const useItemMedia = (menuId: number, itemId: number | null) => {
  return useQuery({
    queryKey: [...menuKeys.items(menuId), 'media', itemId],
    queryFn: () => menuApi.listItemMedia(menuId, itemId!),
    enabled: !!menuId && !!itemId,
    staleTime: 0,
  });
};

/**
 * Hook to bulk set media for a menu item (replaces all existing)
 */
export const useBulkSetItemMedia = (menuId: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ itemId, data }: { itemId: number; data: MenuItemMediaBulkSetRequest }) =>
      menuApi.bulkSetItemMedia(menuId, itemId, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: menuKeys.items(menuId) });
      queryClient.invalidateQueries({ queryKey: [...menuKeys.items(menuId), 'media', variables.itemId] });
      // Don't show toast here - let the parent handle it
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to update images'));
    },
  });
};
