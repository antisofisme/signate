/**
 * Overview Metrics Component
 *
 * LAYER 1: PRESENTATION
 * Dashboard overview statistics cards
 */

import { Monitor, FileImage, ListVideo, UtensilsCrossed, Calendar, Activity } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { DashboardStats, MenuStats, ScheduleOverview } from '../api/dashboard.api';

interface OverviewMetricsProps {
  stats: DashboardStats | undefined;
  menuStats: MenuStats | undefined;
  scheduleOverview: ScheduleOverview | undefined;
  isLoading: boolean;
}

interface MetricCardProps {
  icon: React.ElementType;
  iconColor: string;
  label: string;
  value: string | number;
  subtitle?: string;
  isLoading: boolean;
}

const MetricCard = ({ icon: Icon, iconColor, label, value, subtitle, isLoading }: MetricCardProps) => {
  const colorMap = {
    blue: 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
    green: 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400',
    purple: 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400',
    orange: 'bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400',
    indigo: 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400',
    pink: 'bg-pink-100 dark:bg-pink-900/30 text-pink-600 dark:text-pink-400',
  };
  const iconColorClasses = colorMap[iconColor] || colorMap.blue;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-center gap-4">
        <div className={`p-3 rounded-lg ${iconColorClasses}`}>
          <Icon className="w-6 h-6" />
        </div>
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{label}</p>
          {isLoading ? (
            <div className="h-8 w-20 bg-gray-200 dark:bg-gray-700 animate-pulse rounded mt-1" />
          ) : (
            <>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{value}</p>
              {subtitle && (
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{subtitle}</p>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};

export default function OverviewMetrics({ stats, menuStats, scheduleOverview, isLoading }: OverviewMetricsProps) {
  const { t } = useTranslation();
  const onlinePercentage = stats?.total_devices
    ? Math.round((stats.online_devices / stats.total_devices) * 100)
    : 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {/* Total Devices */}
      <MetricCard
        icon={Monitor}
        iconColor="blue"
        label={t('dashboard.metrics.totalDevices', 'Total Devices')}
        value={stats?.total_devices || 0}
        subtitle={t('dashboard.metrics.onlineDevices', { online: stats?.online_devices || 0, percentage: onlinePercentage })}
        isLoading={isLoading}
      />

      {/* Total Content */}
      <MetricCard
        icon={FileImage}
        iconColor="green"
        label={t('dashboard.metrics.totalContent', 'Total Content')}
        value={stats?.total_contents || 0}
        subtitle={stats ? formatBytes(stats.total_storage_bytes) : '0 B'}
        isLoading={isLoading}
      />

      {/* Active Playlists */}
      <MetricCard
        icon={ListVideo}
        iconColor="purple"
        label={t('dashboard.metrics.activePlaylists', 'Active Playlists')}
        value={stats?.active_playlists || 0}
        subtitle={t('dashboard.metrics.playbackEventsCount', { count: stats?.total_playback_events || 0 })}
        isLoading={isLoading}
      />

      {/* Total Menus - NEW */}
      <MetricCard
        icon={UtensilsCrossed}
        iconColor="orange"
        label={t('dashboard.metrics.totalMenus', 'Digital Menus')}
        value={menuStats?.total_menus || 0}
        subtitle={t('dashboard.metrics.activeMenus', { active: menuStats?.active_menus || 0, items: menuStats?.total_items || 0 })}
        isLoading={isLoading}
      />

      {/* Active Schedules - NEW */}
      <MetricCard
        icon={Calendar}
        iconColor="indigo"
        label={t('dashboard.metrics.activeSchedules', 'Schedules')}
        value={scheduleOverview?.active_schedules || 0}
        subtitle={t('dashboard.metrics.runningNow', { running: scheduleOverview?.running_now || 0, ending: scheduleOverview?.ending_soon || 0 })}
        isLoading={isLoading}
      />

      {/* Menu Views - NEW */}
      <MetricCard
        icon={Activity}
        iconColor="pink"
        label={t('dashboard.metrics.menuViews', 'Menu Views')}
        value={menuStats?.total_views || 0}
        subtitle={t('dashboard.metrics.contactClicks', { clicks: menuStats?.total_contact_clicks || 0 })}
        isLoading={isLoading}
      />
    </div>
  );
}
