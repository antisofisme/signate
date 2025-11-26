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
 */

import { useState, useEffect } from 'react';
import {
  Terminal,
  RefreshCw,
  Trash2,
  Eye,
  Filter,
  AlertCircle,
  Info,
  Bug,
  Activity,
  Network,
  Gauge,
  Wifi,
  WifiOff,
} from 'lucide-react';
import { usePagination } from '@/shared/hooks';
import { Pagination } from '@/shared/components';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { useDeviceLogs, useClearLogs, useConnectionLogs } from '../hooks/useDeviceLogs';
import { useConsoleLiveStream } from '../hooks';
import { LogDetailModal } from './LogDetailModal';
import type { DeviceLog, LogLevel } from '../types/logs';
import { toast } from 'sonner';

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

  const getLevelIcon = (level: string) => {
    if (!level) return <Info className="w-4 h-4" />; // Default icon for undefined/null

    switch (level.toLowerCase()) {
      case 'error':
        return <AlertCircle className="w-4 h-4" />;
      case 'warn':
      case 'warning':
        return <Activity className="w-4 h-4" />;
      case 'info':
        return <Info className="w-4 h-4" />;
      case 'debug':
        return <Bug className="w-4 h-4" />;
      default:
        return <Terminal className="w-4 h-4" />;
    }
  };

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
      <div className="flex flex-col h-full min-h-[600px]">

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

              <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isFetching} className="h-8 px-2 text-xs">
                <RefreshCw className={`w-3 h-3 mr-1 ${isFetching ? 'animate-spin' : ''}`} />
                Refresh
              </Button>

              <Button variant="outline" size="sm" onClick={handleClearLogs} disabled={clearLogsMutation.isPending} className="h-8 px-2 text-xs">
                <Trash2 className="w-3 h-3 mr-1" />
                Clear
              </Button>

              <Button variant={autoRefresh ? 'default' : 'outline'} size="sm" onClick={() => setAutoRefresh(!autoRefresh)} className="h-8 px-2 text-xs">
                <RefreshCw className={`w-3 h-3 mr-1 ${autoRefresh ? 'animate-spin' : ''}`} />
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

              <Button variant="outline" size="sm" onClick={handleRefreshConnection} disabled={isFetchingConnection} className="h-8 px-2 text-xs">
                <RefreshCw className={`w-3 h-3 mr-1 ${isFetchingConnection ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          )}

          {/* Speed Test Filters */}
          {activeTab === 'speedtest' && (
            <div className="flex items-center gap-2 px-3 py-2">
              <div className="flex-1" />

              <Button variant="outline" size="sm" onClick={handleRefreshSpeedTest} disabled={isFetchingSpeedTest} className="h-8 px-2 text-xs">
                <RefreshCw className={`w-3 h-3 mr-1 ${isFetchingSpeedTest ? 'animate-spin' : ''}`} />
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
                <div className="border rounded-lg overflow-hidden">
                  <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-800 sticky top-0">
                      <tr>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-16">
                          Level
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-40">
                          Time
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Message
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                      {liveConsoleLogs.map((log, index) => (
                        <tr
                          key={`${log.timestamp}-${index}`}
                          className="hover:bg-gray-50 dark:hover:bg-gray-800"
                        >
                          <td className="px-3 py-2 whitespace-nowrap">
                            <Badge
                              variant={
                                log.level === 'error' ? 'destructive' :
                                log.level === 'warn' ? 'default' :
                                log.level === 'info' ? 'secondary' :
                                'outline'
                              }
                              className="text-xs"
                            >
                              {log.level.toUpperCase()}
                            </Badge>
                          </td>
                          <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-500 dark:text-gray-400">
                            {new Date(log.timestamp).toLocaleString()}
                          </td>
                          <td className="px-3 py-2 text-sm text-gray-900 dark:text-gray-100 font-mono break-words">
                            {log.message}
                            {log.stack && (
                              <pre className="mt-1 text-xs text-red-600 dark:text-red-400 whitespace-pre-wrap">
                                {log.stack}
                              </pre>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Connection Logs */}
          {activeTab === 'connection' && (
            <div className="space-y-3 p-3">
            {/* Connection Logs List */}
            {isLoadingConnection ? (
              <div className="space-y-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-20 w-full" />
                ))}
              </div>
            ) : !hasConnectionLogs ? (
              <div className="text-center py-12 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
                <Network className="w-12 h-12 mx-auto text-gray-400 mb-3" />
                <p className="text-gray-500 dark:text-gray-400">No connection logs available</p>
              </div>
            ) : (
              <div className="border rounded-lg overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-800">
                    <tr>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-32">
                        Event Type
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-24">
                        Status
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-40">
                        Time
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-24">
                        Latency
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Error Message
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                    {connectionLogs.map((log: any) => (
                      <tr key={log.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                        <td className="px-3 py-2 whitespace-nowrap">
                          <Badge variant="outline" className="text-xs">
                            {log.event_type}
                          </Badge>
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap">
                          <Badge
                            variant={
                              log.status === 'success' || log.status === 'connected' || log.status === 'online' ? 'default' :
                              log.status === 'failed' || log.status === 'disconnected' || log.status === 'offline' ? 'destructive' :
                              'secondary'
                            }
                            className="text-xs"
                          >
                            {log.status}
                          </Badge>
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-500 dark:text-gray-400">
                          {new Date(log.logged_at || log.recorded_at).toLocaleString()}
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                          {log.latency_ms !== null ? `${log.latency_ms}ms` : '-'}
                        </td>
                        <td className="px-3 py-2 text-sm text-red-600 dark:text-red-400 font-mono truncate max-w-md">
                          {log.error_message || '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            </div>
          )}

          {/* Speed Test Logs */}
          {activeTab === 'speedtest' && (
            <div className="space-y-3 p-3">
            {/* Speed Test Logs Table */}
            {isLoadingSpeedTest ? (
              <div className="space-y-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-16 w-full" />
                ))}
              </div>
            ) : !hasSpeedTestLogs ? (
              <div className="text-center py-12 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
                <Gauge className="w-12 h-12 mx-auto text-gray-400 mb-3" />
                <p className="text-gray-500 dark:text-gray-400">No speed test logs available</p>
              </div>
            ) : (
              <>
                <div className="overflow-x-auto bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
                  <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-900">
                      <tr>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Timestamp
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Download Speed
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Upload Speed
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Latency
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Error
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                      {speedTestLogs.map((log: any) => (
                        <tr key={log.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                          <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                            {new Date(log.recorded_at).toLocaleString()}
                          </td>
                          <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                            {log.download_speed_mbps !== null ? (
                              <div className="flex items-baseline gap-1">
                                <span className="font-semibold">{log.download_speed_mbps.toFixed(2)}</span>
                                <span className="text-xs text-gray-500 dark:text-gray-400">Mbps</span>
                              </div>
                            ) : (
                              <span className="text-gray-400">-</span>
                            )}
                          </td>
                          <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                            {log.upload_speed_mbps !== null ? (
                              <div className="flex items-baseline gap-1">
                                <span className="font-semibold">{log.upload_speed_mbps.toFixed(2)}</span>
                                <span className="text-xs text-gray-500 dark:text-gray-400">Mbps</span>
                              </div>
                            ) : (
                              <span className="text-gray-400">-</span>
                            )}
                          </td>
                          <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                            {log.latency_ms !== null ? (
                              <span className="font-semibold">{log.latency_ms}ms</span>
                            ) : (
                              <span className="text-gray-400">-</span>
                            )}
                          </td>
                          <td className="px-3 py-2 whitespace-nowrap">
                            <Badge variant={
                              log.status === 'success' ? 'default' :
                              log.status === 'failed' ? 'destructive' :
                              'secondary'
                            }>
                              {log.status}
                            </Badge>
                          </td>
                          <td className="px-3 py-2 text-sm text-gray-500 dark:text-gray-400 max-w-xs truncate">
                            {log.error_message || '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
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
