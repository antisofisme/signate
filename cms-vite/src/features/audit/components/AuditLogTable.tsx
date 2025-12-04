/**
 * Audit Log Table Component
 * Table display of audit logs with pagination and detail modal
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ChevronLeft, ChevronRight, FileText, Eye } from 'lucide-react';
import { format } from 'date-fns';
import { TABLE_STYLES } from '@/shared/components';
import type { AuditLog } from '../types/auditLog';
import { AuditDetailModal } from './AuditDetailModal';
import { generateActionSummary } from '../utils/auditFormatter';

interface AuditLogTableProps {
  logs: AuditLog[];
  isLoading: boolean;
  currentPage: number;
  totalPages: number;
  perPage: number;
  total: number;
  onPageChange: (page: number) => void;
}

export function AuditLogTable({
  logs,
  isLoading,
  currentPage,
  totalPages,
  perPage,
  total,
  onPageChange,
}: AuditLogTableProps) {
  const { t } = useTranslation();
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);

  const handleViewDetail = (log: AuditLog) => {
    setSelectedLog(log);
    setIsDetailModalOpen(true);
  };

  const handleCloseDetail = () => {
    setIsDetailModalOpen(false);
    setSelectedLog(null);
  };

  const getActionBadgeColor = (action: string) => {
    if (action.includes('create')) return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
    if (action.includes('update')) return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
    if (action.includes('delete')) return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
    if (action.includes('login')) return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
    return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
  };

  const getResourceBadgeColor = (resourceType: string) => {
    const colors: Record<string, string> = {
      user: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      organization: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
      device: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      content: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
      auth: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200',
    };
    return colors[resourceType] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
  };

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <div className="p-12 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">{t('audit.loadingLogs')}</p>
        </div>
      </div>
    );
  }

  if (logs.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <div className="p-12 text-center">
          <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">
            {t('audit.noLogsFound')}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={TABLE_STYLES.container}>
      <div className="overflow-x-auto">
        <table className={TABLE_STYLES.table}>
          <thead className={TABLE_STYLES.thead}>
            <tr>
              <th className={TABLE_STYLES.th}>
                {t('audit.table.timestamp')}
              </th>
              <th className={TABLE_STYLES.th}>
                {t('audit.table.user')}
              </th>
              <th className={TABLE_STYLES.th}>
                {t('audit.table.action')}
              </th>
              <th className={TABLE_STYLES.th}>
                {t('audit.table.resource')}
              </th>
              <th className={TABLE_STYLES.th}>
                {t('audit.table.details')}
              </th>
              <th className={TABLE_STYLES.th}>
                {t('audit.table.ipAddress')}
              </th>
            </tr>
          </thead>
          <tbody className={TABLE_STYLES.tbody}>
            {logs.map((log) => (
              <tr key={log.id} className={TABLE_STYLES.tr}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900 dark:text-white">
                    {format(new Date(log.created_at), 'MMM dd, yyyy')}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {format(new Date(log.created_at), 'HH:mm:ss')}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900 dark:text-white">
                    {log.username || t('audit.system')}
                  </div>
                  {log.organization_name && (
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {log.organization_name}
                    </div>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getActionBadgeColor(log.action)}`}>
                    {log.action}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getResourceBadgeColor(log.resource_type)}`}>
                    {log.resource_type}
                  </span>
                  {log.resource_id && (
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {t('audit.table.id')}: {log.resource_id}
                    </div>
                  )}
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm text-gray-600 dark:text-gray-300 max-w-xs">
                    <p className="truncate">{generateActionSummary(log)}</p>
                    {log.details && (
                      <button
                        onClick={() => handleViewDetail(log)}
                        className="mt-1 text-xs text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
                      >
                        <Eye className="w-3 h-3" />
                        {t('audit.viewDetails', 'View details')}
                      </button>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-300">
                  {log.ip_address || '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Detail Modal */}
      <AuditDetailModal
        log={selectedLog}
        isOpen={isDetailModalOpen}
        onClose={handleCloseDetail}
      />

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="bg-gray-50 dark:bg-gray-700 px-6 py-4 flex items-center justify-between border-t border-gray-200 dark:border-gray-600">
          <div className="text-sm text-gray-700 dark:text-gray-300">
            {t('audit.pagination.showing', {
              from: ((currentPage - 1) * perPage) + 1,
              to: Math.min(currentPage * perPage, total),
              total: total
            })}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => onPageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <div className="flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-300">
              {t('audit.pagination.page', { current: currentPage, total: totalPages })}
            </div>
            <button
              onClick={() => onPageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default AuditLogTable;
