/**
 * Audit Logs Hooks
 *
 * LAYER 2: APPLICATION
 * React Query hooks for audit log operations
 */

import { useQuery } from '@tanstack/react-query';
import { auditApi } from '../services/auditApi';
import type { AuditLogFilters } from '../types/auditLog';

export const AUDIT_LOGS_QUERY_KEY = 'auditLogs';

/**
 * Hook to fetch audit logs with filters
 */
export function useAuditLogs(filters?: AuditLogFilters) {
  return useQuery({
    queryKey: [AUDIT_LOGS_QUERY_KEY, filters],
    queryFn: () => auditApi.getAuditLogs(filters),
    staleTime: 30000, // 30 seconds
  });
}

/**
 * Hook to fetch single audit log by ID
 */
export function useAuditLog(id: number) {
  return useQuery({
    queryKey: [AUDIT_LOGS_QUERY_KEY, id],
    queryFn: () => auditApi.getAuditLog(id),
    enabled: !!id,
  });
}
