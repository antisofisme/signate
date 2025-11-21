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

import { useState, useEffect } from 'react';
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
import { usePagination } from '@/shared/hooks';
import { Pagination } from '@/shared/components';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { useDeviceLogs, useClearLogs, useConnectionLogs } from '../hooks/useDeviceLogs';
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
  const [activeTab, setActiveTab] = useState<'console' | 'connection'>('console');

  // Connection logs state
  const [eventTypeFilter, setEventTypeFilter] = useState<string>('all');

  // Pagination hook (standardized)
  const pagination = usePagination({ pageSize: 50 });
  const connectionPagination = usePagination({ pageSize: 50 });

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
      limit: pagination.limit,
      skip: pagination.skip,
    },
    {
      enabled: deviceId > 0,
      autoRefresh,
    }
  );

  const clearLogsMutation = useClearLogs();

  // Connection logs query
  const {
    data: connectionLogsData,
    isLoading: isLoadingConnection,
    isFetching: isFetchingConnection,
    refetch: refetchConnection,
  } = useConnectionLogs(
    deviceId,
    {
      event_type: eventTypeFilter !== 'all' ? eventTypeFilter : undefined,
      limit: connectionPagination.limit,
      skip: connectionPagination.skip,
    },
    {
      enabled: deviceId > 0 && activeTab === 'connection',
    }
  );

  // Computed
  const logs = logsData?.logs || [];
  const total = logsData?.total || 0;
  const connectionLogs = connectionLogsData?.items || [];
  const connectionTotal = connectionLogsData?.total || 0;
  const totalPages = pagination.getTotalPages(total);
  const connectionTotalPages = connectionPagination.getTotalPages(connectionTotal);
  const hasLogs = logs.length > 0;
  const hasConnectionLogs = connectionLogs.length > 0;

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
        pagination.resetPage();
      },
    });
  };

  const handleLogLevelChange = (value: string) => {
    setLogLevel(value as LogLevel | 'all');
    pagination.resetPage();
  };

  const handleEventTypeChange = (value: string) => {
    setEventTypeFilter(value);
    connectionPagination.resetPage();
  };

  const handleRefreshConnection = () => {
    refetchConnection();
    toast.success('Connection logs refreshed');
  };

  const getEventTypeIcon = (eventType: string) => {
    switch (eventType) {
      case 'network':
        return <Network className="w-4 h-4" />;
      case 'server':
        return <Terminal className="w-4 h-4" />;
      case 'speed_test':
        return <RefreshCw className="w-4 h-4" />;
      default:
        return <Info className="w-4 h-4" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'online':
      case 'connected':
      case 'success':
        return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400';
      case 'offline':
      case 'disconnected':
      case 'failed':
        return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400';
      default:
        return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300';
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
      <Tabs defaultValue="console" value={activeTab} onValueChange={(v) => setActiveTab(v as 'console' | 'connection')}>
        <TabsList>
          <TabsTrigger value="console">
            <Terminal className="w-4 h-4 mr-2" />
            Console Logs
          </TabsTrigger>
          <TabsTrigger value="connection">
            <Network className="w-4 h-4 mr-2" />
            Connection Logs
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

              {/* Pagination - Using standardized component */}
              <Pagination
                currentPage={pagination.currentPage}
                totalPages={totalPages}
                totalItems={total}
                pageSize={pagination.pageSize}
                onPageChange={pagination.goToPage}
                className="px-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700"
              />
            </>
          )}
        </TabsContent>

        {/* Connection Logs Tab */}
        <TabsContent value="connection" className="space-y-4">
          {/* Filter Controls */}
          <div className="flex flex-wrap items-center gap-3 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
            {/* Event Type Filter */}
            <div className="flex items-center gap-2 min-w-[200px]">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Event Type:
              </label>
              <Select value={eventTypeFilter} onValueChange={handleEventTypeChange}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="All Events" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Events</SelectItem>
                  <SelectItem value="network">Network Status</SelectItem>
                  <SelectItem value="server">Server Connection</SelectItem>
                  <SelectItem value="speed_test">Speed Test</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Spacer */}
            <div className="flex-1" />

            {/* Action Buttons */}
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefreshConnection}
              disabled={isFetchingConnection}
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${isFetchingConnection ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>

          {/* Connection Logs Table */}
          {isLoadingConnection ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : !hasConnectionLogs ? (
            <div className="text-center py-12 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
              <Network className="w-12 h-12 mx-auto text-gray-400 mb-3" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-1">
                No Connection Logs Found
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {eventTypeFilter !== 'all'
                  ? `No ${eventTypeFilter.replace('_', ' ')} logs available for this device.`
                  : 'This device has not sent any connection logs yet.'}
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
                        Event Type
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Latency
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Speed
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Error
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {connectionLogs.map((log: any) => (
                      <tr
                        key={log.id}
                        className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                      >
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                          {new Date(log.logged_at).toLocaleTimeString('en-US', {
                            hour: '2-digit',
                            minute: '2-digit',
                            second: '2-digit',
                          })}
                          <div className="text-xs text-gray-500">
                            {new Date(log.logged_at).toLocaleDateString()}
                          </div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <Badge className="flex items-center gap-1.5 w-fit bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                            {getEventTypeIcon(log.event_type)}
                            {log.event_type.replace('_', ' ')}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <Badge className={`${getStatusColor(log.status)}`}>
                            {log.status}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                          {log.latency_ms !== null ? `${log.latency_ms}ms` : '-'}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                          {log.download_speed_mbps !== null || log.upload_speed_mbps !== null ? (
                            <div className="text-xs">
                              {log.download_speed_mbps !== null && (
                                <div>Down: {log.download_speed_mbps.toFixed(2)} Mbps</div>
                              )}
                              {log.upload_speed_mbps !== null && (
                                <div>Up: {log.upload_speed_mbps.toFixed(2)} Mbps</div>
                              )}
                            </div>
                          ) : '-'}
                        </td>
                        <td className="px-4 py-3 text-sm text-red-600 dark:text-red-400 max-w-xs">
                          <div className="truncate" title={log.error_message || ''}>
                            {log.error_message || '-'}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              <Pagination
                currentPage={connectionPagination.currentPage}
                totalPages={connectionTotalPages}
                totalItems={connectionTotal}
                pageSize={connectionPagination.pageSize}
                onPageChange={connectionPagination.goToPage}
                className="px-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700"
              />
            </>
          )}
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
