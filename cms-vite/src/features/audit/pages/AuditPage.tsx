/**
 * Audit Logs Page
 *
 * LAYER 1: PRESENTATION
 * Main page for audit logs - orchestration only
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Filter, FileText } from 'lucide-react';
import { useAuditLogs } from '../hooks/useAuditLogs';
import { useUsers } from '@/features/users/hooks/useUsers';
import { useOrganizations } from '@/features/organizations/hooks/useOrganizations';
import { AuditLogFilters } from '../components/AuditLogFilters';
import { AuditLogTable } from '../components/AuditLogTable';
import { AuditLogStats } from '../components/AuditLogStats';
import type { AuditLogFilters as Filters } from '../types/auditLog';
import { usePagination } from '@/shared/hooks';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import {
  Button,
  PageSkeleton,
  AccessDenied,
  EmptyState,
  PageHeader,
  PageStats,
  PageToolbar,
} from '@/shared/components';

export default function AuditPage() {
  const { t } = useTranslation();

  // Permission check
  const { hasPermission: canView, isLoading: isCheckingPermission } = useCanPerformAction('audit_logs', 'read');

  // Standardized pagination hook
  const pagination = usePagination({ pageSize: 20 });

  const [filters, setFilters] = useState<Omit<Filters, 'page' | 'per_page'>>({});
  const [showFilters, setShowFilters] = useState(true);

  // Queries - convert 0-indexed to 1-indexed for API
  const { data, isLoading } = useAuditLogs({
    ...filters,
    page: pagination.currentPage + 1,
    per_page: pagination.pageSize,
  });
  const { data: usersData } = useUsers({});
  const { data: orgsData } = useOrganizations({ active_only: true });

  // Handle page change - convert 1-indexed from table to 0-indexed for hook
  const handlePageChange = (newPage: number) => {
    pagination.goToPage(newPage - 1);
  };

  const handleClearFilters = () => {
    setFilters({});
    pagination.resetPage();
  };

  // Loading state for permission check
  if (isCheckingPermission) {
    return <PageSkeleton />;
  }

  // Access denied state
  if (!canView) {
    return <AccessDenied />;
  }

  // Empty state when no logs
  const hasNoLogs = !isLoading && data && data.logs.length === 0;

  return (
    <>
      {/* Page Header */}
      <PageHeader
        title={t('audit.title', 'Audit Logs')}
        description={t('audit.subtitle', 'Track system activity and changes')}
      />

      {/* ROW 1: Stats */}
      {data && data.total > 0 && (
        <PageStats
          total={data.total}
          totalLabel="logs"
        />
      )}

      {/* ROW 2: Toolbar */}
      <PageToolbar>
        <PageToolbar.Left>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {t('audit.description', 'View all system activities')}
          </span>
        </PageToolbar.Left>
        <PageToolbar.Right>
          <Button
            variant="secondary"
            onClick={() => setShowFilters(!showFilters)}
            leftIcon={<Filter className="w-4 h-4" />}
          >
            {showFilters ? t('audit.hideFilters') : t('audit.showFilters')}
          </Button>
        </PageToolbar.Right>
      </PageToolbar>

      {/* Filters */}
      {showFilters && (
        <AuditLogFilters
          filters={filters}
          users={usersData?.users || []}
          organizations={orgsData?.organizations || []}
          onFilterChange={setFilters}
          onClearFilters={handleClearFilters}
        />
      )}

      {/* Empty State */}
      {hasNoLogs ? (
        <EmptyState
          icon={FileText}
          title={t('audit.noLogsFound', 'No audit logs found')}
          description={t('audit.noLogsFound', 'No activity has been recorded yet')}
        />
      ) : (
        /* Table */
        <AuditLogTable
          logs={data?.logs || []}
          isLoading={isLoading}
          currentPage={data?.page || 1}
          totalPages={data?.total_pages || 1}
          perPage={data?.per_page || 20}
          total={data?.total || 0}
          onPageChange={handlePageChange}
        />
      )}
    </>
  );
}
