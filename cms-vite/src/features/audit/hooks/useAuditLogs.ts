/**
 * Audit Logs Hooks
 *
 * LAYER 2: APPLICATION
 * React Query hooks for audit log operations
 *
 * Uses organization-scoped query keys for proper cache isolation
 */

import { useQuery } from '@tanstack/react-query';
import { auditApi } from '../api/auditApi';
import { auditKeys, useSelectedOrgId } from '@/shared/hooks/useOrgQuery';
import type { AuditLogFilters } from '../types/auditLog';

// Legacy export for backwards compatibility
export const AUDIT_LOGS_QUERY_KEY = 'audit';

/**
 * Hook to fetch audit logs with filters
 *
 * Uses organization-scoped query key for proper cache isolation
 * between organizations.
 */
export function useAuditLogs(filters?: AuditLogFilters) {
  const orgId = useSelectedOrgId();

  return useQuery({
    queryKey: auditKeys.list(orgId, filters),
    queryFn: () => auditApi.getAuditLogs(filters),
    staleTime: 30000, // 30 seconds
    enabled: !!orgId, // Only fetch when org is selected
  });
}

/**
 * Hook to fetch single audit log by ID
 *
 * Note: Audit log ID is unique across organizations,
 * but we still need orgId context for permission checks
 */
export function useAuditLog(id: number) {
  const orgId = useSelectedOrgId();

  return useQuery({
    queryKey: ['audit', 'detail', id],
    queryFn: () => auditApi.getAuditLog(id),
    enabled: !!id && !!orgId,
  });
}
