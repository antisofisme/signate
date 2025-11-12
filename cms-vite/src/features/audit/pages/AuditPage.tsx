/**
 * Audit Logs Page
 *
 * LAYER 1: PRESENTATION
 * Main page for audit logs - orchestration only
 */

import { useState } from 'react';
import { Filter } from 'lucide-react';
import { useAuditLogs } from '../hooks/useAuditLogs';
import { useUsers } from '@/features/users/hooks/useUsers';
import { useOrganizations } from '@/features/organizations/hooks/useOrganizations';
import { AuditLogFilters } from '../components/AuditLogFilters';
import { AuditLogTable } from '../components/AuditLogTable';
import { AuditLogStats } from '../components/AuditLogStats';
import type { AuditLogFilters as Filters } from '../types/auditLog';

export default function AuditPage() {
  const [filters, setFilters] = useState<Filters>({
    page: 1,
    per_page: 20,
  });
  const [showFilters, setShowFilters] = useState(true);

  // Queries
  const { data, isLoading } = useAuditLogs(filters);
  const { data: usersData } = useUsers({});
  const { data: orgsData } = useOrganizations(true);

  const handlePageChange = (newPage: number) => {
    setFilters({ ...filters, page: newPage });
  };

  const handleClearFilters = () => {
    setFilters({ page: 1, per_page: 20 });
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
          {showFilters ? 'Hide Filters' : 'Show Filters'}
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
