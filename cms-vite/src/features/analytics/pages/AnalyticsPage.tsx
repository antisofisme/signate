/**
 * Analytics Page (Reports Center) - REDESIGNED
 *
 * Tab-based analytics with REAL data:
 * - Menu Analytics: Views, device breakdown, top menus (from menu_views table)
 * - Device Health: Fleet health, resource usage (from device_health_metrics table)
 *
 * Focus: Historical trends, period comparisons, meaningful metrics
 * (Dashboard focuses on real-time monitoring)
 *
 * PERFORMANCE: Chart components are lazy loaded to reduce initial bundle size
 */

import { useState, useCallback, useMemo, lazy, Suspense } from 'react';
import { useTranslation } from 'react-i18next';
import { UtensilsCrossed, Activity } from 'lucide-react';
import { PageHeader, PageSkeleton, AccessDenied, RefreshButton } from '@/shared/components';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import { DateRangePicker, type DateRange } from '../components/DateRangePicker';
import {
  useMenuAnalyticsTrends,
  useDeviceHealthTrends,
} from '../hooks';

// Lazy load tab components (they contain charts)
const MenuAnalyticsTab = lazy(() =>
  import('../components/MenuAnalyticsTab').then((module) => ({
    default: module.MenuAnalyticsTab,
  }))
);

const DeviceHealthTab = lazy(() =>
  import('../components/DeviceHealthTab').then((module) => ({
    default: module.DeviceHealthTab,
  }))
);

// Tab loading skeleton
function TabSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse" />
        <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse" />
      </div>
      <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse" />
    </div>
  );
}

// Tab definitions
type TabId = 'menu' | 'device-health';

interface Tab {
  id: TabId;
  labelKey: string;
  defaultLabel: string;
  icon: React.ElementType;
}

const TABS: Tab[] = [
  {
    id: 'menu',
    labelKey: 'analytics.tabs.menuAnalytics',
    defaultLabel: 'Menu Analytics',
    icon: UtensilsCrossed,
  },
  {
    id: 'device-health',
    labelKey: 'analytics.tabs.deviceHealth',
    defaultLabel: 'Device Health',
    icon: Activity,
  },
];

// Convert date range to query params
function getDateRangeParams(range: DateRange) {
  const now = new Date();
  const end = now.toISOString();
  let start: string;

  switch (range) {
    case '7d':
      start = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString();
      break;
    case '30d':
      start = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString();
      break;
    case '90d':
      start = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000).toISOString();
      break;
    default:
      start = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString();
  }

  return { start_date: start, end_date: end };
}

export default function AnalyticsPage() {
  const { t } = useTranslation();

  // Permission check
  const { hasPermission: canView, isLoading: isCheckingPermission } = useCanPerformAction('analytics', 'read');

  const [activeTab, setActiveTab] = useState<TabId>('menu');
  const [dateRange, setDateRange] = useState<DateRange>('30d');
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Calculate query params based on date range
  const queryParams = useMemo(() => getDateRangeParams(dateRange), [dateRange]);

  // Fetch analytics data
  const {
    data: menuTrends,
    isLoading: menuLoading,
    refetch: refetchMenuTrends,
  } = useMenuAnalyticsTrends(queryParams);

  const {
    data: deviceHealthTrends,
    isLoading: deviceHealthLoading,
    refetch: refetchDeviceHealthTrends,
  } = useDeviceHealthTrends(queryParams);

  // Combined refresh handler
  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await Promise.all([
        refetchMenuTrends(),
        refetchDeviceHealthTrends(),
      ]);
    } finally {
      setIsRefreshing(false);
    }
  }, [refetchMenuTrends, refetchDeviceHealthTrends]);

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
        description={t('analytics.description', 'Real data insights: menu performance and device health metrics')}
      />

      {/* Action Bar */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <DateRangePicker value={dateRange} onChange={setDateRange} />

        <RefreshButton
          onClick={handleRefresh}
          isLoading={isRefreshing}
          label={t('common.refresh', 'Refresh')}
        />
      </div>

      {/* Tab Navigation */}
      <div className="mb-6">
        <nav className="flex space-x-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1" aria-label="Tabs">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium
                  transition-all duration-200 flex-1 justify-center
                  ${
                    isActive
                      ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-white/50 dark:hover:bg-gray-700/50'
                  }
                `}
                aria-current={isActive ? 'page' : undefined}
              >
                <Icon className="w-5 h-5" />
                <span>{t(tab.labelKey, tab.defaultLabel)}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <Suspense fallback={<TabSkeleton />}>
        {activeTab === 'menu' && (
          <MenuAnalyticsTab data={menuTrends} isLoading={menuLoading} />
        )}
        {activeTab === 'device-health' && (
          <DeviceHealthTab data={deviceHealthTrends} isLoading={deviceHealthLoading} />
        )}
      </Suspense>

      {/* Data Source Note */}
      <div className="mt-6 rounded-lg border border-gray-200 dark:border-gray-700 p-4 bg-blue-50 dark:bg-blue-900/20">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white">
              {t('analytics.dataSource', 'Real Data Analytics')}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {activeTab === 'menu'
                ? t('analytics.menuDataSource', 'Data from menu_views table - actual QR scan tracking')
                : t('analytics.deviceDataSource', 'Data from device_health_metrics table - actual device reports')}
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
    </>
  );
}
