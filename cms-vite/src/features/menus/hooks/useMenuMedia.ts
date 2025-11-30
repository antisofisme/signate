/**
 * React Query Hooks for Menu Media Management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { menuApi } from '../api/menuApi';
import { getApiErrorMessage } from '@/shared/utils/types';
import { useSelectedOrgId } from '@/shared/hooks/useOrgQuery';

// Query keys
export const menuMediaKeys = {
  all: ['menu-media'] as const,
  list: (orgId?: number) => [...menuMediaKeys.all, 'list', orgId] as const,
  detail: (id: number) => [...menuMediaKeys.all, 'detail', id] as const,
};

/**
 * Hook to list menu media
 */
export const useMenuMedia = () => {
  const orgId = useSelectedOrgId();

  return useQuery({
    queryKey: menuMediaKeys.list(orgId),
    queryFn: () => menuApi.listMedia(),
  });
};

/**
 * Hook to upload menu media
 */
export const useUploadMenuMedia = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => menuApi.uploadMedia(file),
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
 * Hook to delete menu media
 */
export const useDeleteMenuMedia = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => menuApi.deleteMedia(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: menuMediaKeys.all });
      toast.success('Image deleted successfully');
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to delete image'));
    },
  });
};
