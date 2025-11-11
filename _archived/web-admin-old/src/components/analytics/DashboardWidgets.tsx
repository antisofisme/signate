// ============================================================================
// Dashboard Widgets Component
// ============================================================================

import React from 'react'
import type {
  DashboardData,
  AnalyticsOverview,
  DeviceStatusData,
  ContentPerformance,
  SystemHealth,
} from '../../types/analytics'
import { Activity, Monitor, AlertCircle, TrendingUp, Server, Users } from 'lucide-react'

// ============================================================================
// Type Definitions
// ============================================================================

interface DashboardWidgetsProps {
  /** Dashboard data */
  data: DashboardData | null
  /** Loading state */
  loading: boolean
}

interface MetricCardProps {
  /** Card title */
  title: string
  /** Main metric value */
  value: string | number
  /** Subtitle or description */
  subtitle?: string
  /** Icon component */
  icon: React.ReactNode
  /** Trend percentage (positive or negative) */
  trend?: number
  /** Card color theme */
  color?: 'blue' | 'green' | 'red' | 'yellow' | 'purple'
  /** Loading state */
  loading?: boolean
}

// ============================================================================
// Metric Card Component
// ============================================================================

function MetricCard({
  title,
  value,
  subtitle,
  icon,
  trend,
  color = 'blue',
  loading = false,
}: MetricCardProps) {
  const colorClasses = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    red: 'bg-red-500',
    yellow: 'bg-yellow-500',
    purple: 'bg-purple-500',
  }

  const bgClasses = {
    blue: 'bg-blue-50 dark:bg-blue-900/20',
    green: 'bg-green-50 dark:bg-green-900/20',
    red: 'bg-red-50 dark:bg-red-900/20',
    yellow: 'bg-yellow-50 dark:bg-yellow-900/20',
    purple: 'bg-purple-50 dark:bg-purple-900/20',
  }

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 animate-pulse">
        <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-4"></div>
        <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
            {title}
          </p>
          <div className="flex items-baseline gap-2">
            <h3 className="text-3xl font-bold text-gray-900 dark:text-white">
              {typeof value === 'number' ? value.toLocaleString() : value}
            </h3>
            {trend !== undefined && (
              <span
                className={`text-sm font-medium ${
                  trend >= 0 ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {trend >= 0 ? '+' : ''}
                {trend.toFixed(1)}%
              </span>
            )}
          </div>
          {subtitle && (
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {subtitle}
            </p>
          )}
        </div>
        <div
          className={`${colorClasses[color]} ${bgClasses[color]} p-3 rounded-lg`}
        >
          {icon}
        </div>
      </div>
    </div>
  )
}

// ============================================================================
// Active Devices Card
// ============================================================================

interface ActiveDevicesCardProps {
  devices: DeviceStatusData
  loading: boolean
}

function ActiveDevicesCard({ devices, loading }: ActiveDevicesCardProps) {
  if (loading) {
    return (
      <MetricCard
        title="Active Devices"
        value="-"
        icon={<Monitor className="w-6 h-6 text-white" />}
        color="blue"
        loading
      />
    )
  }

  const total = devices.online + devices.offline + devices.error + devices.pending
  const onlinePercentage = total > 0 ? (devices.online / total) * 100 : 0

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
            Active Devices
          </p>
          <h3 className="text-3xl font-bold text-gray-900 dark:text-white">
            {devices.online} / {total}
          </h3>
        </div>
        <div className="bg-blue-500 bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
          <Monitor className="w-6 h-6 text-white" />
        </div>
      </div>

      {/* Device Status Breakdown */}
      <div className="space-y-2 mt-4">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span className="text-gray-600 dark:text-gray-400">Online</span>
          </div>
          <span className="font-medium text-gray-900 dark:text-white">
            {devices.online}
          </span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-gray-400"></div>
            <span className="text-gray-600 dark:text-gray-400">Offline</span>
          </div>
          <span className="font-medium text-gray-900 dark:text-white">
            {devices.offline}
          </span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <span className="text-gray-600 dark:text-gray-400">Error</span>
          </div>
          <span className="font-medium text-gray-900 dark:text-white">
            {devices.error}
          </span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
            <span className="text-gray-600 dark:text-gray-400">Pending</span>
          </div>
          <span className="font-medium text-gray-900 dark:text-white">
            {devices.pending}
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mt-4">
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div
            className="bg-green-500 h-2 rounded-full transition-all duration-300"
            style={{ width: `${onlinePercentage}%` }}
          ></div>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          {onlinePercentage.toFixed(1)}% online
        </p>
      </div>
    </div>
  )
}

// ============================================================================
// Content Performance Card
// ============================================================================

interface ContentPerformanceCardProps {
  content: ContentPerformance[]
  loading: boolean
}

function ContentPerformanceCard({
  content,
  loading,
}: ContentPerformanceCardProps) {
  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Top Content
          </h3>
          <TrendingUp className="w-5 h-5 text-gray-400" />
        </div>
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Top Content
        </h3>
        <TrendingUp className="w-5 h-5 text-gray-400" />
      </div>

      <div className="space-y-3">
        {content.slice(0, 10).map((item, index) => (
          <div
            key={item.id}
            className="flex items-center gap-3 p-2 rounded hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
          >
            <div className="flex-shrink-0 w-8 text-center">
              <span className="text-sm font-bold text-gray-400">
                #{index + 1}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                {item.title}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {item.type} • {item.views.toLocaleString()} views
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm font-semibold text-gray-900 dark:text-white">
                {item.views.toLocaleString()}
              </p>
            </div>
          </div>
        ))}
      </div>

      {content.length === 0 && (
        <div className="text-center py-8">
          <TrendingUp className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
          <p className="text-sm text-gray-500 dark:text-gray-400">
            No content data available
          </p>
        </div>
      )}
    </div>
  )
}

// ============================================================================
// System Health Card
// ============================================================================

interface SystemHealthCardProps {
  health: SystemHealth
  loading: boolean
}

function SystemHealthCard({ health, loading }: SystemHealthCardProps) {
  if (loading) {
    return (
      <MetricCard
        title="System Health"
        value="-"
        icon={<Server className="w-6 h-6 text-white" />}
        color="green"
        loading
      />
    )
  }

  const getHealthStatus = () => {
    const avgUsage =
      (health.cpu_usage + health.memory_usage + health.disk_usage) / 3
    if (avgUsage < 50) return { status: 'Healthy', color: 'green' }
    if (avgUsage < 80) return { status: 'Warning', color: 'yellow' }
    return { status: 'Critical', color: 'red' }
  }

  const { status, color } = getHealthStatus()

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
            System Health
          </p>
          <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
            {status}
          </h3>
        </div>
        <div
          className={`bg-${color}-500 bg-${color}-50 dark:bg-${color}-900/20 p-3 rounded-lg`}
        >
          <Server className="w-6 h-6 text-white" />
        </div>
      </div>

      <div className="space-y-3 mt-4">
        {/* CPU Usage */}
        <div>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-gray-600 dark:text-gray-400">CPU</span>
            <span className="font-medium text-gray-900 dark:text-white">
              {health.cpu_usage.toFixed(1)}%
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className={`${
                health.cpu_usage > 80
                  ? 'bg-red-500'
                  : health.cpu_usage > 50
                  ? 'bg-yellow-500'
                  : 'bg-green-500'
              } h-2 rounded-full transition-all duration-300`}
              style={{ width: `${health.cpu_usage}%` }}
            ></div>
          </div>
        </div>

        {/* Memory Usage */}
        <div>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-gray-600 dark:text-gray-400">Memory</span>
            <span className="font-medium text-gray-900 dark:text-white">
              {health.memory_usage.toFixed(1)}%
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className={`${
                health.memory_usage > 80
                  ? 'bg-red-500'
                  : health.memory_usage > 50
                  ? 'bg-yellow-500'
                  : 'bg-green-500'
              } h-2 rounded-full transition-all duration-300`}
              style={{ width: `${health.memory_usage}%` }}
            ></div>
          </div>
        </div>

        {/* Disk Usage */}
        <div>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-gray-600 dark:text-gray-400">Disk</span>
            <span className="font-medium text-gray-900 dark:text-white">
              {health.disk_usage.toFixed(1)}%
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className={`${
                health.disk_usage > 80
                  ? 'bg-red-500'
                  : health.disk_usage > 50
                  ? 'bg-yellow-500'
                  : 'bg-green-500'
              } h-2 rounded-full transition-all duration-300`}
              style={{ width: `${health.disk_usage}%` }}
            ></div>
          </div>
        </div>

        {/* Additional Metrics */}
        <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">API Response</span>
            <span className="font-medium text-gray-900 dark:text-white">
              {health.api_response_time}ms
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

// ============================================================================
// Error Rate Card
// ============================================================================

interface ErrorRateCardProps {
  overview: AnalyticsOverview
  loading: boolean
}

function ErrorRateCard({ overview, loading }: ErrorRateCardProps) {
  if (loading) {
    return (
      <MetricCard
        title="Error Rate"
        value="-"
        icon={<AlertCircle className="w-6 h-6 text-white" />}
        color="red"
        loading
      />
    )
  }

  const errorRate = overview.error_count || 0

  return (
    <MetricCard
      title="Error Rate"
      value={errorRate}
      subtitle="Errors in period"
      icon={<AlertCircle className="w-6 h-6 text-white" />}
      color={errorRate > 100 ? 'red' : errorRate > 50 ? 'yellow' : 'green'}
    />
  )
}

// ============================================================================
// Main Dashboard Widgets Component
// ============================================================================

export function DashboardWidgets({ data, loading }: DashboardWidgetsProps) {
  return (
    <div className="space-y-6">
      {/* Overview Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Views"
          value={data?.overview.total_views || 0}
          subtitle="All time views"
          icon={<Activity className="w-6 h-6 text-white" />}
          color="blue"
          loading={loading}
        />
        <MetricCard
          title="Unique Viewers"
          value={data?.overview.unique_viewers || 0}
          subtitle="Distinct viewers"
          icon={<Users className="w-6 h-6 text-white" />}
          color="purple"
          loading={loading}
        />
        <MetricCard
          title="Avg Duration"
          value={
            data?.overview.avg_view_duration
              ? `${Math.round(data.overview.avg_view_duration)}s`
              : '0s'
          }
          subtitle="Average view time"
          icon={<Activity className="w-6 h-6 text-white" />}
          color="green"
          loading={loading}
        />
        <MetricCard
          title="Uptime"
          value={
            data?.overview.uptime_percentage
              ? `${data.overview.uptime_percentage.toFixed(1)}%`
              : '0%'
          }
          subtitle="System availability"
          icon={<Server className="w-6 h-6 text-white" />}
          color="green"
          loading={loading}
        />
      </div>

      {/* Detailed Widgets Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <ActiveDevicesCard
          devices={
            data?.devices || {
              online: 0,
              offline: 0,
              error: 0,
              pending: 0,
            }
          }
          loading={loading}
        />
        <ContentPerformanceCard
          content={data?.topContent || []}
          loading={loading}
        />
        <SystemHealthCard
          health={
            data?.systemHealth || {
              cpu_usage: 0,
              memory_usage: 0,
              disk_usage: 0,
              bandwidth: 0,
              db_connections: 0,
              api_response_time: 0,
            }
          }
          loading={loading}
        />
      </div>
    </div>
  )
}

export default DashboardWidgets
