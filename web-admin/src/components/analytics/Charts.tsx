// ============================================================================
// Analytics Charts Component
// ============================================================================

import React from 'react'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts'
import type {
  TimeSeriesDataPoint,
  ContentPerformance,
  DeviceStatusData,
  ErrorRateData,
  HeatmapData,
} from '../../types/analytics'
import { TrendingUp, TrendingDown } from 'lucide-react'

// ============================================================================
// Type Definitions
// ============================================================================

interface ViewsChartProps {
  data: TimeSeriesDataPoint[]
  loading?: boolean
}

interface TopContentChartProps {
  data: ContentPerformance[]
  loading?: boolean
}

interface DeviceStatusChartProps {
  data: DeviceStatusData
  loading?: boolean
}

interface ErrorRateChartProps {
  data: ErrorRateData[]
  loading?: boolean
}

interface HeatmapChartProps {
  data: HeatmapData[]
  loading?: boolean
}

// ============================================================================
// Chart Colors
// ============================================================================

const COLORS = {
  primary: '#3b82f6', // blue-500
  secondary: '#10b981', // green-500
  tertiary: '#f59e0b', // yellow-500
  danger: '#ef4444', // red-500
  purple: '#8b5cf6', // purple-500
  teal: '#14b8a6', // teal-500
}

const PIE_COLORS = [COLORS.primary, '#9ca3af', COLORS.danger, COLORS.tertiary]

// ============================================================================
// Custom Tooltip Component
// ============================================================================

interface CustomTooltipProps {
  active?: boolean
  payload?: Array<{
    name: string
    value: number
    color: string
    dataKey: string
  }>
  label?: string
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-3">
        <p className="text-sm font-medium text-gray-900 dark:text-white mb-2">
          {label}
        </p>
        {payload.map((entry, index) => (
          <div key={index} className="flex items-center gap-2 text-sm">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: entry.color }}
            ></div>
            <span className="text-gray-600 dark:text-gray-400">
              {entry.name}:
            </span>
            <span className="font-semibold text-gray-900 dark:text-white">
              {typeof entry.value === 'number'
                ? entry.value.toLocaleString()
                : entry.value}
            </span>
          </div>
        ))}
      </div>
    )
  }
  return null
}

// ============================================================================
// Loading Skeleton Component
// ============================================================================

function ChartLoadingSkeleton() {
  return (
    <div className="w-full h-[300px] flex items-center justify-center">
      <div className="animate-pulse flex flex-col items-center">
        <div className="w-16 h-16 bg-gray-200 dark:bg-gray-700 rounded-lg mb-4"></div>
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-32"></div>
      </div>
    </div>
  )
}

// ============================================================================
// Empty State Component
// ============================================================================

function ChartEmptyState({ message }: { message: string }) {
  return (
    <div className="w-full h-[300px] flex items-center justify-center">
      <div className="text-center">
        <TrendingDown className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
        <p className="text-sm text-gray-500 dark:text-gray-400">{message}</p>
      </div>
    </div>
  )
}

// ============================================================================
// Views Over Time Chart (Line Chart)
// ============================================================================

