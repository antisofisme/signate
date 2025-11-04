/**
 * Organizations Hooks
 *
 * LAYER 2: BUSINESS LOGIC
 * React Query hooks for organization management
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { organizationsApi } from '@/features/organizations/services/organizationsApi';
import { handleAPIError } from '@/lib/errors/errorHandler';
import { toast } from '@/lib/notifications/toast';
import type {
  CreateOrganizationRequest,
  UpdateOrganizationRequest,
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

      // Show success toast with PIN
      toast.success(
        `Organization "${data.name}" berhasil dibuat dengan PIN: ${data.organization_pin}`
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

      // Show success toast
      toast.success('Organization berhasil dihapus');
    },
    onError: (error) => {
      const appError = handleAPIError(error);
      toast.error(appError.message);
    },
  });
}
