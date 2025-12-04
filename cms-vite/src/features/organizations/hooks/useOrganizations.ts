/**
 * Organizations Hooks
 *
 * LAYER 2: BUSINESS LOGIC
 * React Query hooks for organization management
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { organizationsApi } from '@/features/organizations/api/organizationsApi';
import { handleAPIError } from '@/lib/errors/errorHandler';
import { toast } from '@/shared/utils/toast';
import type {
  CreateOrganizationRequest,
  UpdateOrganizationRequest,
  UpdatePinRequest,
} from '../types/organization';

/**
 * Get all organizations
 */
export function useOrganizations(activeOnly = false) {
  return useQuery({
    queryKey: ['organizations', { activeOnly }],
    queryFn: () => organizationsApi.list(activeOnly),
    staleTime: 1 * 60 * 1000, // 1 minute
  });
}

/**
 * Get single organization
 */
export function useOrganization(id: number) {
  return useQuery({
    queryKey: ['organizations', id],
    queryFn: () => organizationsApi.get(id),
    staleTime: 2 * 60 * 1000, // 2 minutes
    enabled: !!id,
  });
}

/**
 * Create organization mutation
 */
export function useCreateOrganization() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (orgData: CreateOrganizationRequest) =>
      organizationsApi.create(orgData),
    onSuccess: (data) => {
      // Invalidate organization list
      queryClient.invalidateQueries({ queryKey: ['organizations'] });

      // Invalidate dashboard (organization count changes)
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });

      // REMOVED: Organization PIN from toast message (No-PIN flow)
      toast.success(
        `Organization "${data.name}" berhasil dibuat`
      );
    },
    onError: (error) => {
      const appError = handleAPIError(error);
      toast.error(appError.message);
    },
  });
}

/**
 * Update organization mutation
 */
export function useUpdateOrganization() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: number;
      data: UpdateOrganizationRequest;
    }) => organizationsApi.update(id, data),
    onSuccess: (data, variables) => {
      // Invalidate queries
      queryClient.invalidateQueries({ queryKey: ['organizations'] });
      queryClient.invalidateQueries({
        queryKey: ['organizations', variables.id],
      });

      // Show success toast
      toast.success(`Organization "${data.name}" berhasil diupdate`);
    },
    onError: (error) => {
      const appError = handleAPIError(error);
      toast.error(appError.message);
    },
  });
}

/**
 * Delete organization mutation
 */
export function useDeleteOrganization() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => organizationsApi.delete(id),
    onSuccess: (_, id) => {
      // Invalidate queries
      queryClient.invalidateQueries({ queryKey: ['organizations'] });
      queryClient.removeQueries({ queryKey: ['organizations', id] });

      // Invalidate dashboard (organization count changes)
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });

      // Invalidate related entities (cascade delete may affect these)
      queryClient.invalidateQueries({ queryKey: ['users'] });
      queryClient.invalidateQueries({ queryKey: ['devices'] });
      queryClient.invalidateQueries({ queryKey: ['playlists'] });
      queryClient.invalidateQueries({ queryKey: ['content'] });
      queryClient.invalidateQueries({ queryKey: ['schedules'] });

      // Show success toast
      toast.success('Organization berhasil dihapus');
    },
    onError: (error) => {
      const appError = handleAPIError(error);
      toast.error(appError.message);
    },
  });
}

// =============================================================================
// PIN MANAGEMENT HOOKS
// =============================================================================

/**
 * Regenerate organization PIN mutation
 */
export function useRegeneratePin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (orgId: number) => organizationsApi.regeneratePin(orgId),
    onSuccess: (data) => {
      // Invalidate organization queries to refresh PIN
      queryClient.invalidateQueries({ queryKey: ['organizations'] });
      queryClient.invalidateQueries({
        queryKey: ['organizations', data.organization_id],
      });

      toast.success('PIN berhasil di-regenerate');
    },
    onError: (error) => {
      const appError = handleAPIError(error);
      toast.error(appError.message);
    },
  });
}

/**
 * Update organization PIN mutation
 */
export function useUpdatePin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ orgId, pinData }: { orgId: number; pinData: UpdatePinRequest }) =>
      organizationsApi.updatePin(orgId, pinData),
    onSuccess: (data) => {
      // Invalidate organization queries to refresh PIN
      queryClient.invalidateQueries({ queryKey: ['organizations'] });
      queryClient.invalidateQueries({
        queryKey: ['organizations', data.organization_id],
      });

      toast.success('PIN berhasil diupdate');
    },
    onError: (error) => {
      const appError = handleAPIError(error);
      toast.error(appError.message);
    },
  });
}
