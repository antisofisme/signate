/**
 * Audit Log Stats Component
 * Display total audit logs count
 */

import { FileText } from 'lucide-react';

interface AuditLogStatsProps {
  total: number;
}

export function AuditLogStats({ total }: AuditLogStatsProps) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div className="flex items-center gap-3">
        <FileText className="w-8 h-8 text-blue-600 dark:text-blue-400" />
        <div>
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
            Total Audit Logs
          </h3>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
            {total.toLocaleString()}
          </p>
        </div>
      </div>
    </div>
  );
}

export default AuditLogStats;
