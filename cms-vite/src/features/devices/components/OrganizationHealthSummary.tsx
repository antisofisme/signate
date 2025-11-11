/**
 * Organization Health Summary Component
 *
 * LAYER 1: PRESENTATION
 * Organization-wide device health overview widget
 */

import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  XCircle,
  WifiOff,
  Cpu,
  HardDrive,
  MemoryStick,
  TrendingUp,
  Loader2,
} from 'lucide-react';
import { deviceHealthApi } from '../api/health';
import type { OrganizationHealthSummary as OrgHealthSummaryType } from '../types/health';

interface OrganizationHealthSummaryProps {
  organizationId: number;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export function OrganizationHealthSummary({
  organizationId,
  autoRefresh = true,
  refreshInterval = 60000, // 60 seconds
}: OrganizationHealthSummaryProps) {
  const { data: summary, isLoading } = useQuery<OrgHealthSummaryType>({
    queryKey: ['org-health-summary', organizationId],
    queryFn: () => deviceHealthApi.getOrganizationSummary(organizationId),
    refetchInterval: autoRefresh ? refreshInterval : false,
    staleTime: 50000,
  });

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <div className="flex items-center justify-center h-32">
          <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
        </div>
      </div>
    );
  }

  if (!summary) {
    return null;
  }

  const healthyPercentage =
    summary.total_devices > 0
      ? Math.round((summary.healthy_devices / summary.total_devices) * 100)
      : 0;

  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-900 border border-blue-200 dark:border-gray-700 rounded-lg p-6 shadow-sm">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="p-3 bg-blue-600 rounded-lg">
          <Activity className="w-6 h-6 text-white" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Organization Health
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Fleet-wide device monitoring
          </p>
        </div>
      </div>

      {/* Device Status Overview */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        {/* Total Devices */}
        <StatCard
          icon={<Activity className="w-5 h-5" />}
          label="Total"
          value={summary.total_devices}
          color="text-gray-600 dark:text-gray-400"
          bgColor="bg-gray-100 dark:bg-gray-800"
        />

        {/* Healthy */}
        <StatCard
          icon={<CheckCircle className="w-5 h-5" />}
          label="Healthy"
          value={summary.healthy_devices}
          color="text-green-600 dark:text-green-400"
          bgColor="bg-green-100 dark:bg-green-900/30"
        />

        {/* Warning */}
        <StatCard
          icon={<AlertTriangle className="w-5 h-5" />}
          label="Warning"
          value={summary.warning_devices}
          color="text-yellow-600 dark:text-yellow-400"
          bgColor="bg-yellow-100 dark:bg-yellow-900/30"
        />

        {/* Critical */}
        <StatCard
          icon={<XCircle className="w-5 h-5" />}
          label="Critical"
          value={summary.critical_devices}
          color="text-red-600 dark:text-red-400"
          bgColor="bg-red-100 dark:bg-red-900/30"
        />

        {/* Offline */}
        <StatCard
          icon={<WifiOff className="w-5 h-5" />}
          label="Offline"
          value={summary.offline_devices}
          color="text-gray-600 dark:text-gray-400"
          bgColor="bg-gray-100 dark:bg-gray-800"
        />
      </div>

      {/* Health Progress Bar */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Overall Health
          </span>
          <span className="text-sm font-bold text-gray-900 dark:text-white">
            {healthyPercentage}%
          </span>
        </div>
        <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-green-500 to-green-600 transition-all duration-500"
            style={{ width: `${healthyPercentage}%` }}
          />
        </div>
      </div>

      {/* Average Metrics */}
      <div className="grid grid-cols-3 gap-4">
        {/* Avg CPU */}
        <MetricCard
          icon={<Cpu className="w-4 h-4" />}
          label="Avg CPU"
          value={
            summary.avg_cpu_usage !== undefined && summary.avg_cpu_usage !== null
              ? `${summary.avg_cpu_usage.toFixed(1)}%`
              : 'N/A'
          }
          isWarning={
            summary.avg_cpu_usage !== undefined && summary.avg_cpu_usage > 70
          }
        />

        {/* Avg Memory */}
        <MetricCard
          icon={<MemoryStick className="w-4 h-4" />}
          label="Avg Memory"
          value={
            summary.avg_memory_usage !== undefined && summary.avg_memory_usage !== null
              ? `${summary.avg_memory_usage.toFixed(1)}%`
              : 'N/A'
          }
          isWarning={
            summary.avg_memory_usage !== undefined && summary.avg_memory_usage > 80
          }
        />

        {/* Avg Disk */}
        <MetricCard
          icon={<HardDrive className="w-4 h-4" />}
          label="Avg Disk"
          value={
            summary.avg_disk_usage !== undefined && summary.avg_disk_usage !== null
              ? `${summary.avg_disk_usage.toFixed(1)}%`
              : 'N/A'
          }
          isWarning={
            summary.avg_disk_usage !== undefined && summary.avg_disk_usage > 85
          }
        />
      </div>

      {/* Devices with Errors */}
      {summary.devices_with_errors > 0 && (
        <div className="mt-4 p-3 bg-yellow-100 dark:bg-yellow-900/30 border border-yellow-300 dark:border-yellow-700 rounded-lg">
          <div className="flex items-center gap-2 text-yellow-800 dark:text-yellow-200">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span className="text-sm font-medium">
              {summary.devices_with_errors} device{summary.devices_with_errors !== 1 ? 's' : ''}{' '}
              reporting errors
            </span>
          </div>
        </div>
      )}

      {/* No Data State */}
      {summary.total_devices === 0 && (
        <div className="text-center py-6">
          <TrendingUp className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
          <p className="text-gray-600 dark:text-gray-400 text-sm">
            No devices reporting health data yet
          </p>
        </div>
      )}
    </div>
  );
}

// Stat Card Component
interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: string;
  bgColor: string;
}

function StatCard({ icon, label, value, color, bgColor }: StatCardProps) {
  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3">
      <div className={`${bgColor} ${color} w-10 h-10 rounded-lg flex items-center justify-center mb-2`}>
        {icon}
      </div>
      <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
      <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">{label}</p>
    </div>
  );
}

// Metric Card Component
interface MetricCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  isWarning: boolean;
}

function MetricCard({ icon, label, value, isWarning }: MetricCardProps) {
  return (
    <div
      className={`p-3 rounded-lg border ${
        isWarning
          ? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800'
          : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700'
      }`}
    >
      <div className="flex items-center gap-2 mb-1">
        <div
          className={`${
            isWarning
              ? 'text-yellow-600 dark:text-yellow-400'
              : 'text-gray-600 dark:text-gray-400'
          }`}
        >
          {icon}
        </div>
        <span className="text-xs text-gray-600 dark:text-gray-400">{label}</span>
      </div>
      <p
        className={`text-lg font-bold ${
          isWarning
            ? 'text-yellow-900 dark:text-yellow-100'
            : 'text-gray-900 dark:text-white'
        }`}
      >
        {value}
      </p>
    </div>
  );
}
