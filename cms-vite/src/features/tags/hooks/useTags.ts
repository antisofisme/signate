/**
 * Tags Hooks
 *
 * LAYER 2: BUSINESS LOGIC
 * React Query hooks for tag management
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { tagsApi } from '@/features/tags/services/tagsApi';
import { handleAPIError } from '@/lib/errors/errorHandler';
import { toast } from '@/lib/notifications/toast';
import type {
  CreateTagRequest,
  UpdateTagRequest,
  TagListFilters,
} from '../types/tag';

/**
 * Get all tags with optional sorting
 */
export function useTags(filters?: TagListFilters) {
  return useQuery({
    queryKey: ['tags', filters],
    queryFn: () => tagsApi.list(filters),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

/**
 * Get single tag
 */
export function useTag(id: number) {
  return useQuery({
    queryKey: ['tags', id],
    queryFn: () => tagsApi.get(id),
    staleTime: 2 * 60 * 1000, // 2 minutes
    enabled: !!id,
  });
}

/**
 * Get tag with usage statistics
 */
export function useTagUsage(id: number) {
  return useQuery({
    queryKey: ['tags', id, 'usage'],
    queryFn: () => tagsApi.getUsage(id),
    staleTime: 1 * 60 * 1000, // 1 minute
    enabled: !!id,
  });
}

/**
 * Create tag mutation
 */
export function useCreateTag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (tagData: CreateTagRequest) => tagsApi.create(tagData),
    onSuccess: (data) => {
      // Invalidate tag list
      queryClient.invalidateQueries({ queryKey: ['tags'] });

      // Show success toast
      toast.success(`Tag "${data.tag_name}" berhasil dibuat`);
    },
    onError: (error) => {
      const appError = handleAPIError(error);
      toast.error(appError.message);
    },
  });
}

/**
 * Update tag mutation
 */
export function useUpdateTag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateTagRequest }) =>
      tagsApi.update(id, data),
    onSuccess: (data, variables) => {
      // Invalidate queries
      queryClient.invalidateQueries({ queryKey: ['tags'] });
      queryClient.invalidateQueries({ queryKey: ['tags', variables.id] });

      // Show success toast
      toast.success(`Tag "${data.tag_name}" berhasil diupdate`);
    },
    onError: (error) => {
      const appError = handleAPIError(error);
      toast.error(appError.message);
    },
  });
}

/**
 * Delete tag mutation
 */
export function useDeleteTag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, force }: { id: number; force?: boolean }) =>
      tagsApi.delete(id, force),
    onSuccess: (_, variables) => {
      // Invalidate queries
      queryClient.invalidateQueries({ queryKey: ['tags'] });
      queryClient.removeQueries({ queryKey: ['tags', variables.id] });

      // Show success toast
      toast.success('Tag berhasil dihapus');
    },
    onError: (error) => {
      const appError = handleAPIError(error);
      toast.error(appError.message);
    },
  });
}
