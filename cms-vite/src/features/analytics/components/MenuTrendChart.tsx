/**
 * Menu Trend Chart Component
 *
 * LAYER 1: PRESENTATION
 * Displays daily menu view trends using Recharts
 */

import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { useTranslation } from 'react-i18next';
import type { MenuViewTrendPoint } from '../types';

interface MenuTrendChartProps {
  data: MenuViewTrendPoint[];
  isLoading: boolean;
}

export function MenuTrendChart({ data, isLoading }: MenuTrendChartProps) {
  const { t } = useTranslation();

  if (isLoading) {
    return (
      <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse" />
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-500 dark:text-gray-400">
        {t('analytics.menuAnalytics.noTrendData', 'No trend data available')}
      </div>
    );
  }

  // Format date for display
  const formattedData = data.map((item) => ({
    ...item,
    displayDate: new Date(item.date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    }),
  }));

  return (
    <ResponsiveContainer width="100%" height={256}>
      <AreaChart data={formattedData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="colorViews" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="colorClicks" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#10B981" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
        <XAxis
          dataKey="displayDate"
          tick={{ fontSize: 12 }}
          className="text-gray-500 dark:text-gray-400"
        />
        <YAxis
          tick={{ fontSize: 12 }}
          className="text-gray-500 dark:text-gray-400"
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'var(--tooltip-bg, #fff)',
            border: '1px solid var(--tooltip-border, #e5e7eb)',
            borderRadius: '8px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
          }}
          labelStyle={{ fontWeight: 600, marginBottom: 4 }}
          formatter={(value: number, name: string) => [
            value.toLocaleString(),
            name === 'views'
              ? t('analytics.menuAnalytics.views', 'Views')
              : t('analytics.menuAnalytics.clicks', 'Contact Clicks'),
          ]}
        />
        <Legend
          wrapperStyle={{ paddingTop: 10 }}
          formatter={(value) =>
            value === 'views'
              ? t('analytics.menuAnalytics.views', 'Views')
              : t('analytics.menuAnalytics.clicks', 'Contact Clicks')
          }
        />
        <Area
          type="monotone"
          dataKey="views"
          stroke="#3B82F6"
          strokeWidth={2}
          fillOpacity={1}
          fill="url(#colorViews)"
        />
        <Area
          type="monotone"
          dataKey="contact_clicks"
          stroke="#10B981"
          strokeWidth={2}
          fillOpacity={1}
          fill="url(#colorClicks)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export default MenuTrendChart;
