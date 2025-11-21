/**
 * Device Logs Viewer Component
 *
 * Comprehensive console logs viewer with:
 * - Tabbed interface (Console Logs / Connection Logs)
 * - Filter controls (log level, auto-refresh)
 * - Pagination
 * - Log detail modal
 * - Clear logs functionality
 */

import { useState } from 'react';
import {
  Terminal,
  RefreshCw,
  Trash2,
  AlertCircle,
  Info,
  AlertTriangle,
  Bug,
  Eye,
  Network,
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { useDeviceLogs, useClearLogs } from '../hooks/useDeviceLogs';
import { LogDetailModal } from './LogDetailModal';
import type { DeviceLog, LogLevel } from '../types/logs';
import { LOG_LEVEL_OPTIONS, LOG_LEVEL_COLORS } from '../types/logs';
import { toast } from 'sonner';

interface DeviceLogsViewerProps {
  deviceId: number;
  deviceName?: string;
}

export function DeviceLogsViewer({ deviceId, deviceName }: DeviceLogsViewerProps) {
  // State
  const [selectedLog, setSelectedLog] = useState<DeviceLog | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [logLevel, setLogLevel] = useState<LogLevel | 'all'>('all');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [currentPage, setCurrentPage] = useState(0);
  const pageSize = 50;

  // Queries
  const {
    data: logsData,
    isLoading,
    isFetching,
    refetch,
  } = useDeviceLogs(
    deviceId,
    {
      log_level: logLevel !== 'all' ? logLevel : undefined,
      limit: pageSize,
      skip: currentPage * pageSize,
    },
    {
      enabled: deviceId > 0,
      autoRefresh,
    }
  );

  const clearLogsMutation = useClearLogs();

  // Computed
  const logs = logsData?.logs || [];
  const total = logsData?.total || 0;
  const totalPages = Math.ceil(total / pageSize);
  const hasLogs = logs.length > 0;
  const startIndex = currentPage * pageSize + 1;
  const endIndex = Math.min((currentPage + 1) * pageSize, total);

  // Handlers
  const handleViewDetails = (log: DeviceLog) => {
    setSelectedLog(log);
    setIsDetailModalOpen(true);
  };

  const handleRefresh = () => {
    refetch();
    toast.success('Logs refreshed');
  };

  const handleClearLogs = () => {
    if (!confirm('Are you sure you want to clear all console logs for this device?')) {
      return;
    }

    clearLogsMutation.mutate(deviceId, {
      onSuccess: () => {
        setCurrentPage(0);
      },
    });
  };

  const handleLogLevelChange = (value: string) => {
    setLogLevel(value as LogLevel | 'all');
    setCurrentPage(0);
  };

  const handlePreviousPage = () => {
    if (currentPage > 0) {
      setCurrentPage(currentPage - 1);
    }
  };

  const handleNextPage = () => {
    if (currentPage < totalPages - 1) {
      setCurrentPage(currentPage + 1);
    }
  };

  const getLevelIcon = (level: LogLevel) => {
    switch (level) {
      case 'error':
        return <AlertCircle className="w-4 h-4" />;
      case 'warn':
        return <AlertTriangle className="w-4 h-4" />;
      case 'info':
        return <Info className="w-4 h-4" />;
      case 'debug':
        return <Bug className="w-4 h-4" />;
      default:
        return <Terminal className="w-4 h-4" />;
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Terminal className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Device Logs
            {deviceName && (
              <span className="ml-2 text-sm font-normal text-gray-500 dark:text-gray-400">
                {deviceName}
              </span>
            )}
          </h3>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="console">
        <TabsList>
          <TabsTrigger value="console">
            <Terminal className="w-4 h-4 mr-2" />
            Console Logs
          </TabsTrigger>
          <TabsTrigger value="connection" disabled>
            <Network className="w-4 h-4 mr-2" />
            Connection Logs
            <Badge className="ml-2 text-xs bg-gray-200 text-gray-600">Coming Soon</Badge>
          </TabsTrigger>
        </TabsList>

        {/* Console Logs Tab */}
        <TabsContent value="console" className="space-y-4">
          {/* Filter Controls */}
          <div className="flex flex-wrap items-center gap-3 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
            {/* Log Level Filter */}
            <div className="flex items-center gap-2 min-w-[180px]">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Level:
              </label>
              <Select value={logLevel} onValueChange={handleLogLevelChange}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="All Logs" />
                </SelectTrigger>
                <SelectContent>
                  {LOG_LEVEL_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Auto-refresh Toggle */}
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Auto-refresh (30s)
              </span>
            </label>

            {/* Spacer */}
            <div className="flex-1" />

            {/* Action Buttons */}
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={isFetching}
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${isFetching ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleClearLogs}
                disabled={clearLogsMutation.isPending || !hasLogs}
                className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Clear Logs
              </Button>
            </div>
          </div>

          {/* Logs Table */}
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : !hasLogs ? (
            <div className="text-center py-12 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
              <Terminal className="w-12 h-12 mx-auto text-gray-400 mb-3" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-1">
                No Logs Found
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {logLevel !== 'all'
                  ? `No ${logLevel} logs available for this device.`
                  : 'This device has not sent any console logs yet.'}
              </p>
            </div>
          ) : (
            <>
              {/* Table */}
              <div className="overflow-x-auto border border-gray-200 dark:border-gray-700 rounded-lg">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-900">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Timestamp
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Level
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Message
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Source
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {logs.map((log) => (
                      <tr
                        key={log.id}
                        className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                      >
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                          {new Date(log.recorded_at).toLocaleTimeString('en-US', {
                            hour: '2-digit',
                            minute: '2-digit',
                            second: '2-digit',
                          })}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <Badge className={`flex items-center gap-1.5 w-fit ${LOG_LEVEL_COLORS[log.log_level]}`}>
                            {getLevelIcon(log.log_level)}
                            {log.log_level}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900 dark:text-white max-w-md">
                          <div className="truncate" title={log.message}>
                            {log.message}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 max-w-xs">
                          <div className="truncate font-mono text-xs" title={log.source || 'N/A'}>
                            {log.source || 'N/A'}
                          </div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-right">
                          <button
                            onClick={() => handleViewDetails(log)}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
                          >
                            <Eye className="w-4 h-4" />
                            Details
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              <div className="flex items-center justify-between px-4 py-3 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
                <div className="text-sm text-gray-700 dark:text-gray-300">
                  Showing{' '}
                  <span className="font-medium">{startIndex}</span>
                  {' - '}
                  <span className="font-medium">{endIndex}</span>
                  {' of '}
                  <span className="font-medium">{total}</span>
                  {' logs'}
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handlePreviousPage}
                    disabled={currentPage === 0}
                  >
                    Previous
                  </Button>
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    Page {currentPage + 1} of {totalPages || 1}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleNextPage}
                    disabled={currentPage >= totalPages - 1}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </>
          )}
        </TabsContent>

        {/* Connection Logs Tab (Placeholder) */}
        <TabsContent value="connection">
          <div className="text-center py-12 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
            <Network className="w-12 h-12 mx-auto text-gray-400 mb-3" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-1">
              Connection Logs Coming Soon
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Network, server, and speed test logs will be available in a future update.
            </p>
          </div>
        </TabsContent>
      </Tabs>

      {/* Log Detail Modal */}
      <LogDetailModal
        log={selectedLog}
        isOpen={isDetailModalOpen}
        onClose={() => {
          setIsDetailModalOpen(false);
          setSelectedLog(null);
        }}
      />
    </div>
  );
}
