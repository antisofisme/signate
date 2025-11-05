/**
 * Audit Logs API Service
 *
 * LAYER 2: INFRASTRUCTURE
 * HTTP client for audit log endpoints
 */

import { apiClient } from '@/lib/api/client';
import type { AuditLog, AuditLogListResponse, AuditLogFilters } from '../types/auditLog';

export const auditApi = {
  /**
   * Get audit logs with filters and pagination
   */
  getAuditLogs: async (filters?: AuditLogFilters): Promise<AuditLogListResponse> => {
    const params = new URLSearchParams();

    if (filters?.user_id) params.append('user_id', filters.user_id.toString());
    if (filters?.organization_id) params.append('organization_id', filters.organization_id.toString());
    if (filters?.action) params.append('action', filters.action);
    if (filters?.resource_type) params.append('resource_type', filters.resource_type);
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);

    // Convert page/per_page to limit/offset for backend
    const page = filters?.page || 1;
    const per_page = filters?.per_page || 20;
    params.append('limit', per_page.toString());
    params.append('offset', ((page - 1) * per_page).toString());

    const queryString = params.toString();
    const url = `/audit-logs${queryString ? `?${queryString}` : ''}`;

    const { data } = await apiClient.get<AuditLogListResponse>(url);
    return data;
  },

  /**
   * Get single audit log by ID
   */
  getAuditLog: async (id: number): Promise<AuditLog> => {
    const { data } = await apiClient.get<AuditLog>(`/audit-logs/${id}`);
    return data;
  },
};
