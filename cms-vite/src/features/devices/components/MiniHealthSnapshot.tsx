/**
 * Mini Health Snapshot Component
 * Displays quick health metrics (CPU, Memory, Disk) in Overview tab
 *
 * Features:
 * - Auto-refresh every 30 seconds (when device online)
 * - Color-coded status indicators (green/yellow/red)
 * - Multiple states: loading, offline, no-data, success
 * - Translation support (EN/ID)
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Activity, ChevronRight } from 'lucide-react';
import { deviceHealthApi } from '../api/health';
import type { DeviceHealthMetrics } from '../types/health';

interface MiniHealthSnapshotProps {
  deviceId: number;
  isOnline: boolean;
  onViewDetails?: () => void;
}

export function MiniHealthSnapshot({
  deviceId,
  isOnline,
  onViewDetails
}: MiniHealthSnapshotProps) {
  const { t } = useTranslation();
  const [health, setHealth] = useState<DeviceHealthMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch health data
  const fetchHealth = async () => {
    if (!isOnline) {
      setHealth(null);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    const data = await deviceHealthApi.getLatestHealth(deviceId);
    setHealth(data);
    setIsLoading(false);
  };

  // Initial fetch + auto-refresh
  useEffect(() => {
    fetchHealth();

    if (isOnline) {
      const interval = setInterval(fetchHealth, 30000); // 30s
      return () => clearInterval(interval);
    }
  }, [deviceId, isOnline]);

  // Calculate overall status based on highest metric
  const getOverallStatus = (): 'healthy' | 'warning' | 'critical' => {
    if (!health) return 'healthy';
    const maxUsage = Math.max(
      health.cpu_usage || 0,
      health.memory_usage || 0,
      health.disk_usage || 0
    );
    if (maxUsage >= 85) return 'critical';
    if (maxUsage >= 70) return 'warning';
    return 'healthy';
  };

  // Get color class for metric
  const getMetricColor = (value?: number) => {
    if (!value) return 'text-gray-400';
    if (value >= 85) return 'text-red-500 dark:text-red-400';
    if (value >= 70) return 'text-yellow-500 dark:text-yellow-400';
    return 'text-green-500 dark:text-green-400';
  };

  // Format last updated time
  const getLastUpdatedText = () => {
    if (!health?.recorded_at) return '';
    const diff = Date.now() - new Date(health.recorded_at).getTime();
    const minutes = Math.floor(diff / 60000);
    if (minutes < 1) return t('devices.health.justNow');
    return t('devices.health.minutesAgo', { count: minutes });
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24"></div>
          <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-full"></div>
          <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
        </div>
      </div>
    );
  }

  // Offline state
  if (!isOnline) {
    return (
      <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
          <Activity className="w-4 h-4" />
          {t('devices.health.snapshot')}
        </h4>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          {t('devices.health.deviceOffline')}
        </p>
      </div>
    );
  }

  // No data state
  if (!health) {
    return (
      <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
          <Activity className="w-4 h-4" />
          {t('devices.health.snapshot')}
        </h4>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          {t('devices.health.noDataAvailable')}
        </p>
      </div>
    );
  }

  const status = getOverallStatus();
  const statusColors = {
    healthy: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
    warning: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400',
    critical: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
  };

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
      {/* Header with Status Badge */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-gray-700 dark:text-gray-300" />
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusColors[status]}`}>
            {status.charAt(0).toUpperCase() + status.slice(1)}
          </span>
        </div>
        <span className="text-xs text-gray-500 dark:text-gray-400">
          {getLastUpdatedText()}
        </span>
      </div>

      {/* Metrics */}
      <div className="space-y-1.5 mb-3">
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-600 dark:text-gray-400 flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${getMetricColor(health.cpu_usage)}`}></span>
            CPU:
          </span>
          <span className={`font-medium ${getMetricColor(health.cpu_usage)}`}>
            {health.cpu_usage !== undefined ? `${health.cpu_usage.toFixed(1)}%` : 'N/A'}
          </span>
        </div>

        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-600 dark:text-gray-400 flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${getMetricColor(health.memory_usage)}`}></span>
            Memory:
          </span>
          <span className={`font-medium ${getMetricColor(health.memory_usage)}`}>
            {health.memory_usage !== undefined ? `${health.memory_usage.toFixed(1)}%` : 'N/A'}
          </span>
        </div>

        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-600 dark:text-gray-400 flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${getMetricColor(health.disk_usage)}`}></span>
            Disk:
          </span>
          <span className={`font-medium ${getMetricColor(health.disk_usage)}`}>
            {health.disk_usage !== undefined ? `${health.disk_usage.toFixed(1)}%` : 'N/A'}
          </span>
        </div>
      </div>

      {/* View Details Link */}
      {onViewDetails && (
        <button
          onClick={onViewDetails}
          className="w-full text-xs text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 flex items-center justify-center gap-1 pt-2 border-t border-gray-200 dark:border-gray-700"
        >
          {t('devices.health.viewDetails')}
          <ChevronRight className="w-3 h-3" />
        </button>
      )}
    </div>
  );
}
