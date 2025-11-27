/**
 * AnalyticsOverview Component
 * Display overall statistics cards with trend comparisons
 */

import { Play, CheckCircle, FileVideo, Monitor, Clock, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { PlaybackStats } from '../types';

interface AnalyticsOverviewProps {
  stats: PlaybackStats;
  previousStats?: PlaybackStats;
  isLoading?: boolean;
}

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ElementType;
  description?: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
}

function StatCard({ title, value, icon: Icon, description, trend }: StatCardProps) {
  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm">
      <div className="flex flex-row items-center justify-between space-y-0 p-6 pb-2">
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">{title}</h3>
        <Icon className="h-4 w-4 text-gray-500 dark:text-gray-400" />
      </div>
      <div className="p-6 pt-0">
        <div className="text-2xl font-bold text-gray-900 dark:text-white">{value}</div>
        <div className="flex items-center gap-2 mt-1">
          {trend && (
            <span
              className={`flex items-center gap-1 text-xs font-medium ${
                trend.value === 0
                  ? 'text-gray-500 dark:text-gray-400'
                  : trend.isPositive
                  ? 'text-green-600 dark:text-green-400'
                  : 'text-red-600 dark:text-red-400'
              }`}
            >
              {trend.value === 0 ? (
                <Minus className="h-3 w-3" />
              ) : trend.isPositive ? (
                <TrendingUp className="h-3 w-3" />
              ) : (
                <TrendingDown className="h-3 w-3" />
              )}
              {trend.value > 0 ? '+' : ''}{trend.value.toFixed(1)}%
            </span>
          )}
          {description && (
            <span className="text-xs text-gray-600 dark:text-gray-400">{description}</span>
          )}
        </div>
      </div>
    </div>
  );
}

export function AnalyticsOverview({ stats, previousStats, isLoading }: AnalyticsOverviewProps) {
  const { t } = useTranslation();

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-32 animate-pulse bg-gray-200 dark:bg-gray-700 rounded-lg" />
        ))}
      </div>
    );
  }

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('id-ID').format(num);
  };

  const formatHours = (hours: number) => {
    if (hours < 1) {
      return `${Math.round(hours * 60)}m`;
    }
    return `${hours.toFixed(1)}h`;
  };

  // Calculate trend percentages
  const calculateTrend = (current: number, previous?: number) => {
    if (!previous || previous === 0) return undefined;
    const change = ((current - previous) / previous) * 100;
    return {
      value: change,
      isPositive: change >= 0,
    };
  };

  // Add null safety for all stats
  const safeStats = {
    total_plays: stats?.total_plays || 0,
    completed_plays: stats?.completed_plays || 0,
    unique_content: stats?.unique_content || 0,
    unique_devices: stats?.unique_devices || 0,
    total_watch_time_hours: stats?.total_watch_time_hours || 0,
    total_watch_time_seconds: stats?.total_watch_time_seconds || 0,
    completion_rate: stats?.completion_rate || 0,
  };

  const safePreviousStats = previousStats ? {
    total_plays: previousStats.total_plays || 0,
    completed_plays: previousStats.completed_plays || 0,
    unique_content: previousStats.unique_content || 0,
    unique_devices: previousStats.unique_devices || 0,
    total_watch_time_hours: previousStats.total_watch_time_hours || 0,
  } : undefined;

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
      <StatCard
        title={t('analytics.totalPlays', 'Total Plays')}
        value={formatNumber(safeStats.total_plays)}
        icon={Play}
        description={t('analytics.vsLastPeriod', 'vs last period')}
        trend={calculateTrend(safeStats.total_plays, safePreviousStats?.total_plays)}
      />

      <StatCard
        title={t('analytics.completed', 'Completed')}
        value={formatNumber(safeStats.completed_plays)}
        icon={CheckCircle}
        description={`${safeStats.completion_rate.toFixed(0)}% ${t('analytics.rate', 'rate')}`}
        trend={calculateTrend(safeStats.completed_plays, safePreviousStats?.completed_plays)}
      />

      <StatCard
        title={t('analytics.uniqueContent', 'Unique Content')}
        value={formatNumber(safeStats.unique_content)}
        icon={FileVideo}
        description={t('analytics.contentPlayed', 'content played')}
        trend={calculateTrend(safeStats.unique_content, safePreviousStats?.unique_content)}
      />

      <StatCard
        title={t('analytics.activeDevices', 'Active Devices')}
        value={formatNumber(safeStats.unique_devices)}
        icon={Monitor}
        description={t('analytics.withPlayback', 'with playback')}
        trend={calculateTrend(safeStats.unique_devices, safePreviousStats?.unique_devices)}
      />

      <StatCard
        title={t('analytics.watchTime', 'Watch Time')}
        value={formatHours(safeStats.total_watch_time_hours)}
        icon={Clock}
        description={`${formatNumber(Math.round(safeStats.total_watch_time_seconds))}s ${t('analytics.total', 'total')}`}
        trend={calculateTrend(safeStats.total_watch_time_hours, safePreviousStats?.total_watch_time_hours)}
      />
    </div>
  );
}
