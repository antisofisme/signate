/**
 * Organization Quota Hooks
 *
 * LAYER 2: BUSINESS LOGIC
 * React Query hooks for quota management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { organizationsApi } from '../api/organizationsApi';
import type { UpdateQuotaRequest } from '../types/organization';
import { toast } from 'sonner';

// Query keys
export const quotaKeys = {
  all: ['organization-quota'] as const,
  detail: (orgId: number) => [...quotaKeys.all, orgId] as const,
  check: {
    device: (orgId: number) => [...quotaKeys.all, orgId, 'check-device'] as const,
    user: (orgId: number) => [...quotaKeys.all, orgId, 'check-user'] as const,
    content: (orgId: number, fileSize: number) =>
      [...quotaKeys.all, orgId, 'check-content', fileSize] as const,
  },
};

/**
 * Hook to fetch organization quota
 * Auto-refetches every 30 seconds to keep quota status fresh
 */
export function useOrganizationQuota(orgId: number | undefined) {
  return useQuery({
    queryKey: orgId ? quotaKeys.detail(orgId) : ['no-org'],
    queryFn: () => organizationsApi.getQuota(orgId!),
    enabled: !!orgId,
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Refetch every minute
  });
}

/**
 * Hook to update organization quota limits
 * Admin only
 */
export function useUpdateQuota() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ orgId, data }: { orgId: number; data: UpdateQuotaRequest }) =>
      organizationsApi.updateQuota(orgId, data),
    onSuccess: (_, variables) => {
      // Invalidate quota queries
      queryClient.invalidateQueries({ queryKey: quotaKeys.detail(variables.orgId) });
      toast.success('Quota updated successfully');
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to update quota');
    },
  });
}

/**
 * Hook to check if organization can add more devices
 */
export function useCheckDeviceQuota(orgId: number | undefined) {
  return useQuery({
    queryKey: orgId ? quotaKeys.check.device(orgId) : ['no-org'],
    queryFn: () => organizationsApi.checkDeviceQuota(orgId!),
    enabled: !!orgId,
  });
}

/**
 * Hook to check if organization can add more users
 */
export function useCheckUserQuota(orgId: number | undefined) {
  return useQuery({
    queryKey: orgId ? quotaKeys.check.user(orgId) : ['no-org'],
    queryFn: () => organizationsApi.checkUserQuota(orgId!),
    enabled: !!orgId,
  });
}

/**
 * Hook to check if organization can add content with specified size
 */
export function useCheckContentQuota(orgId: number | undefined, fileSizeBytes: number) {
  return useQuery({
    queryKey: orgId ? quotaKeys.check.content(orgId, fileSizeBytes) : ['no-org'],
    queryFn: () => organizationsApi.checkContentQuota(orgId!, fileSizeBytes),
    enabled: !!orgId && fileSizeBytes > 0,
  });
}

/**
 * Helper hook to check quota warnings
 * Returns warning level based on percentage used
 */
export function useQuotaWarningLevel(percentageUsed: number) {
  if (percentageUsed >= 95) return 'critical'; // Red
  if (percentageUsed >= 80) return 'warning'; // Orange
  if (percentageUsed >= 60) return 'info'; // Yellow
  return 'normal'; // Green
}
