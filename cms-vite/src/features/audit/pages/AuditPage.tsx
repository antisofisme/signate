/**
 * Audit Logs Page
 *
 * LAYER 1: PRESENTATION
 * Main page for audit logs - orchestration only
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Filter } from 'lucide-react';
import { useAuditLogs } from '../hooks/useAuditLogs';
import { useUsers } from '@/features/users/hooks/useUsers';
import { useOrganizations } from '@/features/organizations/hooks/useOrganizations';
import { AuditLogFilters } from '../components/AuditLogFilters';
import { AuditLogTable } from '../components/AuditLogTable';
import { AuditLogStats } from '../components/AuditLogStats';
import type { AuditLogFilters as Filters } from '../types/auditLog';
import { usePagination } from '@/shared/hooks';

export default function AuditPage() {
  const { t } = useTranslation();

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
  const { data: orgsData } = useOrganizations(true);

  // Handle page change - convert 1-indexed from table to 0-indexed for hook
  const handlePageChange = (newPage: number) => {
    pagination.goToPage(newPage - 1);
  };

  const handleClearFilters = () => {
    setFilters({});
    pagination.resetPage();
  };

  return (
    <div className="space-y-6">
      {/* Filter Toggle */}
      <div className="flex justify-end">
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
        >
          <Filter className="w-5 h-5" />
          {showFilters ? t('audit.hideFilters') : t('audit.showFilters')}
        </button>
      </div>

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

      {/* Stats */}
      {data && <AuditLogStats total={data.total} />}

      {/* Table */}
      <AuditLogTable
        logs={data?.logs || []}
        isLoading={isLoading}
        currentPage={data?.page || 1}
        totalPages={data?.total_pages || 1}
        perPage={data?.per_page || 20}
        total={data?.total || 0}
        onPageChange={handlePageChange}
      />
    </div>
  );
}
