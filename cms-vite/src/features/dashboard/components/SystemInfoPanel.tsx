/**
 * System Info Panel Component
 *
 * LAYER 1: PRESENTATION
 * System storage and resource information
 */

import { HardDrive, Database, FileImage, Video, File } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { SystemInfo } from '../api/dashboard.api';

interface SystemInfoPanelProps {
  data: SystemInfo | undefined;
  isLoading: boolean;
}

const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};

const formatUptime = (seconds: number): string => {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
};

const getContentIcon = (type: string) => {
  switch (type.toLowerCase()) {
    case 'image':
      return FileImage;
    case 'video':
      return Video;
    default:
      return File;
  }
};

export default function SystemInfoPanel({ data, isLoading }: SystemInfoPanelProps) {
  const { t } = useTranslation();
  const storageUsedPercentage = data
    ? Math.round((data.storage_used_bytes / data.storage_total_bytes) * 100)
    : 0;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
        <HardDrive className="w-5 h-5" />
        {t('dashboard.systemInfo.title', 'Storage & System Info')}
      </h2>

      {isLoading ? (
        <div className="space-y-4">
          <div className="h-24 bg-gray-200 dark:bg-gray-700 animate-pulse rounded-lg" />
          <div className="h-32 bg-gray-200 dark:bg-gray-700 animate-pulse rounded-lg" />
        </div>
      ) : data ? (
        <div className="space-y-6">
          {/* Storage Overview */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {t('dashboard.systemInfo.storageUsage', 'Storage Usage')}
              </span>
              <span className="text-sm font-semibold text-gray-900 dark:text-white">
                {formatBytes(data.storage_used_bytes)} / {formatBytes(data.storage_total_bytes)}
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
              <div
                className={`h-3 rounded-full transition-all ${
                  storageUsedPercentage >= 90
                    ? 'bg-red-500 dark:bg-red-600'
                    : storageUsedPercentage >= 70
                    ? 'bg-yellow-500 dark:bg-yellow-600'
                    : 'bg-green-500 dark:bg-green-600'
                }`}
                style={{ width: `${storageUsedPercentage}%` }}
              />
            </div>
            <div className="flex items-center justify-between mt-1 text-xs text-gray-500 dark:text-gray-400">
              <span>{t('dashboard.systemInfo.used', '{{percentage}}% used', { percentage: storageUsedPercentage })}</span>
              <span>{t('dashboard.systemInfo.free', '{{size}} free', { size: formatBytes(data.storage_free_bytes) })}</span>
            </div>
          </div>

          {/* Content Breakdown */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
              {t('dashboard.systemInfo.contentBreakdown', 'Content Breakdown')}
            </h3>
            <div className="space-y-3">
              {data.content_by_type.map((content) => {
                const Icon = getContentIcon(content.type);
                const percentage = data.storage_used_bytes
                  ? Math.round((content.size_bytes / data.storage_used_bytes) * 100)
                  : 0;

                return (
                  <div key={content.type} className="flex items-center gap-3">
                    <div className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
                      <Icon className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-gray-900 dark:text-white capitalize">
                          {content.type} ({content.count})
                        </span>
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {formatBytes(content.size_bytes)} ({percentage}%)
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                        <div
                          className="h-1.5 bg-blue-500 dark:bg-blue-600 rounded-full"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* System Stats */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                <Database className="w-4 h-4 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('dashboard.systemInfo.databaseSize', 'Database Size')}</p>
                <p className="text-sm font-semibold text-gray-900 dark:text-white">
                  {formatBytes(data.database_size_bytes)}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                <HardDrive className="w-4 h-4 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('dashboard.systemInfo.systemUptime', 'System Uptime')}</p>
                <p className="text-sm font-semibold text-gray-900 dark:text-white">
                  {formatUptime(data.uptime_seconds)}
                </p>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="py-8 text-center text-gray-500 dark:text-gray-400">
          {t('dashboard.systemInfo.noInfo', 'No system information available')}
        </div>
      )}
    </div>
  );
}
