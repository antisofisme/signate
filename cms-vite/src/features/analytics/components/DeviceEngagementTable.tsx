/**
 * DeviceEngagementTable Component
 * Display device engagement and activity metrics
 */

import { Monitor, Play, Clock, Activity, CheckCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { DeviceEngagement } from '../types';

interface DeviceEngagementTableProps {
  data: DeviceEngagement[];
  isLoading?: boolean;
  limit?: number;
}

export function DeviceEngagementTable({ data, isLoading, limit = 10 }: DeviceEngagementTableProps) {
  const { t } = useTranslation();

  const formatHours = (seconds: number) => {
    const hours = seconds / 3600;
    if (hours < 1) {
      return `${Math.round(seconds / 60)}m`;
    }
    return `${hours.toFixed(1)}h`;
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('id-ID').format(num);
  };

  if (isLoading) {
    return (
      <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm">
        <div className="p-6 pb-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-blue-500" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              {t('analytics.deviceActivity', 'Device Activity')}
            </h3>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            {t('analytics.deviceActivityDesc', 'Device engagement metrics')}
          </p>
        </div>
        <div className="p-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex items-center gap-4 py-3 animate-pulse">
              <div className="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded-lg" />
              <div className="flex-1">
                <div className="h-4 w-32 bg-gray-200 dark:bg-gray-700 rounded" />
                <div className="h-3 w-48 bg-gray-200 dark:bg-gray-700 rounded mt-2" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm">
        <div className="p-6 pb-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-blue-500" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              {t('analytics.deviceActivity', 'Device Activity')}
            </h3>
          </div>
        </div>
        <div className="p-8 text-center text-gray-500 dark:text-gray-400">
          {t('analytics.noDeviceData', 'No device activity data available')}
        </div>
      </div>
    );
  }

  const displayData = data.slice(0, limit);

  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm">
      <div className="p-6 pb-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-blue-500" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {t('analytics.deviceActivity', 'Device Activity')}
          </h3>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          {t('analytics.deviceActivityDesc', 'Device engagement metrics')}
        </p>
      </div>
      <div className="divide-y divide-gray-200 dark:divide-gray-700">
        {displayData.map((device, index) => {
          const avgPlaysPerContent = device.avg_plays_per_content ??
            (device.unique_content > 0 ? device.total_plays / device.unique_content : 0);

          return (
            <div
              key={device.device_id}
              className="flex items-center gap-4 p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
            >
              {/* Device Icon */}
              <div className="flex items-center justify-center w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <Monitor className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>

              {/* Device Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h4 className="font-medium text-gray-900 dark:text-white truncate">
                    {device.device_name}
                  </h4>
                  {device.is_active && (
                    <span className="flex items-center gap-1 px-1.5 py-0.5 text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded">
                      <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
                      Active
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-4 mt-1 text-sm text-gray-500 dark:text-gray-400">
                  <span className="flex items-center gap-1">
                    <Play className="h-3 w-3" />
                    {formatNumber(device.total_plays)} {t('analytics.plays', 'plays')}
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatHours(device.total_watch_time_seconds)}
                  </span>
                  <span className="flex items-center gap-1">
                    <CheckCircle className="h-3 w-3" />
                    {device.unique_content} {t('analytics.content', 'content')}
                  </span>
                </div>
              </div>

              {/* Engagement Score / Avg plays */}
              <div className="text-right">
                <div className="text-lg font-semibold text-gray-900 dark:text-white">
                  {avgPlaysPerContent.toFixed(1)}x
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {t('analytics.avgPerContent', 'avg/content')}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
