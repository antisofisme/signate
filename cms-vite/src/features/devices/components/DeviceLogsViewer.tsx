/**
 * Device Logs Viewer Component
 *
 * Features:
 * - Tabbed interface (Console Logs / Connection Logs / Speed Test)
 * - Filter controls (log level, auto-refresh)
 * - Pagination
 * - Log detail modal
 * - Clear logs functionality
 * - Sticky header and footer with scrollable content
 * - Standardized DataTable with compact mode
 */

import { useState, useEffect, useMemo } from 'react';
import {
  Terminal,
  RefreshCw,
  Trash2,
  Filter,
  Network,
  Gauge,
  Wifi,
  WifiOff,
} from 'lucide-react';
import { usePagination } from '@/shared/hooks';
import { Pagination, Button, DataTable, type Column } from '@/shared/components';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { useDeviceLogs, useClearLogs, useConnectionLogs } from '../hooks/useDeviceLogs';
import { useConsoleLiveStream } from '../hooks';
import { LogDetailModal } from './LogDetailModal';
import type { DeviceLog, LogLevel } from '../types/logs';
import { toast } from '@/shared/utils/toast';

export type LogsViewTab = 'console' | 'connection' | 'speedtest';

interface DeviceLogsViewerProps {
  deviceId: number;
  deviceName?: string;
  activeTab?: LogsViewTab;
  onTabChange?: (tab: LogsViewTab) => void;
}

