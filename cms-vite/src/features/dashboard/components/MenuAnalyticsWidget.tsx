/**
 * Menu Analytics Widget Component
 *
 * LAYER 1: PRESENTATION
 * Menu analytics with device type breakdown and top menus
 */

import { Smartphone, Tablet, Monitor, HelpCircle, UtensilsCrossed, Phone } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { MenuStats } from '../api/dashboard.api';

interface MenuAnalyticsWidgetProps {
  data: MenuStats | undefined;
  isLoading: boolean;
}

export default function MenuAnalyticsWidget({ data, isLoading }: MenuAnalyticsWidgetProps) {
  const { t } = useTranslation();

  const totalViews = data ?
    data.views_by_device.mobile +
    data.views_by_device.tablet +
    data.views_by_device.desktop +
    data.views_by_device.unknown
    : 0;

  const getPercentage = (value: number) => {
    if (!totalViews) return 0;
    return Math.round((value / totalViews) * 100);
  };

  const deviceStats = [
    {
      label: t('dashboard.menuAnalytics.mobile', 'Mobile'),
      value: data?.views_by_device.mobile || 0,
      percentage: getPercentage(data?.views_by_device.mobile || 0),
      icon: Smartphone,
      color: 'text-blue-600 dark:text-blue-400',
      bgColor: 'bg-blue-100 dark:bg-blue-900/30',
      barColor: 'bg-blue-500 dark:bg-blue-600',
    },
    {
      label: t('dashboard.menuAnalytics.tablet', 'Tablet'),
      value: data?.views_by_device.tablet || 0,
      percentage: getPercentage(data?.views_by_device.tablet || 0),
      icon: Tablet,
      color: 'text-purple-600 dark:text-purple-400',
      bgColor: 'bg-purple-100 dark:bg-purple-900/30',
      barColor: 'bg-purple-500 dark:bg-purple-600',
    },
    {
      label: t('dashboard.menuAnalytics.desktop', 'Desktop'),
      value: data?.views_by_device.desktop || 0,
      percentage: getPercentage(data?.views_by_device.desktop || 0),
      icon: Monitor,
      color: 'text-green-600 dark:text-green-400',
      bgColor: 'bg-green-100 dark:bg-green-900/30',
      barColor: 'bg-green-500 dark:bg-green-600',
    },
    {
      label: t('dashboard.menuAnalytics.unknown', 'Unknown'),
      value: data?.views_by_device.unknown || 0,
      percentage: getPercentage(data?.views_by_device.unknown || 0),
      icon: HelpCircle,
      color: 'text-gray-600 dark:text-gray-400',
      bgColor: 'bg-gray-100 dark:bg-gray-700',
      barColor: 'bg-gray-500 dark:bg-gray-600',
    },
  ];

  const getMenuTypeBadgeColor = (type: string) => {
    switch (type) {
      case 'food_beverage':
        return 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300';
      case 'room_service':
        return 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300';
      case 'spa_wellness':
        return 'bg-pink-100 dark:bg-pink-900/30 text-pink-700 dark:text-pink-300';
      case 'amenities':
        return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300';
      default:
        return 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300';
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
        {t('dashboard.menuAnalytics.title', 'Menu Analytics by Device')}
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Device Breakdown */}
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
            {t('dashboard.menuAnalytics.viewsByDevice', 'Views by Device Type')}
          </h3>
          {deviceStats.map((stat) => {
            const Icon = stat.icon;
            return (
              <div key={stat.label} className="flex items-center gap-4">
                <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                  <Icon className={`w-5 h-5 ${stat.color}`} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {stat.label}
                    </span>
                    <span className="text-sm font-semibold text-gray-900 dark:text-white">
                      {isLoading ? '-' : `${stat.value.toLocaleString()} (${stat.percentage}%)`}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all duration-500 ${stat.barColor}`}
                      style={{ width: `${stat.percentage}%` }}
                    />
                  </div>
                </div>
              </div>
            );
          })}

          {/* Total Summary */}
          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500 dark:text-gray-400">
                {t('dashboard.menuAnalytics.totalViews', 'Total Views')}
              </span>
              <span className="font-semibold text-gray-900 dark:text-white">
                {isLoading ? '-' : totalViews.toLocaleString()}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm mt-2">
              <span className="text-gray-500 dark:text-gray-400 flex items-center gap-1">
                <Phone className="w-4 h-4" />
                {t('dashboard.menuAnalytics.contactClicks', 'Contact Clicks')}
              </span>
              <span className="font-semibold text-green-600 dark:text-green-400">
                {isLoading ? '-' : (data?.total_contact_clicks || 0).toLocaleString()}
              </span>
            </div>
          </div>
        </div>

        {/* Top Menus */}
        <div>
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">
            {t('dashboard.menuAnalytics.topMenus', 'Top Performing Menus')}
          </h3>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
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
                      <span className="text-xs font-bold text-gray-400 dark:text-gray-500">
                        #{index + 1}
                      </span>
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {menu.menu_name}
                        </p>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${getMenuTypeBadgeColor(menu.menu_type)}`}>
                          {menu.menu_type.replace('_', ' ')}
                        </span>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-semibold text-gray-900 dark:text-white">
                        {menu.views.toLocaleString()}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
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
                {t('dashboard.menuAnalytics.noMenus', 'No menu data available')}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
