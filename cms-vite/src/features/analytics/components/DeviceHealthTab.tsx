/**
 * Device Health Tab Component
 *
 * LAYER 1: PRESENTATION
 * Displays REAL device health analytics data from device_health_metrics table
 *
 * Features:
 * - Fleet health score
 * - Device status breakdown
 * - Resource usage trends
 * - Individual device summaries
 */

import { lazy, Suspense } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Activity,
  Cpu,
  HardDrive,
  Server,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Wifi,
} from 'lucide-react';
import type { DeviceHealthTrend, DeviceHealthSummary } from '../types';

// Lazy load chart component
const DeviceHealthChart = lazy(() =>
  import('./DeviceHealthChart').then((module) => ({
    default: module.DeviceHealthChart,
  }))
);

interface DeviceHealthTabProps {
  data: DeviceHealthTrend | undefined;
  isLoading: boolean;
}

// Chart skeleton
function ChartSkeleton() {
  return (
    <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse" />
  );
}

// Fleet health score gauge
function FleetHealthGauge({
  score,
  isLoading,
}: {
  score: number;
  isLoading: boolean;
}) {
  const { t } = useTranslation();

  const getScoreColor = (s: number) => {
    if (s >= 80) return 'text-green-600 dark:text-green-400';
    if (s >= 50) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getScoreLabel = (s: number) => {
    if (s >= 80) return t('analytics.deviceHealth.excellent', 'Excellent');
    if (s >= 50) return t('analytics.deviceHealth.fair', 'Fair');
    return t('analytics.deviceHealth.poor', 'Poor');
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 text-center">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        {t('analytics.deviceHealth.fleetHealth', 'Fleet Health Score')}
      </h3>
      {isLoading ? (
        <div className="h-24 w-24 mx-auto bg-gray-200 dark:bg-gray-700 rounded-full animate-pulse" />
      ) : (
        <div className="relative inline-flex items-center justify-center">
          <svg className="w-32 h-32 transform -rotate-90">
            <circle
              cx="64"
              cy="64"
              r="56"
              stroke="currentColor"
              strokeWidth="8"
              fill="none"
              className="text-gray-200 dark:text-gray-700"
            />
            <circle
              cx="64"
              cy="64"
              r="56"
              stroke="currentColor"
              strokeWidth="8"
              fill="none"
              strokeDasharray={`${(score / 100) * 352} 352`}
              strokeLinecap="round"
              className={getScoreColor(score)}
            />
          </svg>
          <div className="absolute">
            <span className={`text-3xl font-bold ${getScoreColor(score)}`}>{score}</span>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {getScoreLabel(score)}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

// Device status cards
function DeviceStatusCards({
  healthy,
  warning,
  critical,
  isLoading,
}: {
  healthy: number;
  warning: number;
  critical: number;
  isLoading: boolean;
}) {
  const { t } = useTranslation();
  const total = healthy + warning + critical;

  const statuses = [
    {
      label: t('analytics.deviceHealth.healthy', 'Healthy'),
      value: healthy,
      icon: CheckCircle,
      color: 'text-green-600 dark:text-green-400',
      bgColor: 'bg-green-100 dark:bg-green-900/30',
    },
    {
      label: t('analytics.deviceHealth.warning', 'Warning'),
      value: warning,
      icon: AlertTriangle,
      color: 'text-yellow-600 dark:text-yellow-400',
      bgColor: 'bg-yellow-100 dark:bg-yellow-900/30',
    },
    {
      label: t('analytics.deviceHealth.critical', 'Critical'),
      value: critical,
      icon: XCircle,
      color: 'text-red-600 dark:text-red-400',
      bgColor: 'bg-red-100 dark:bg-red-900/30',
    },
  ];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        {t('analytics.deviceHealth.deviceStatus', 'Device Status')}
      </h3>
      <div className="grid grid-cols-3 gap-4">
        {statuses.map((status) => {
          const Icon = status.icon;
          return (
            <div key={status.label} className="text-center">
              <div className={`inline-flex p-3 rounded-full ${status.bgColor} mb-2`}>
                <Icon className={`w-6 h-6 ${status.color}`} />
              </div>
              {isLoading ? (
                <div className="h-8 w-12 mx-auto bg-gray-200 dark:bg-gray-700 animate-pulse rounded" />
              ) : (
                <>
                  <p className={`text-2xl font-bold ${status.color}`}>{status.value}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{status.label}</p>
                </>
              )}
            </div>
          );
        })}
      </div>
      {!isLoading && total > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex h-2 rounded-full overflow-hidden">
            <div
              className="bg-green-500"
              style={{ width: `${(healthy / total) * 100}%` }}
            />
            <div
              className="bg-yellow-500"
              style={{ width: `${(warning / total) * 100}%` }}
            />
            <div
              className="bg-red-500"
              style={{ width: `${(critical / total) * 100}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}

// Resource usage card
function ResourceUsageCard({
  label,
  value,
  icon: Icon,
  iconColor,
  isLoading,
}: {
  label: string;
  value: number;
  icon: React.ElementType;
  iconColor: string;
  isLoading: boolean;
}) {
  const getUsageColor = (v: number) => {
    if (v >= 90) return 'text-red-600 dark:text-red-400';
    if (v >= 70) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-green-600 dark:text-green-400';
  };

  const getBarColor = (v: number) => {
    if (v >= 90) return 'bg-red-500';
    if (v >= 70) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Icon className={`w-5 h-5 ${iconColor}`} />
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{label}</span>
        </div>
        {isLoading ? (
          <div className="h-6 w-12 bg-gray-200 dark:bg-gray-700 animate-pulse rounded" />
        ) : (
          <span className={`text-lg font-bold ${getUsageColor(value)}`}>{value}%</span>
        )}
      </div>
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all duration-500 ${getBarColor(value)}`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}

// Device health status badge
function DeviceStatusBadge({ status }: { status: 'healthy' | 'warning' | 'critical' }) {
  const colors = {
    healthy: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
    warning: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300',
    critical: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300',
  };

  return (
    <span className={`text-xs px-2 py-0.5 rounded-full ${colors[status]}`}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

// Device summary row
function DeviceSummaryRow({ device }: { device: DeviceHealthSummary }) {
  return (
    <div className="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Server className="w-5 h-5 text-gray-400" />
          <div>
            <p className="text-sm font-medium text-gray-900 dark:text-white">
              {device.device_name}
            </p>
            <DeviceStatusBadge status={device.status} />
          </div>
        </div>
        <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
          <span title="CPU">
            <Cpu className="w-3 h-3 inline mr-1" />
            {device.latest_cpu_usage?.toFixed(1) || '-'}%
          </span>
          <span title="Memory">
            <Activity className="w-3 h-3 inline mr-1" />
            {device.latest_memory_usage?.toFixed(1) || '-'}%
          </span>
          <span title="Disk">
            <HardDrive className="w-3 h-3 inline mr-1" />
            {device.latest_disk_usage?.toFixed(1) || '-'}%
          </span>
          <span className="font-semibold text-gray-700 dark:text-gray-300">
            Score: {device.health_score}
          </span>
        </div>
      </div>
    </div>
  );
}

export function DeviceHealthTab({ data, isLoading }: DeviceHealthTabProps) {
  const { t } = useTranslation();

  return (
    <div className="space-y-6">
      {/* Top Row: Fleet Health Score + Device Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <FleetHealthGauge score={data?.fleet_health_score || 0} isLoading={isLoading} />
        <DeviceStatusCards
          healthy={data?.devices_healthy || 0}
          warning={data?.devices_warning || 0}
          critical={data?.devices_critical || 0}
          isLoading={isLoading}
        />
      </div>

      {/* Average Resource Usage */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {t('analytics.deviceHealth.avgResourceUsage', 'Average Resource Usage')}
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <ResourceUsageCard
            label={t('analytics.deviceHealth.cpu', 'CPU Usage')}
            value={data?.avg_cpu_usage || 0}
            icon={Cpu}
            iconColor="text-blue-500"
            isLoading={isLoading}
          />
          <ResourceUsageCard
            label={t('analytics.deviceHealth.memory', 'Memory Usage')}
            value={data?.avg_memory_usage || 0}
            icon={Activity}
            iconColor="text-purple-500"
            isLoading={isLoading}
          />
          <ResourceUsageCard
            label={t('analytics.deviceHealth.disk', 'Disk Usage')}
            value={data?.avg_disk_usage || 0}
            icon={HardDrive}
            iconColor="text-green-500"
            isLoading={isLoading}
          />
        </div>
      </div>

      {/* Resource Usage Trend Chart */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <Wifi className="w-5 h-5" />
          {t('analytics.deviceHealth.usageTrend', 'Resource Usage Trend')}
        </h3>
        <Suspense fallback={<ChartSkeleton />}>
          <DeviceHealthChart data={data?.daily_trend || []} isLoading={isLoading} />
        </Suspense>
      </div>

      {/* Device Summaries */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <Server className="w-5 h-5" />
          {t('analytics.deviceHealth.deviceSummaries', 'Device Health Summaries')}
        </h3>
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-gray-200 dark:bg-gray-700 animate-pulse rounded" />
            ))}
          </div>
        ) : data?.device_summaries && data.device_summaries.length > 0 ? (
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {data.device_summaries.map((device) => (
              <DeviceSummaryRow key={device.device_id} device={device} />
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <Server className="w-12 h-12 text-gray-400 dark:text-gray-500 mb-3" />
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t('analytics.deviceHealth.noDeviceData', 'No device health data available')}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default DeviceHealthTab;