export function ViewsChart({ data, loading = false }: ViewsChartProps) {
  if (loading) {
    return <ChartLoadingSkeleton />
  }

  if (!data || data.length === 0) {
    return <ChartEmptyState message="No view data available for this period" />
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="colorViews" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={COLORS.primary} stopOpacity={0.8} />
            <stop offset="95%" stopColor={COLORS.primary} stopOpacity={0.1} />
          </linearGradient>
          <linearGradient id="colorViewers" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={COLORS.secondary} stopOpacity={0.8} />
            <stop offset="95%" stopColor={COLORS.secondary} stopOpacity={0.1} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
        <XAxis
          dataKey="date"
          className="text-xs text-gray-600 dark:text-gray-400"
          tick={{ fill: 'currentColor' }}
        />
        <YAxis
          className="text-xs text-gray-600 dark:text-gray-400"
          tick={{ fill: 'currentColor' }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          wrapperStyle={{
            paddingTop: '20px',
            fontSize: '14px',
          }}
        />
        <Area
          type="monotone"
          dataKey="views"
          stroke={COLORS.primary}
          fillOpacity={1}
          fill="url(#colorViews)"
          strokeWidth={2}
          name="Total Views"
        />
        <Area
          type="monotone"
          dataKey="unique_viewers"
          stroke={COLORS.secondary}
          fillOpacity={1}
          fill="url(#colorViewers)"
          strokeWidth={2}
          name="Unique Viewers"
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

// ============================================================================
// Top Content Chart (Bar Chart)
// ============================================================================

export function TopContentChart({ data, loading = false }: TopContentChartProps) {
  if (loading) {
    return <ChartLoadingSkeleton />
  }

  if (!data || data.length === 0) {
    return <ChartEmptyState message="No content data available" />
  }

  // Prepare data for bar chart (top 10)
  const chartData = data.slice(0, 10).map((item) => ({
    name: item.title.length > 20 ? item.title.substring(0, 20) + '...' : item.title,
    fullName: item.title,
    views: item.views,
    viewers: item.unique_viewers,
  }))

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 50 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
        <XAxis
          dataKey="name"
          angle={-45}
          textAnchor="end"
          height={100}
          className="text-xs text-gray-600 dark:text-gray-400"
          tick={{ fill: 'currentColor' }}
        />
        <YAxis
          className="text-xs text-gray-600 dark:text-gray-400"
          tick={{ fill: 'currentColor' }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          wrapperStyle={{
            paddingTop: '10px',
            fontSize: '14px',
          }}
        />
        <Bar dataKey="views" fill={COLORS.primary} radius={[8, 8, 0, 0]} name="Views" />
        <Bar dataKey="viewers" fill={COLORS.secondary} radius={[8, 8, 0, 0]} name="Viewers" />
      </BarChart>
    </ResponsiveContainer>
  )
}

// ============================================================================
// Device Status Chart (Pie Chart)
// ============================================================================

export function DeviceStatusChart({ data, loading = false }: DeviceStatusChartProps) {
  if (loading) {
    return <ChartLoadingSkeleton />
  }

  if (!data) {
    return <ChartEmptyState message="No device data available" />
  }

  const chartData = [
    { name: 'Online', value: data.online, color: COLORS.secondary },
    { name: 'Offline', value: data.offline, color: '#9ca3af' },
    { name: 'Error', value: data.error, color: COLORS.danger },
    { name: 'Pending', value: data.pending, color: COLORS.tertiary },
  ].filter((item) => item.value > 0)

  if (chartData.length === 0) {
    return <ChartEmptyState message="No devices registered" />
  }

  const total = chartData.reduce((sum, item) => sum + item.value, 0)

  return (
    <div className="relative">
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) =>
              `${name}: ${(percent * 100).toFixed(0)}%`
            }
            outerRadius={100}
            fill="#8884d8"
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend
            verticalAlign="bottom"
            height={36}
            wrapperStyle={{
              fontSize: '14px',
            }}
          />
        </PieChart>
      </ResponsiveContainer>

      {/* Total in Center */}
      <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center pointer-events-none">
        <p className="text-3xl font-bold text-gray-900 dark:text-white">{total}</p>
        <p className="text-sm text-gray-500 dark:text-gray-400">Devices</p>
      </div>
    </div>
  )
}

// ============================================================================
// Error Rate Chart (Line Chart)
// ============================================================================

export function ErrorRateChart({ data, loading = false }: ErrorRateChartProps) {
  if (loading) {
    return <ChartLoadingSkeleton />
  }

  if (!data || data.length === 0) {
    return <ChartEmptyState message="No error data available" />
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
        <XAxis
          dataKey="hour"
          className="text-xs text-gray-600 dark:text-gray-400"
          tick={{ fill: 'currentColor' }}
        />
        <YAxis
          className="text-xs text-gray-600 dark:text-gray-400"
          tick={{ fill: 'currentColor' }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          wrapperStyle={{
            paddingTop: '20px',
            fontSize: '14px',
          }}
        />
        <Line
          type="monotone"
          dataKey="errors"
          stroke={COLORS.danger}
          strokeWidth={2}
          name="Errors"
          dot={{ r: 4 }}
          activeDot={{ r: 6 }}
        />
        <Line
          type="monotone"
          dataKey="requests"
          stroke={COLORS.primary}
          strokeWidth={2}
          name="Requests"
          dot={{ r: 4 }}
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

// ============================================================================
// Viewing Pattern Heatmap (Simplified Bar Chart)
// ============================================================================

export function HeatmapChart({ data, loading = false }: HeatmapChartProps) {
  if (loading) {
    return <ChartLoadingSkeleton />
  }

  if (!data || data.length === 0) {
    return <ChartEmptyState message="No viewing pattern data available" />
  }

  // Group by hour and sum values
  const hourlyData = Array.from({ length: 24 }, (_, hour) => {
    const hourData = data.filter((d) => d.hour === hour)
    const total = hourData.reduce((sum, d) => sum + d.value, 0)
    return {
      hour: `${hour.toString().padStart(2, '0')}:00`,
      views: total,
    }
  })

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={hourlyData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
        <XAxis
          dataKey="hour"
          className="text-xs text-gray-600 dark:text-gray-400"
          tick={{ fill: 'currentColor' }}
        />
        <YAxis
          className="text-xs text-gray-600 dark:text-gray-400"
          tick={{ fill: 'currentColor' }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          wrapperStyle={{
            paddingTop: '20px',
            fontSize: '14px',
          }}
        />
        <Bar
          dataKey="views"
          fill={COLORS.purple}
          radius={[8, 8, 0, 0]}
          name="Views by Hour"
        />
      </BarChart>
    </ResponsiveContainer>
  )
}

// ============================================================================
// Trend Indicator Component
// ============================================================================

interface TrendIndicatorProps {
  value: number
  label: string
}

export function TrendIndicator({ value, label }: TrendIndicatorProps) {
  const isPositive = value >= 0

  return (
    <div className="flex items-center gap-2">
      {isPositive ? (
        <TrendingUp className="w-4 h-4 text-green-500" />
      ) : (
        <TrendingDown className="w-4 h-4 text-red-500" />
      )}
      <span
        className={`text-sm font-medium ${
          isPositive ? 'text-green-600' : 'text-red-600'
        }`}
      >
        {isPositive ? '+' : ''}
        {value.toFixed(1)}%
      </span>
      <span className="text-sm text-gray-500 dark:text-gray-400">{label}</span>
    </div>
  )
}

// ============================================================================
// Export all chart components
// ============================================================================

export default {
  ViewsChart,
  TopContentChart,
  DeviceStatusChart,
  ErrorRateChart,
  HeatmapChart,
  TrendIndicator,
}