export function DeviceLogsViewer({
  deviceId,
  deviceName,
  activeTab = 'console',
  onTabChange,
}: DeviceLogsViewerProps) {
  // State
  const [selectedLog, setSelectedLog] = useState<DeviceLog | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [logLevel, setLogLevel] = useState<string>('all');
  const [eventTypeFilter, setEventTypeFilter] = useState<string>('all');

  // Pagination hook (standardized)
  const pagination = usePagination({ pageSize: 50 });
  const connectionPagination = usePagination({ pageSize: 50 });
  const speedTestPagination = usePagination({ pageSize: 50 });

  // Queries
  const {
    data: logsData,
    isLoading,
    isFetching,
    refetch,
  } = useDeviceLogs(
    deviceId,
    {
      log_level: logLevel !== 'all' ? (logLevel as LogLevel) : undefined,
      limit: pagination.limit,
      skip: pagination.skip,
    },
    {
      enabled: deviceId > 0 && activeTab === 'console',
    }
  );

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

  // Speed test logs query (filtered connection_logs with event_type=speed_test)
  const {
    data: speedTestLogsData,
    isLoading: isLoadingSpeedTest,
    isFetching: isFetchingSpeedTest,
    refetch: refetchSpeedTest,
  } = useConnectionLogs(
    deviceId,
    {
      event_type: 'speed_test',
      limit: speedTestPagination.limit,
      skip: speedTestPagination.skip,
    },
    {
      enabled: deviceId > 0 && activeTab === 'speedtest',
    }
  );

  // Live console streaming (WebSocket-based, no database)
  const {
    logs: liveConsoleLogs,
    isConnected: isConsoleConnected,
    isConnecting: isConsoleConnecting,
    error: consoleStreamError,
    clearLogs: clearLiveConsoleLogs,
    reconnect: reconnectConsoleStream,
  } = useConsoleLiveStream({
    deviceId,
    enabled: activeTab === 'console', // Only connect when console tab is active
    maxLogs: 1000,
    onError: (error) => {
      console.error('[DeviceLogsViewer] Console stream error:', error);
    },
  });

  // Computed
  const logs = logsData?.logs || [];
  const total = logsData?.total || 0;
  const connectionLogs = connectionLogsData?.items || [];
  const connectionTotal = connectionLogsData?.total || 0;
  const speedTestLogs = speedTestLogsData?.items || [];
  const speedTestTotal = speedTestLogsData?.total || 0;
  const totalPages = pagination.getTotalPages(total);
  const connectionTotalPages = connectionPagination.getTotalPages(connectionTotal);
  const speedTestTotalPages = speedTestPagination.getTotalPages(speedTestTotal);
  const hasLogs = logs.length > 0;
  const hasConnectionLogs = connectionLogs.length > 0;
  const hasSpeedTestLogs = speedTestLogs.length > 0;

  // Handlers
  const handleViewDetails = (log: DeviceLog) => {
    setSelectedLog(log);
    setIsDetailModalOpen(true);
  };

  const clearLogsMutation = useClearLogs();

  const handleClearLogs = async () => {
    if (!window.confirm('Are you sure you want to clear all logs? This action cannot be undone.')) {
      return;
    }

    try {
      await clearLogsMutation.mutateAsync(deviceId);
      toast.success('All logs cleared successfully');
      refetch();
    } catch (error) {
      toast.error('Failed to clear logs');
    }
  };

  const handleLogLevelChange = (value: string) => {
    setLogLevel(value);
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

  const handleRefreshSpeedTest = () => {
    refetchSpeedTest();
    toast.success('Speed test logs refreshed');
  };

  // ============================================
  // Column Definitions - Standardized for DataTable
  // ============================================

  // Console Logs Columns
  const consoleColumns: Column<any>[] = useMemo(() => [
    {
      key: 'level',
      header: 'Level',
      headerClassName: 'w-20',
      className: 'whitespace-nowrap',
      render: (log) => (
        <Badge
          variant={
            log.level === 'error' ? 'destructive' :
            log.level === 'warn' ? 'default' :
            log.level === 'info' ? 'secondary' :
            'outline'
          }
          className="text-xs"
        >
          {log.level?.toUpperCase() || 'LOG'}
        </Badge>
      ),
    },
    {
      key: 'timestamp',
      header: 'Time',
      headerClassName: 'w-40',
      className: 'whitespace-nowrap text-xs text-gray-500 dark:text-gray-400',
      render: (log) => new Date(log.timestamp).toLocaleString(),
    },
    {
      key: 'message',
      header: 'Message',
      className: 'font-mono break-words',
      render: (log) => (
        <div>
          {log.message}
          {log.stack && (
            <pre className="mt-1 text-xs text-red-600 dark:text-red-400 whitespace-pre-wrap">
              {log.stack}
            </pre>
          )}
        </div>
      ),
    },
  ], []);

  // Connection Logs Columns
  const connectionColumns: Column<any>[] = useMemo(() => [
    {
      key: 'event_type',
      header: 'Event Type',
      headerClassName: 'w-28',
      className: 'whitespace-nowrap',
      render: (log) => (
        <Badge variant="outline" className="text-xs">
          {log.event_type}
        </Badge>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      headerClassName: 'w-24',
      className: 'whitespace-nowrap',
      render: (log) => (
        <Badge
          variant={
            ['success', 'connected', 'online', 'tested'].includes(log.status) ? 'default' :
            ['failed', 'disconnected', 'offline'].includes(log.status) ? 'destructive' :
            'secondary'
          }
          className="text-xs"
        >
          {log.status}
        </Badge>
      ),
    },
    {
      key: 'logged_at',
      header: 'Time',
      headerClassName: 'w-40',
      className: 'whitespace-nowrap text-xs text-gray-500 dark:text-gray-400',
      render: (log) => new Date(log.logged_at || log.recorded_at).toLocaleString(),
    },
    {
      key: 'latency_ms',
      header: 'Latency',
      headerClassName: 'w-20',
      className: 'whitespace-nowrap',
      render: (log) => log.latency_ms !== null ? `${log.latency_ms}ms` : '-',
    },
    {
      key: 'error_message',
      header: 'Error',
      className: 'text-red-600 dark:text-red-400 font-mono truncate max-w-xs',
      render: (log) => log.error_message || '-',
    },
  ], []);

  // Speed Test Logs Columns
  const speedTestColumns: Column<any>[] = useMemo(() => [
    {
      key: 'logged_at',
      header: 'Time',
      headerClassName: 'w-40',
      className: 'whitespace-nowrap text-xs text-gray-500 dark:text-gray-400',
      render: (log) => new Date(log.logged_at || log.recorded_at).toLocaleString(),
    },
    {
      key: 'test_trigger',
      header: 'Trigger',
      headerClassName: 'w-20',
      className: 'whitespace-nowrap',
      render: (log) => (
        <Badge
          variant={log.test_trigger === 'manual' ? 'default' : 'outline'}
          className="text-xs"
        >
          {log.test_trigger === 'manual' ? 'Manual' : 'Auto'}
        </Badge>
      ),
    },
    {
      key: 'download_speed_mbps',
      header: 'Download',
      headerClassName: 'w-28',
      className: 'whitespace-nowrap',
      render: (log) => log.download_speed_mbps !== null ? (
        <span><span className="font-semibold">{Number(log.download_speed_mbps).toFixed(2)}</span> <span className="text-xs text-gray-500">Mbps</span></span>
      ) : <span className="text-gray-400">-</span>,
    },
    {
      key: 'upload_speed_mbps',
      header: 'Upload',
      headerClassName: 'w-28',
      className: 'whitespace-nowrap',
      render: (log) => log.upload_speed_mbps !== null ? (
        <span><span className="font-semibold">{Number(log.upload_speed_mbps).toFixed(2)}</span> <span className="text-xs text-gray-500">Mbps</span></span>
      ) : <span className="text-gray-400">-</span>,
    },
    {
      key: 'latency_ms',
      header: 'Latency',
      headerClassName: 'w-20',
      className: 'whitespace-nowrap',
      render: (log) => log.latency_ms !== null ? (
        <span className="font-semibold">{log.latency_ms}ms</span>
      ) : <span className="text-gray-400">-</span>,
    },
    {
      key: 'status',
      header: 'Status',
      headerClassName: 'w-20',
      className: 'whitespace-nowrap',
      render: (log) => (
        <Badge
          variant={
            log.status === 'success' || log.status === 'tested' ? 'default' :
            log.status === 'failed' ? 'destructive' :
            'secondary'
          }
          className="text-xs"
        >
          {log.status}
        </Badge>
      ),
    },
    {
      key: 'error_message',
      header: 'Error',
      className: 'text-gray-500 dark:text-gray-400 truncate max-w-xs',
      render: (log) => log.error_message || '-',
    },
  ], []);

  // Auto-refresh effect
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      if (activeTab === 'console') {
        refetch();
      } else if (activeTab === 'connection') {
        refetchConnection();
      } else if (activeTab === 'speedtest') {
        refetchSpeedTest();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [autoRefresh, activeTab, refetch, refetchConnection, refetchSpeedTest]);

  return (
    <>
      <div className="flex flex-col h-full">

        {/* Sticky Filter Bar */}
        <div className="sticky top-0 z-[9] bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
          {/* Console Filters */}
          {activeTab === 'console' && (
            <div className="flex items-center gap-2 px-3 py-2">
              <Filter className="w-4 h-4 text-gray-500" />
              <Select value={logLevel} onValueChange={handleLogLevelChange}>
                <SelectTrigger className="w-36 h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Levels</SelectItem>
                  <SelectItem value="error">Error</SelectItem>
                  <SelectItem value="warn">Warning</SelectItem>
                  <SelectItem value="info">Info</SelectItem>
                  <SelectItem value="debug">Debug</SelectItem>
                </SelectContent>
              </Select>

              <div className="flex-1" />

              <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isFetching} loading={isFetching} leftIcon={<RefreshCw className="w-3 h-3" />} className="h-8 px-2 text-xs">
                Refresh
              </Button>

              <Button variant="outline" size="sm" onClick={handleClearLogs} disabled={clearLogsMutation.isPending} loading={clearLogsMutation.isPending} leftIcon={<Trash2 className="w-3 h-3" />} className="h-8 px-2 text-xs">
                Clear
              </Button>

              <Button variant={autoRefresh ? 'primary' : 'outline'} size="sm" onClick={() => setAutoRefresh(!autoRefresh)} leftIcon={<RefreshCw className={`w-3 h-3 ${autoRefresh ? 'animate-spin' : ''}`} />} className="h-8 px-2 text-xs">
                Auto
              </Button>
            </div>
          )}

          {/* Connection Filters */}
          {activeTab === 'connection' && (
            <div className="flex items-center gap-2 px-3 py-2">
              <Filter className="w-4 h-4 text-gray-500" />
              <Select value={eventTypeFilter} onValueChange={handleEventTypeChange}>
                <SelectTrigger className="w-36 h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="network">Network</SelectItem>
                  <SelectItem value="server">Server</SelectItem>
                  <SelectItem value="speed_test">Speed Test</SelectItem>
                </SelectContent>
              </Select>

              <div className="flex-1" />

              <Button variant="outline" size="sm" onClick={handleRefreshConnection} disabled={isFetchingConnection} loading={isFetchingConnection} leftIcon={<RefreshCw className="w-3 h-3" />} className="h-8 px-2 text-xs">
                Refresh
              </Button>
            </div>
          )}

          {/* Speed Test Filters */}
          {activeTab === 'speedtest' && (
            <div className="flex items-center gap-2 px-3 py-2">
              <div className="flex-1" />

              <Button variant="outline" size="sm" onClick={handleRefreshSpeedTest} disabled={isFetchingSpeedTest} loading={isFetchingSpeedTest} leftIcon={<RefreshCw className="w-3 h-3" />} className="h-8 px-2 text-xs">
                Refresh
              </Button>
            </div>
          )}
        </div>

        {/* Scrollable Content Area */}
        <div className="flex-1 overflow-y-auto">
          {/* Console Logs - LIVE STREAM (WebSocket, no database) */}
          {activeTab === 'console' && (
            <div className="space-y-3 p-3">
              {/* Connection Status Banner */}
              <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${
                isConsoleConnected
                  ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
                  : isConsoleConnecting
                  ? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800'
                  : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
              }`}>
                {isConsoleConnected ? (
                  <>
                    <Wifi className="w-4 h-4 text-green-600 dark:text-green-400" />
                    <span className="text-xs font-medium text-green-700 dark:text-green-300">
                      Live Streaming Active ({liveConsoleLogs.length} logs)
                    </span>
                  </>
                ) : isConsoleConnecting ? (
                  <>
                    <RefreshCw className="w-4 h-4 text-yellow-600 dark:text-yellow-400 animate-spin" />
                    <span className="text-xs font-medium text-yellow-700 dark:text-yellow-300">
                      Connecting to live stream...
                    </span>
                  </>
                ) : (
                  <>
                    <WifiOff className="w-4 h-4 text-red-600 dark:text-red-400" />
                    <span className="text-xs font-medium text-red-700 dark:text-red-300">
                      {consoleStreamError ? `Error: ${consoleStreamError.message}` : 'Disconnected'}
                    </span>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={reconnectConsoleStream}
                      className="ml-auto h-6 text-xs"
                    >
                      Reconnect
                    </Button>
                  </>
                )}
                {isConsoleConnected && liveConsoleLogs.length > 0 && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={clearLiveConsoleLogs}
                    className="ml-auto h-6 text-xs"
                  >
                    <Trash2 className="w-3 h-3 mr-1" />
                    Clear
                  </Button>
                )}
              </div>

              {/* Logs List */}
              {isConsoleConnecting ? (
                <div className="space-y-2">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Skeleton key={i} className="h-20 w-full" />
                  ))}
                </div>
              ) : liveConsoleLogs.length === 0 ? (
                <div className="text-center py-12 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
                  <Terminal className="w-12 h-12 mx-auto text-gray-400 mb-3" />
                  <p className="text-gray-500 dark:text-gray-400">
                    {isConsoleConnected ? 'Waiting for console logs...' : 'No connection to device'}
                  </p>
                  <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
                    Logs will appear here in real-time when the device sends them
                  </p>
                </div>
              ) : (
                <DataTable
                  compact
                  columns={consoleColumns}
                  data={liveConsoleLogs.map((log, i) => ({ ...log, _index: i }))}
                  keyExtractor={(log) => `${log.timestamp}-${log._index}`}
                  emptyMessage="Waiting for console logs..."
                  emptyIcon={Terminal}
                />
              )}
            </div>
          )}

          {/* Connection Logs */}
          {activeTab === 'connection' && (
            <div className="p-3">
              <DataTable
                compact
                columns={connectionColumns}
                data={connectionLogs}
                keyExtractor={(log: any) => log.id}
                isLoading={isLoadingConnection}
                emptyMessage="No connection logs available"
                emptyIcon={Network}
                skeletonRows={8}
              />
            </div>
          )}

          {/* Speed Test Logs */}
          {activeTab === 'speedtest' && (
            <div className="p-3">
              <DataTable
                compact
                columns={speedTestColumns}
                data={speedTestLogs}
                keyExtractor={(log: any) => log.id}
                isLoading={isLoadingSpeedTest}
                emptyMessage="No speed test logs available"
                emptyIcon={Gauge}
                skeletonRows={8}
              />
            </div>
          )}
        </div>

        {/* Sticky Footer - Pagination (not needed for console live stream) */}
        <div className="sticky bottom-0 z-10 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 px-3 py-2">
          {activeTab === 'console' && liveConsoleLogs.length > 0 && (
            <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
              Showing last {liveConsoleLogs.length} logs (live stream)
            </div>
          )}
          {activeTab === 'connection' && hasConnectionLogs && (
            <Pagination
              currentPage={connectionPagination.currentPage}
              totalPages={connectionTotalPages}
              totalItems={connectionTotal}
              pageSize={connectionPagination.pageSize}
              onPageChange={connectionPagination.goToPage}
            />
          )}
          {activeTab === 'speedtest' && hasSpeedTestLogs && (
            <Pagination
              currentPage={speedTestPagination.currentPage}
              totalPages={speedTestTotalPages}
              totalItems={speedTestTotal}
              pageSize={speedTestPagination.pageSize}
              onPageChange={speedTestPagination.goToPage}
            />
          )}
        </div>
      </div>

      {/* Log Detail Modal */}
      <LogDetailModal
        log={selectedLog}
        isOpen={isDetailModalOpen}
        onClose={() => {
          setIsDetailModalOpen(false);
          setSelectedLog(null);
        }}
      />
    </>
  );
}
