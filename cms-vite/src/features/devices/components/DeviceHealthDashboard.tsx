/**
 * Device Health Dashboard Component
 *
 * LAYER 1: PRESENTATION
 * Displays device health metrics, alerts, and historical data
 */

import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  Cpu,
  HardDrive,
  MemoryStick,
  Wifi,
  Monitor,
  AlertTriangle,
  CheckCircle,
  XCircle,
  TrendingUp,
  RefreshCw,
  Play,
  Pause,
  Gauge,
  Timer,
  Zap,
  BarChart3,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { deviceHealthApi } from '../api/health';
import type { DeviceHealthWithAlerts, HealthAlert } from '../types/health';
import { formatDistanceToNow } from 'date-fns';

interface DeviceHealthDashboardProps {
  deviceId: number;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export function DeviceHealthDashboard({
  deviceId,
  autoRefresh = true,
  refreshInterval = 30000, // 30 seconds
}: DeviceHealthDashboardProps) {
  // Fetch latest health with alerts
  const {
    data: healthData,
    isLoading,
    isError,
    refetch,
  } = useQuery<DeviceHealthWithAlerts>({
    queryKey: ['device-health', deviceId],
    queryFn: () => deviceHealthApi.getHealth(deviceId),
    refetchInterval: autoRefresh ? refreshInterval : false,
    staleTime: 20000, // Consider data stale after 20 seconds
  });

  // Fetch 24h history for charts
  const { data: historyData } = useQuery({
    queryKey: ['device-health-history', deviceId],
    queryFn: () => deviceHealthApi.getHealthHistory(deviceId, 24),
    refetchInterval: autoRefresh ? 60000 : false, // Refresh every minute
    staleTime: 50000,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (isError || !healthData) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
        <div className="flex items-start gap-3">
          <XCircle className="w-6 h-6 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-red-900 dark:text-red-100">
              Unable to load health data
            </h3>
            <p className="text-sm text-red-700 dark:text-red-300 mt-1">
              No health metrics available for this device. The device may need to send health data first.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const { health, alerts } = healthData;

  if (!health) {
    return (
      <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-6 h-6 text-gray-400 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-gray-100">
              No health data available
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              This device hasn't reported any health metrics yet.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 dark:text-green-400';
      case 'warning':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'critical':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-5 h-5" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5" />;
      case 'critical':
        return <XCircle className="w-5 h-5" />;
      default:
        return <Activity className="w-5 h-5" />;
    }
  };

  const getAlertLevelColor = (level: string) => {
    switch (level) {
      case 'info':
        return 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 border-blue-300 dark:border-blue-700';
      case 'warning':
        return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200 border-yellow-300 dark:border-yellow-700';
      case 'critical':
        return 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200 border-red-300 dark:border-red-700';
      default:
        return 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 border-gray-300 dark:border-gray-700';
    }
  };

  // Prepare chart data
  const chartData =
    historyData?.history.map((h) => ({
      time: new Date(h.recorded_at).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
      }),
      cpu: h.cpu_usage || 0,
      memory: h.memory_usage || 0,
      disk: h.disk_usage || 0,
    })) || [];

  return (
    <div className="space-y-6">
      {/* Overall Status Header */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={getStatusColor(health.overall_status)}>
              {getStatusIcon(health.overall_status)}
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Device Health Status
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Last updated {formatDistanceToNow(new Date(health.recorded_at))} ago
              </p>
            </div>
          </div>
          <button
            onClick={() => refetch()}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            title="Refresh health data"
          >
            <RefreshCw className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </button>
        </div>
      </div>

      {/* Alerts Section */}
      {alerts.length > 0 && (
        <div className="space-y-3">
          <h4 className="font-semibold text-gray-900 dark:text-white">
            Active Alerts ({alerts.length})
          </h4>
          {alerts.map((alert: HealthAlert, index: number) => (
            <div
              key={index}
              className={`border rounded-lg p-4 ${getAlertLevelColor(alert.alert_level)}`}
            >
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="font-medium">{alert.alert_message}</p>
                  <p className="text-sm mt-1">
                    Current: {alert.metric_value.toFixed(1)}% | Threshold:{' '}
                    {alert.threshold_value.toFixed(1)}%
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* CPU Usage */}
        <MetricCard
          icon={<Cpu className="w-5 h-5" />}
          title="CPU Usage"
          value={health.cpu_usage !== undefined ? `${health.cpu_usage.toFixed(1)}%` : 'N/A'}
          status={
            health.cpu_usage !== undefined && health.cpu_usage > 80
              ? 'warning'
              : 'healthy'
          }
        />

        {/* Memory Usage */}
        <MetricCard
          icon={<MemoryStick className="w-5 h-5" />}
          title="Memory Usage"
          value={
            health.memory_usage !== undefined
              ? `${health.memory_usage.toFixed(1)}%`
              : 'N/A'
          }
          subtitle={
            health.memory_used_mb && health.memory_total_mb
              ? `${health.memory_used_mb} / ${health.memory_total_mb} MB`
              : undefined
          }
          status={
            health.memory_usage !== undefined && health.memory_usage > 85
              ? 'warning'
              : 'healthy'
          }
        />

        {/* Disk Usage */}
        <MetricCard
          icon={<HardDrive className="w-5 h-5" />}
          title="Disk Usage"
          value={
            health.disk_usage !== undefined ? `${health.disk_usage.toFixed(1)}%` : 'N/A'
          }
          subtitle={
            health.disk_used_gb && health.disk_total_gb
              ? `${health.disk_used_gb} / ${health.disk_total_gb} GB`
              : undefined
          }
          status={
            health.disk_usage !== undefined && health.disk_usage > 90
              ? 'warning'
              : 'healthy'
          }
        />

        {/* Network Latency */}
        <MetricCard
          icon={<Wifi className="w-5 h-5" />}
          title="Network Latency"
          value={
            health.network_latency_ms !== undefined
              ? `${health.network_latency_ms} ms`
              : 'N/A'
          }
          subtitle={health.connection_quality || undefined}
          status={
            health.network_latency_ms !== undefined && health.network_latency_ms > 100
              ? 'warning'
              : 'healthy'
          }
        />

        {/* Display */}
        <MetricCard
          icon={<Monitor className="w-5 h-5" />}
          title="Display"
          value={health.display_resolution || 'N/A'}
          subtitle={
            health.display_refresh_rate
              ? `${health.display_refresh_rate} Hz`
              : undefined
          }
          status="healthy"
        />

        {/* Player Uptime */}
        <MetricCard
          icon={<TrendingUp className="w-5 h-5" />}
          title="Player Uptime"
          value={
            health.player_uptime_hours !== undefined
              ? `${health.player_uptime_hours}h`
              : 'N/A'
          }
          subtitle={health.player_version || undefined}
          status="healthy"
        />
      </div>

      {/* Behavioral Metrics (Phase 3) */}
      {(health.playback_stalls_count !== undefined ||
        health.buffer_underruns_count !== undefined ||
        health.content_play_count !== undefined) && (
        <div className="mt-6">
          <h4 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Play className="w-4 h-4" />
            Playback Metrics
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              icon={<Play className="w-5 h-5" />}
              title="Content Plays"
              value={health.content_play_count?.toString() || '0'}
              status="healthy"
            />
            <MetricCard
              icon={<Pause className="w-5 h-5" />}
              title="Playback Stalls"
              value={health.playback_stalls_count?.toString() || '0'}
              status={health.playback_stalls_count && health.playback_stalls_count > 5 ? 'warning' : 'healthy'}
            />
            <MetricCard
              icon={<AlertTriangle className="w-5 h-5" />}
              title="Buffer Underruns"
              value={health.buffer_underruns_count?.toString() || '0'}
              status={health.buffer_underruns_count && health.buffer_underruns_count > 3 ? 'warning' : 'healthy'}
            />
            <MetricCard
              icon={<Timer className="w-5 h-5" />}
              title="Time to First Play"
              value={health.time_to_first_playback_ms ? `${health.time_to_first_playback_ms}ms` : 'N/A'}
              status={health.time_to_first_playback_ms && health.time_to_first_playback_ms > 3000 ? 'warning' : 'healthy'}
            />
          </div>
        </div>
      )}

      {/* Performance Metrics (Phase 4) */}
      {(health.fps_current !== undefined ||
        health.long_tasks_count !== undefined ||
        health.cpu_pressure !== undefined) && (
        <div className="mt-6">
          <h4 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Gauge className="w-4 h-4" />
            Performance Metrics
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              icon={<Gauge className="w-5 h-5" />}
              title="Current FPS"
              value={health.fps_current?.toString() || 'N/A'}
              status={health.fps_current && health.fps_current < 30 ? 'warning' : 'healthy'}
            />
            <MetricCard
              icon={<Zap className="w-5 h-5" />}
              title="CPU Pressure"
              value={health.cpu_pressure || 'nominal'}
              status={health.cpu_pressure === 'critical' ? 'critical' :
                      health.cpu_pressure === 'serious' ? 'warning' : 'healthy'}
            />
            <MetricCard
              icon={<Activity className="w-5 h-5" />}
              title="Long Tasks"
              value={health.long_tasks_count?.toString() || '0'}
              status={health.long_tasks_count && health.long_tasks_count > 10 ? 'warning' : 'healthy'}
            />
            <MetricCard
              icon={<Timer className="w-5 h-5" />}
              title="TTFB"
              value={health.ttfb_ms ? `${health.ttfb_ms}ms` : 'N/A'}
              status={health.ttfb_ms && health.ttfb_ms > 500 ? 'warning' : 'healthy'}
            />
          </div>
        </div>
      )}

      {/* Error Rate Summary */}
      {(health.error_rate_percent !== undefined ||
        health.content_load_failures_count !== undefined) && (
        <div className="mt-6">
          <h4 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Error Statistics
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <MetricCard
              icon={<BarChart3 className="w-5 h-5" />}
              title="Error Rate"
              value={health.error_rate_percent !== undefined ? `${health.error_rate_percent.toFixed(1)}%` : 'N/A'}
              status={health.error_rate_percent && health.error_rate_percent > 5 ? 'warning' : 'healthy'}
            />
            <MetricCard
              icon={<XCircle className="w-5 h-5" />}
              title="Load Failures"
              value={health.content_load_failures_count?.toString() || '0'}
              status={health.content_load_failures_count && health.content_load_failures_count > 5 ? 'warning' : 'healthy'}
            />
            <MetricCard
              icon={<Activity className="w-5 h-5" />}
              title="Quality Switches"
              value={health.quality_switches_count?.toString() || '0'}
              subtitle="HLS adaptive"
              status="healthy"
            />
          </div>
        </div>
      )}

      {/* Content Errors */}
      {health.content_errors_count > 0 && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-yellow-900 dark:text-yellow-100">
                {health.content_errors_count} content error
                {health.content_errors_count !== 1 ? 's' : ''} detected
              </p>
              {health.last_error_message && (
                <p className="text-sm text-yellow-800 dark:text-yellow-200 mt-1">
                  Last error: {health.last_error_message}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 24h Health History Chart */}
      {chartData.length > 0 && (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <h4 className="font-semibold text-gray-900 dark:text-white mb-4">
            24-Hour Health Trends
          </h4>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="time"
                tick={{ fontSize: 12 }}
                stroke="#888"
              />
              <YAxis
                domain={[0, 100]}
                tick={{ fontSize: 12 }}
                stroke="#888"
                label={{ value: 'Usage (%)', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(0, 0, 0, 0.8)',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#fff',
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="cpu"
                stroke="#3b82f6"
                strokeWidth={2}
                name="CPU"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="memory"
                stroke="#10b981"
                strokeWidth={2}
                name="Memory"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="disk"
                stroke="#f59e0b"
                strokeWidth={2}
                name="Disk"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

// Metric Card Component
interface MetricCardProps {
  icon: React.ReactNode;
  title: string;
  value: string;
  subtitle?: string;
  status: 'healthy' | 'warning' | 'critical';
}

function MetricCard({ icon, title, value, subtitle, status }: MetricCardProps) {
  const getStatusColor = () => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 dark:text-green-400';
      case 'warning':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'critical':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
      <div className="flex items-center gap-3 mb-2">
        <div className={getStatusColor()}>{icon}</div>
        <h5 className="text-sm font-medium text-gray-600 dark:text-gray-400">
          {title}
        </h5>
      </div>
      <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
      {subtitle && (
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{subtitle}</p>
      )}
    </div>
  );
}
