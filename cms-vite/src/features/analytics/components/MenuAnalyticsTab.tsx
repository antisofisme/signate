/**
 * Menu Analytics Tab Component
 *
 * LAYER 1: PRESENTATION
 * Displays REAL menu analytics data from menu_views table
 *
 * Features:
 * - Total views and contact clicks
 * - Device type breakdown
 * - Daily trend chart
 * - Top performing menus
 * - Popular viewing hours
 */

import { lazy, Suspense } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Eye,
  Phone,
  Smartphone,
  Tablet,
  Monitor,
  HelpCircle,
  TrendingUp,
  UtensilsCrossed,
  Clock,
} from 'lucide-react';
import type { MenuAnalyticsTrend } from '../types';

// Lazy load chart component
const MenuTrendChart = lazy(() =>
  import('./MenuTrendChart').then((module) => ({
    default: module.MenuTrendChart,
  }))
);

interface MenuAnalyticsTabProps {
  data: MenuAnalyticsTrend | undefined;
  isLoading: boolean;
}

// Chart skeleton
function ChartSkeleton() {
  return (
    <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse" />
  );
}

// Stat card component
function StatCard({
  icon: Icon,
  label,
  value,
  subtitle,
  iconColor,
  isLoading,
}: {
  icon: React.ElementType;
  label: string;
  value: number | string;
  subtitle?: string;
  iconColor: string;
  isLoading: boolean;
}) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div className="flex items-center gap-4">
        <div className={`p-3 rounded-lg ${iconColor}`}>
          <Icon className="w-6 h-6" />
        </div>
        <div>
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{label}</p>
          {isLoading ? (
            <div className="h-8 w-24 bg-gray-200 dark:bg-gray-700 animate-pulse rounded mt-1" />
          ) : (
            <>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {typeof value === 'number' ? value.toLocaleString() : value}
              </p>
              {subtitle && (
                <p className="text-xs text-gray-500 dark:text-gray-400">{subtitle}</p>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// Device breakdown item
function DeviceBreakdownItem({
  icon: Icon,
  label,
  value,
  percentage,
  color,
  isLoading,
}: {
  icon: React.ElementType;
  label: string;
  value: number;
  percentage: number;
  color: string;
  isLoading: boolean;
}) {
  return (
    <div className="flex items-center gap-4">
      <div className={`p-2 rounded-lg ${color.replace('bg-', 'bg-').replace('-500', '-100')} dark:bg-opacity-20`}>
        <Icon className={`w-5 h-5 ${color.replace('bg-', 'text-')}`} />
      </div>
      <div className="flex-1">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-medium text-gray-900 dark:text-white">{label}</span>
          <span className="text-sm font-semibold text-gray-900 dark:text-white">
            {isLoading ? '-' : `${value.toLocaleString()} (${percentage}%)`}
          </span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-500 ${color}`}
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
    </div>
  );
}

// Popular hour item
function PopularHourItem({
  hour,
  views,
  percentage,
  maxPercentage,
}: {
  hour: number;
  views: number;
  percentage: number;
  maxPercentage: number;
}) {
  const barHeight = maxPercentage > 0 ? (percentage / maxPercentage) * 100 : 0;
  const hourLabel = `${hour.toString().padStart(2, '0')}:00`;

  return (
    <div className="flex flex-col items-center">
      <div className="h-20 w-6 bg-gray-100 dark:bg-gray-700 rounded-t relative flex items-end">
        <div
          className="w-full bg-blue-500 dark:bg-blue-600 rounded-t transition-all duration-500"
          style={{ height: `${barHeight}%` }}
          title={`${views} views (${percentage.toFixed(1)}%)`}
        />
      </div>
      <span className="text-xs text-gray-500 dark:text-gray-400 mt-1">{hourLabel}</span>
    </div>
  );
}

// Menu type badge
function MenuTypeBadge({ type }: { type: string }) {
  const colors: Record<string, string> = {
    food_beverage: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300',
    room_service: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
    spa_wellness: 'bg-pink-100 dark:bg-pink-900/30 text-pink-700 dark:text-pink-300',
    amenities: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
  };

  return (
    <span className={`text-xs px-2 py-0.5 rounded-full ${colors[type] || 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}`}>
      {type.replace('_', ' ')}
    </span>
  );
}

export function MenuAnalyticsTab({ data, isLoading }: MenuAnalyticsTabProps) {
  const { t } = useTranslation();

  const totalViews = data?.total_views || 0;
  const totalContactClicks = data?.total_contact_clicks || 0;
  const viewsByDevice = data?.views_by_device || { mobile: 0, tablet: 0, desktop: 0, unknown: 0 };

  const getPercentage = (value: number) => {
    if (!totalViews) return 0;
    return Math.round((value / totalViews) * 100);
  };

  // Find max percentage for popular hours scaling
  const maxHourPercentage = Math.max(...(data?.popular_hours?.map((h) => h.percentage) || [0]));

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <StatCard
          icon={Eye}
          label={t('analytics.menuAnalytics.totalViews', 'Total Menu Views')}
          value={totalViews}
          subtitle={data ? `${new Date(data.period_start).toLocaleDateString()} - ${new Date(data.period_end).toLocaleDateString()}` : undefined}
          iconColor="bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400"
          isLoading={isLoading}
        />
        <StatCard
          icon={Phone}
          label={t('analytics.menuAnalytics.contactClicks', 'Contact Button Clicks')}
          value={totalContactClicks}
          subtitle={totalViews > 0 ? `${((totalContactClicks / totalViews) * 100).toFixed(1)}% conversion` : undefined}
          iconColor="bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400"
          isLoading={isLoading}
        />
      </div>

      {/* Device Breakdown & Daily Trend */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Device Breakdown */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
            <Smartphone className="w-5 h-5" />
            {t('analytics.menuAnalytics.deviceBreakdown', 'Views by Device')}
          </h3>
          <div className="space-y-4">
            <DeviceBreakdownItem
              icon={Smartphone}
              label={t('analytics.menuAnalytics.mobile', 'Mobile')}
              value={viewsByDevice.mobile}
              percentage={getPercentage(viewsByDevice.mobile)}
              color="bg-blue-500"
              isLoading={isLoading}
            />
            <DeviceBreakdownItem
              icon={Tablet}
              label={t('analytics.menuAnalytics.tablet', 'Tablet')}
              value={viewsByDevice.tablet}
              percentage={getPercentage(viewsByDevice.tablet)}
              color="bg-purple-500"
              isLoading={isLoading}
            />
            <DeviceBreakdownItem
              icon={Monitor}
              label={t('analytics.menuAnalytics.desktop', 'Desktop')}
              value={viewsByDevice.desktop}
              percentage={getPercentage(viewsByDevice.desktop)}
              color="bg-green-500"
              isLoading={isLoading}
            />
            <DeviceBreakdownItem
              icon={HelpCircle}
              label={t('analytics.menuAnalytics.unknown', 'Unknown')}
              value={viewsByDevice.unknown}
              percentage={getPercentage(viewsByDevice.unknown)}
              color="bg-gray-500"
              isLoading={isLoading}
            />
          </div>
        </div>

        {/* Daily Trend Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            {t('analytics.menuAnalytics.dailyTrend', 'Daily View Trend')}
          </h3>
          <Suspense fallback={<ChartSkeleton />}>
            <MenuTrendChart data={data?.daily_trend || []} isLoading={isLoading} />
          </Suspense>
        </div>
      </div>

      {/* Top Menus & Popular Hours */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Menus */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
            <UtensilsCrossed className="w-5 h-5" />
            {t('analytics.menuAnalytics.topMenus', 'Top Performing Menus')}
          </h3>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="h-16 bg-gray-200 dark:bg-gray-700 animate-pulse rounded" />
              ))}
            </div>
          ) : data?.top_menus && data.top_menus.length > 0 ? (
            <div className="space-y-3">
              {data.top_menus.slice(0, 5).map((menu, index) => (
                <div
                  key={menu.menu_id}
                  className="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-gray-400 dark:text-gray-500 w-5">
                        #{index + 1}
                      </span>
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {menu.menu_name}
                        </p>
                        <MenuTypeBadge type={menu.menu_type} />
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-semibold text-gray-900 dark:text-white">
                        {menu.total_views.toLocaleString()} views
                      </p>
                      <p className="text-xs text-green-600 dark:text-green-400">
                        {menu.contact_clicks} clicks
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <UtensilsCrossed className="w-12 h-12 text-gray-400 dark:text-gray-500 mb-3" />
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t('analytics.menuAnalytics.noMenuData', 'No menu data available for this period')}
              </p>
            </div>
          )}
        </div>

        {/* Popular Hours */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
            <Clock className="w-5 h-5" />
            {t('analytics.menuAnalytics.popularHours', 'Popular Viewing Hours')}
          </h3>
          {isLoading ? (
            <ChartSkeleton />
          ) : data?.popular_hours && data.popular_hours.length > 0 ? (
            <div className="flex justify-between items-end gap-1 overflow-x-auto pb-2">
              {data.popular_hours.map((hour) => (
                <PopularHourItem
                  key={hour.hour}
                  hour={hour.hour}
                  views={hour.views}
                  percentage={hour.percentage}
                  maxPercentage={maxHourPercentage}
                />
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Clock className="w-12 h-12 text-gray-400 dark:text-gray-500 mb-3" />
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t('analytics.menuAnalytics.noHourData', 'No hourly data available')}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default MenuAnalyticsTab;
