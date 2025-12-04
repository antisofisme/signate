/**
 * Organization Quota Hooks
 *
 * LAYER 2: BUSINESS LOGIC
 * React Query hooks for quota management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from '@/shared/utils/toast';
import { getApiErrorMessage } from '@/shared/utils/types';
import { organizationsApi } from '../api/organizationsApi';
import type { UpdateQuotaRequest } from '../types/organization';

// Query keys - IMPORTANT: Don't include dynamic values like fileSize in keys!
export const quotaKeys = {
  all: ['organization-quota'] as const,
  detail: (orgId: number) => [...quotaKeys.all, orgId] as const,
  check: {
    device: (orgId: number) => [...quotaKeys.all, orgId, 'check-device'] as const,
    user: (orgId: number) => [...quotaKeys.all, orgId, 'check-user'] as const,
    // FIXED: Don't include fileSize in key to avoid cache fragmentation
    content: (orgId: number) => [...quotaKeys.all, orgId, 'check-content'] as const,
  },
};

/**
 * Hook to fetch organization quota
 * Uses long staleTime since quota rarely changes
 */
export function useOrganizationQuota(orgId: number | undefined) {
  return useQuery({
    queryKey: orgId ? quotaKeys.detail(orgId) : ['no-org'],
    queryFn: () => organizationsApi.getQuota(orgId!),
    enabled: !!orgId,
    staleTime: 5 * 60 * 1000, // 5 minutes - quota rarely changes
    // REMOVED refetchInterval - unnecessary background polling
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
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to update quota'));
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
 * FIXED: Uses cached organization quota to calculate available space client-side
 * instead of API call per file size change (prevents cache fragmentation)
 */
export function useCheckContentQuota(orgId: number | undefined, fileSizeBytes: number) {
  // Get organization quota (cached)
  const { data: quotaData, isLoading } = useOrganizationQuota(orgId);

  // Convert GB to bytes for comparison
  const GB_TO_BYTES = 1024 * 1024 * 1024;
  // quotaData is OrganizationQuota directly (not wrapped in SuccessResponse)
  const contentQuota = quotaData?.content;

  // Calculate quota check locally instead of API call per file size change
  const maxSizeBytes = contentQuota?.max_size_gb != null
    ? contentQuota.max_size_gb * GB_TO_BYTES
    : Infinity;
  const usedSizeBytes = contentQuota?.current_size_gb != null
    ? contentQuota.current_size_gb * GB_TO_BYTES
    : 0;
  const availableSizeBytes = contentQuota?.available_size_gb != null
    ? contentQuota.available_size_gb * GB_TO_BYTES
    : Infinity;

  // Check if upload would exceed quota
  const canUpload = isFinite(maxSizeBytes)
    ? usedSizeBytes + fileSizeBytes <= maxSizeBytes
    : true; // Allow if no quota set

  return {
    data: {
      allowed: canUpload,  // Match QuotaCheckResult interface
      can_add: canUpload,
      current: usedSizeBytes,
      current_used: usedSizeBytes,
      max: maxSizeBytes,
      limit: maxSizeBytes,
      available: availableSizeBytes,
      remaining: availableSizeBytes,
      requested_size: fileSizeBytes,
      reason: canUpload ? undefined : `File size (${formatBytes(fileSizeBytes)}) exceeds remaining quota (${formatBytes(availableSizeBytes)})`,
    },
    isLoading,
    isError: false,
  };
}

// Helper to format bytes
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  if (!isFinite(bytes)) return 'Unlimited';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
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
