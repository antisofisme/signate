/**
 * Device Health Chart Component
 *
 * LAYER 1: PRESENTATION
 * Displays device health trends (CPU, Memory, Disk) using Recharts
 */

import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { useTranslation } from 'react-i18next';
import type { DeviceHealthTrendPoint } from '../types';

interface DeviceHealthChartProps {
  data: DeviceHealthTrendPoint[];
  isLoading: boolean;
}

export function DeviceHealthChart({ data, isLoading }: DeviceHealthChartProps) {
  const { t } = useTranslation();

  if (isLoading) {
    return (
      <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse" />
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-500 dark:text-gray-400">
        {t('analytics.deviceHealth.noTrendData', 'No trend data available')}
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
      <LineChart data={formattedData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
        <XAxis
          dataKey="displayDate"
          tick={{ fontSize: 12 }}
          className="text-gray-500 dark:text-gray-400"
        />
        <YAxis
          tick={{ fontSize: 12 }}
          domain={[0, 100]}
          className="text-gray-500 dark:text-gray-400"
          tickFormatter={(value) => `${value}%`}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'var(--tooltip-bg, #fff)',
            border: '1px solid var(--tooltip-border, #e5e7eb)',
            borderRadius: '8px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
          }}
          labelStyle={{ fontWeight: 600, marginBottom: 4 }}
          formatter={(value: number, name: string) => {
            const labels: Record<string, string> = {
              avg_cpu_usage: t('analytics.deviceHealth.cpu', 'CPU Usage'),
              avg_memory_usage: t('analytics.deviceHealth.memory', 'Memory Usage'),
              avg_disk_usage: t('analytics.deviceHealth.disk', 'Disk Usage'),
            };
            return [`${value.toFixed(1)}%`, labels[name] || name];
          }}
        />
        <Legend
          wrapperStyle={{ paddingTop: 10 }}
          formatter={(value) => {
            const labels: Record<string, string> = {
              avg_cpu_usage: t('analytics.deviceHealth.cpu', 'CPU'),
              avg_memory_usage: t('analytics.deviceHealth.memory', 'Memory'),
              avg_disk_usage: t('analytics.deviceHealth.disk', 'Disk'),
            };
            return labels[value] || value;
          }}
        />
        <Line
          type="monotone"
          dataKey="avg_cpu_usage"
          stroke="#3B82F6"
          strokeWidth={2}
          dot={{ r: 3 }}
          activeDot={{ r: 5 }}
        />
        <Line
          type="monotone"
          dataKey="avg_memory_usage"
          stroke="#8B5CF6"
          strokeWidth={2}
          dot={{ r: 3 }}
          activeDot={{ r: 5 }}
        />
        <Line
          type="monotone"
          dataKey="avg_disk_usage"
          stroke="#10B981"
          strokeWidth={2}
          dot={{ r: 3 }}
          activeDot={{ r: 5 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

export default DeviceHealthChart;
