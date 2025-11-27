/**
 * Analytics Page (Reports Center)
 * Historical analytics and reporting - differentiated from Dashboard (real-time)
 *
 * Focus: Historical trends, period comparisons, exports
 * (Dashboard focuses on real-time monitoring)
 *
 * PERFORMANCE: Chart components are lazy loaded to reduce initial bundle size
 */

import { useState, useCallback, useMemo, lazy, Suspense } from 'react';
import { useTranslation } from 'react-i18next';
import { PageHeader, PageSkeleton, AccessDenied, RefreshButton } from '@/shared/components';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import { AnalyticsOverview } from '../components/AnalyticsOverview';
import { DateRangePicker, type DateRange } from '../components/DateRangePicker';
import { ExportButtons } from '../components/ExportButtons';
import { TopContentTable } from '../components/TopContentTable';
import { DeviceEngagementTable } from '../components/DeviceEngagementTable';
import {
  useAnalyticsStats,
  useContentPerformance,
  usePlaybackTimeline,
  useDeviceEngagement,
} from '../hooks';

// Lazy load chart component (Recharts is ~220 KB)
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

// Convert date range to query params
function getDateRangeParams(range: DateRange) {
  const now = new Date();
  const end = now.toISOString().split('T')[0];
  let start: string;

  switch (range) {
    case '7d':
      start = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
      break;
    case '30d':
      start = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
      break;
    case '90d':
      start = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
      break;
    default:
      start = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
  }

  return { start_date: start, end_date: end };
}

// Get interval based on date range
function getIntervalForRange(range: DateRange): 'day' | 'week' | 'month' {
  switch (range) {
    case '7d':
      return 'day';
    case '30d':
      return 'day';
    case '90d':
      return 'week';
    default:
      return 'day';
  }
}

export default function AnalyticsPage() {
  const { t } = useTranslation();

  // Permission check
  const { hasPermission: canView, isLoading: isCheckingPermission } = useCanPerformAction('analytics', 'view');

  const [dateRange, setDateRange] = useState<DateRange>('30d');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  // Calculate query params based on date range
  const queryParams = useMemo(() => getDateRangeParams(dateRange), [dateRange]);
  const interval = useMemo(() => getIntervalForRange(dateRange), [dateRange]);

  // Fetch analytics data
  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useAnalyticsStats(queryParams);
  const { data: contentPerformance, isLoading: contentLoading, refetch: refetchContent } = useContentPerformance({
    ...queryParams,
    limit: 10,
  });
  const { data: timeline, isLoading: timelineLoading, refetch: refetchTimeline } = usePlaybackTimeline({
    ...queryParams,
    interval,
  });
  const { data: deviceEngagement, isLoading: deviceLoading, refetch: refetchDevices } = useDeviceEngagement({
    ...queryParams,
    limit: 10,
  });

  // Combined refresh handler
  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await Promise.all([
        refetchStats(),
        refetchContent(),
        refetchTimeline(),
        refetchDevices(),
      ]);
    } finally {
      setIsRefreshing(false);
    }
  }, [refetchStats, refetchContent, refetchTimeline, refetchDevices]);

  // Export handlers (placeholder - implement actual export logic)
  const handleExportPDF = useCallback(async () => {
    setIsExporting(true);
    try {
      // TODO: Implement PDF export
      console.log('Exporting PDF with data:', { stats, contentPerformance, timeline, deviceEngagement });
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate export
      alert(t('analytics.exportSuccess', 'Report exported successfully!'));
    } catch {
      alert(t('analytics.exportError', 'Failed to export report'));
    } finally {
      setIsExporting(false);
    }
  }, [stats, contentPerformance, timeline, deviceEngagement, t]);

  const handleExportExcel = useCallback(async () => {
    setIsExporting(true);
    try {
      // TODO: Implement Excel export
      console.log('Exporting Excel with data:', { stats, contentPerformance, deviceEngagement });
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate export
      alert(t('analytics.exportSuccess', 'Report exported successfully!'));
    } catch {
      alert(t('analytics.exportError', 'Failed to export report'));
    } finally {
      setIsExporting(false);
    }
  }, [stats, contentPerformance, deviceEngagement, t]);

  // Loading state while checking permissions
  if (isCheckingPermission) {
    return <PageSkeleton />;
  }

  // Access denied if user doesn't have view permission
  if (!canView) {
    return <AccessDenied />;
  }

  return (
    <>
      <PageHeader
        title={t('analytics.title', 'Analytics & Reports')}
        description={t('analytics.description', 'Historical trends, content performance, and engagement metrics')}
      />

      {/* Action Bar */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <DateRangePicker value={dateRange} onChange={setDateRange} />

        <div className="flex items-center gap-4">
          <ExportButtons
            onExportPDF={handleExportPDF}
            onExportExcel={handleExportExcel}
            isExporting={isExporting}
          />
          <RefreshButton
            onClick={handleRefresh}
            isLoading={isRefreshing}
            label={t('common.refresh', 'Refresh')}
          />
        </div>
      </div>

      {/* Content */}
      <div className="space-y-6">
        {/* Stats Overview with Period Comparison */}
        <AnalyticsOverview stats={stats!} isLoading={statsLoading} />

        {/* Playback Trend Chart - Full Width */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {t('analytics.playbackTrend', 'Playback Trend')}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {t('analytics.playbackTrendDesc', 'Activity over time for the selected period')}
              </p>
            </div>
          </div>
          <Suspense fallback={<ChartSkeleton />}>
            <PlaybackTimelineChart
              data={timeline || []}
              isLoading={timelineLoading}
              variant="area"
            />
          </Suspense>
        </div>

        {/* Two Column Layout: Top Content + Device Activity */}
        <div className="grid gap-6 lg:grid-cols-2">
          <TopContentTable data={contentPerformance || []} isLoading={contentLoading} />
          <DeviceEngagementTable data={deviceEngagement || []} isLoading={deviceLoading} />
        </div>

        {/* Period Summary */}
        <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 bg-blue-50 dark:bg-blue-900/20">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white">
                {t('analytics.reportPeriod', 'Report Period')}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {stats?.period_start && stats?.period_end ? (
                  <>
                    {new Date(stats.period_start).toLocaleDateString()} - {new Date(stats.period_end).toLocaleDateString()}
                  </>
                ) : (
                  t('analytics.showingSelectedPeriod', 'Showing data for selected period')
                )}
              </p>
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              <span className="text-blue-600 dark:text-blue-400 font-medium">
                {t('analytics.tip', 'Tip')}:
              </span>{' '}
              {t('analytics.useDashboard', 'For real-time monitoring, use the Dashboard')}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
