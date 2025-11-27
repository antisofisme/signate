/**
 * Analytics Page (Standalone)
 * Main analytics dashboard - standalone feature like Digital Menus
 *
 * NOTE: Auto-polling removed for performance optimization.
 * Use the Refresh button to manually update data.
 *
 * PERFORMANCE: Chart components are lazy loaded to reduce initial bundle size
 * by ~220 KB (Recharts library is loaded on demand)
 */

import { useState, useCallback, lazy, Suspense } from 'react';
import { RefreshCw } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { PageHeader } from '@/shared/components';
import { AnalyticsOverview } from '../components/AnalyticsOverview';
import {
  useAnalyticsStats,
  useContentPerformance,
  usePlaybackTimeline,
} from '../hooks';

// Lazy load chart components (Recharts is ~220 KB)
const ContentPerformanceChart = lazy(() =>
  import('../components/ContentPerformanceChart').then((module) => ({
    default: module.ContentPerformanceChart,
  }))
);
const PlaybackTimelineChart = lazy(() =>
  import('../components/PlaybackTimelineChart').then((module) => ({
    default: module.PlaybackTimelineChart,
  }))
);

// Loading skeleton for charts
function ChartSkeleton() {
  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm">
      <div className="p-6 pb-4">
        <div className="h-6 w-48 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
        <div className="h-4 w-64 bg-gray-200 dark:bg-gray-700 rounded mt-2 animate-pulse" />
      </div>
      <div className="p-6 pt-0">
        <div className="h-80 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse" />
      </div>
    </div>
  );
}

export default function AnalyticsPage() {
  const { t } = useTranslation();
  const [interval, setInterval] = useState<'day' | 'week' | 'month'>('day');
  const [limit, setLimit] = useState(10);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Fetch analytics data with refetch functions
  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useAnalyticsStats();
  const { data: contentPerformance, isLoading: contentLoading, refetch: refetchContent } = useContentPerformance({
    limit,
  });
  const { data: timeline, isLoading: timelineLoading, refetch: refetchTimeline } = usePlaybackTimeline({
    interval,
  });

  // Combined refresh handler
  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await Promise.all([
        refetchStats(),
        refetchContent(),
        refetchTimeline(),
      ]);
    } finally {
      setIsRefreshing(false);
    }
  }, [refetchStats, refetchContent, refetchTimeline]);

  return (
    <>
      <PageHeader
        title={t('analytics.title', 'Analytics & Reports')}
        description={t('analytics.description', 'Track content performance and device engagement')}
      />

      {/* Action Bar */}
      <div className="mb-6 flex justify-end">
        <button
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label={t('analytics.refresh', 'Refresh analytics data')}
        >
          <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          {isRefreshing ? t('common.refreshing', 'Refreshing...') : t('common.refresh', 'Refresh')}
        </button>
      </div>

      {/* Content */}
      <div className="space-y-6">
        {/* Stats Overview */}
        <AnalyticsOverview stats={stats!} isLoading={statsLoading} />

        {/* Charts Section - Lazy loaded for performance */}
        <div className="grid gap-4 md:grid-cols-2">
          <Suspense fallback={<ChartSkeleton />}>
            <ContentPerformanceChart data={contentPerformance || []} isLoading={contentLoading} />
          </Suspense>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {t('analytics.playbackTimeline', 'Playback Timeline')}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {t('analytics.activityOverTime', 'Activity over time')}
                </p>
              </div>
              <select
                value={interval}
                onChange={(e) => setInterval(e.target.value as 'day' | 'week' | 'month')}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label={t('analytics.selectInterval', 'Select time interval')}
              >
                <option value="day">{t('analytics.daily', 'Daily')}</option>
                <option value="week">{t('analytics.weekly', 'Weekly')}</option>
                <option value="month">{t('analytics.monthly', 'Monthly')}</option>
              </select>
            </div>
            <Suspense fallback={<ChartSkeleton />}>
              <PlaybackTimelineChart
                data={timeline || []}
                isLoading={timelineLoading}
                variant="area"
              />
            </Suspense>
          </div>
        </div>

        {/* Additional Info */}
        <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 bg-gray-50 dark:bg-gray-800/50">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white">
                {t('analytics.manualRefresh', 'Manual Refresh')}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {t('analytics.clickRefresh', 'Click the Refresh button above to update analytics data')}
              </p>
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              {stats?.period_start && stats?.period_end && (
                <span>
                  {t('analytics.showingLast30Days', 'Showing data from last 30 days')}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
