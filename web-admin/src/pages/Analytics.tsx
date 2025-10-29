// ============================================================================
// Analytics Page - Comprehensive Dashboard with Export Functionality
// ============================================================================

import React, { useState, useEffect } from 'react'
import {
  Calendar,
  Download,
  FileText,
  RefreshCw,
  TrendingUp,
  BarChart3,
  Filter,
  X,
} from 'lucide-react'
import { format, subDays, startOfDay, endOfDay } from 'date-fns'
import toast from 'react-hot-toast'

// Components
import { PageHeader } from '../components/shared/PageHeader'
import { Button } from '../components/shared/Button'
import { DashboardWidgets } from '../components/analytics/DashboardWidgets'
import {
  ViewsChart,
  TopContentChart,
  DeviceStatusChart,
  ErrorRateChart,
  HeatmapChart,
} from '../components/analytics/Charts'

// Services & Types
import analyticsAPI from '../services/api/analytics'
import type {
  DashboardData,
  DateRange,
  ExportOptions,
} from '../types/analytics'

// ============================================================================
// Type Definitions
// ============================================================================

interface DateRangeOption {
  label: string
  value: string
  getDates: () => DateRange
}

// ============================================================================
// Date Range Presets
// ============================================================================

const DATE_RANGE_OPTIONS: DateRangeOption[] = [
  {
    label: 'Last 24 Hours',
    value: '24h',
    getDates: () => ({
      start: subDays(new Date(), 1),
      end: new Date(),
    }),
  },
  {
    label: 'Last 7 Days',
    value: '7d',
    getDates: () => ({
      start: subDays(new Date(), 7),
      end: new Date(),
    }),
  },
  {
    label: 'Last 30 Days',
    value: '30d',
    getDates: () => ({
      start: subDays(new Date(), 30),
      end: new Date(),
    }),
  },
  {
    label: 'Last 90 Days',
    value: '90d',
    getDates: () => ({
      start: subDays(new Date(), 90),
      end: new Date(),
    }),
  },
]

// ============================================================================
// Main Analytics Component
// ============================================================================

export default function Analytics() {
  // State Management
  const [selectedRange, setSelectedRange] = useState<string>('30d')
  const [customDateRange, setCustomDateRange] = useState<DateRange | null>(null)
  const [dateRange, setDateRange] = useState<DateRange>(
    DATE_RANGE_OPTIONS[2].getDates()
  )
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date())
  const [exporting, setExporting] = useState(false)
  const [showFilters, setShowFilters] = useState(false)

  // ============================================================================
  // Data Loading
  // ============================================================================

  /**
   * Load dashboard data from API
   */
  const loadDashboard = async () => {
    try {
      setLoading(true)
      const data = await analyticsAPI.getDashboard(dateRange)
      setDashboardData(data)
      setLastUpdated(new Date())
    } catch (error) {
      console.error('Failed to load dashboard:', error)
      toast.error('Failed to load analytics data')
    } finally {
      setLoading(false)
    }
  }

  /**
   * Handle date range change
   */
  const handleDateRangeChange = (rangeValue: string) => {
    setSelectedRange(rangeValue)
    const option = DATE_RANGE_OPTIONS.find((opt) => opt.value === rangeValue)
    if (option) {
      const newRange = option.getDates()
      setDateRange(newRange)
      setCustomDateRange(null)
    }
  }

  /**
   * Handle custom date range
   */
  const handleCustomDateChange = (start: string, end: string) => {
    const customRange: DateRange = {
      start: startOfDay(new Date(start)),
      end: endOfDay(new Date(end)),
    }
    setDateRange(customRange)
    setCustomDateRange(customRange)
    setSelectedRange('custom')
  }

  /**
   * Manual refresh
   */
  const handleRefresh = () => {
    toast.promise(loadDashboard(), {
      loading: 'Refreshing data...',
      success: 'Data refreshed successfully',
      error: 'Failed to refresh data',
    })
  }

  // ============================================================================
  // Export Functionality
  // ============================================================================

  /**
   * Export report in specified format
   */
  const handleExport = async (format: 'pdf' | 'excel' | 'csv') => {
    setExporting(true)
    try {
      const timestamp = format(new Date(), 'yyyy-MM-dd_HHmmss')
      const filename = `analytics_report_${timestamp}`

      if (format === 'pdf') {
        await analyticsAPI.exportToPDF(dateRange, {
          orientation: 'landscape',
          filename: `${filename}.pdf`,
        })
      } else if (format === 'excel') {
        await analyticsAPI.exportToExcel(dateRange, `${filename}.xlsx`)
      } else if (format === 'csv') {
        await analyticsAPI.exportToCSV(dateRange, `${filename}.csv`)
      }

      toast.success(`Report exported as ${format.toUpperCase()}`)
    } catch (error) {
      console.error(`Export failed:`, error)
      toast.error(`Failed to export as ${format.toUpperCase()}`)
    } finally {
      setExporting(false)
    }
  }

  // ============================================================================
  // Effects
  // ============================================================================

  /**
   * Load dashboard on mount and date range change
   */
  useEffect(() => {
    loadDashboard()
  }, [dateRange])

  /**
   * Auto-refresh every 30 seconds
   */
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        loadDashboard()
      }, 30000) // 30 seconds

      return () => clearInterval(interval)
    }
  }, [autoRefresh, dateRange])

  // ============================================================================
  // Render
  // ============================================================================

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <PageHeader
        title="Analytics & Insights"
        subtitle="Monitor performance, track trends, and export reports"
        icon={<BarChart3 className="w-8 h-8" />}
      >
        <div className="flex items-center gap-3">
          {/* Auto-refresh Toggle */}
          <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 cursor-pointer">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span>Auto-refresh (30s)</span>
          </label>

          {/* Refresh Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={loading}
          >
            <RefreshCw
              className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`}
            />
            Refresh
          </Button>

          {/* Filter Toggle */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter className="w-4 h-4 mr-2" />
            Filters
          </Button>
        </div>
      </PageHeader>

      {/* Filters Bar */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4">
        <div className="flex flex-wrap items-center gap-4">
          {/* Date Range Presets */}
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-gray-400" />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Date Range:
            </span>
            <div className="flex gap-2">
              {DATE_RANGE_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  onClick={() => handleDateRangeChange(option.value)}
                  className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                    selectedRange === option.value
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* Custom Date Range */}
          <div className="flex items-center gap-2 ml-auto">
            <input
              type="date"
              value={
                customDateRange?.start
                  ? format(
                      new Date(customDateRange.start),
                      'yyyy-MM-dd'
                    )
                  : ''
              }
              onChange={(e) =>
                handleCustomDateChange(
                  e.target.value,
                  customDateRange?.end
                    ? format(new Date(customDateRange.end), 'yyyy-MM-dd')
                    : format(new Date(), 'yyyy-MM-dd')
                )
              }
              className="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
            <span className="text-gray-500">to</span>
            <input
              type="date"
              value={
                customDateRange?.end
                  ? format(new Date(customDateRange.end), 'yyyy-MM-dd')
                  : ''
              }
              onChange={(e) =>
                handleCustomDateChange(
                  customDateRange?.start
                    ? format(new Date(customDateRange.start), 'yyyy-MM-dd')
                    : format(subDays(new Date(), 30), 'yyyy-MM-dd'),
                  e.target.value
                )
              }
              className="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>

          {/* Export Buttons */}
          <div className="flex items-center gap-2 border-l border-gray-300 dark:border-gray-600 pl-4">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Export:
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExport('pdf')}
              disabled={exporting || !dashboardData}
            >
              <FileText className="w-4 h-4 mr-2" />
              PDF
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExport('excel')}
              disabled={exporting || !dashboardData}
            >
              <Download className="w-4 h-4 mr-2" />
              Excel
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExport('csv')}
              disabled={exporting || !dashboardData}
            >
              <Download className="w-4 h-4 mr-2" />
              CSV
            </Button>
          </div>
        </div>

        {/* Last Updated */}
        <div className="mt-3 text-xs text-gray-500 dark:text-gray-400">
          Last updated: {format(lastUpdated, 'MMM dd, yyyy HH:mm:ss')}
        </div>
      </div>

      {/* Dashboard Widgets */}
      <DashboardWidgets data={dashboardData} loading={loading} />

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Views Over Time */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Views Over Time
            </h3>
            <TrendingUp className="w-5 h-5 text-gray-400" />
          </div>
          <ViewsChart
            data={dashboardData?.trends || []}
            loading={loading}
          />
        </div>

        {/* Top Content */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Top Performing Content
            </h3>
            <TrendingUp className="w-5 h-5 text-gray-400" />
          </div>
          <TopContentChart
            data={dashboardData?.topContent || []}
            loading={loading}
          />
        </div>

        {/* Device Status */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Device Status Distribution
            </h3>
            <BarChart3 className="w-5 h-5 text-gray-400" />
          </div>
          <DeviceStatusChart
            data={
              dashboardData?.devices || {
                online: 0,
                offline: 0,
                error: 0,
                pending: 0,
              }
            }
            loading={loading}
          />
        </div>

        {/* Error Rate */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Error Rate Trends
            </h3>
            <BarChart3 className="w-5 h-5 text-gray-400" />
          </div>
          <ErrorRateChart
            data={dashboardData?.errors || []}
            loading={loading}
          />
        </div>
      </div>

      {/* Viewing Pattern Heatmap */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Viewing Patterns by Hour
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Understand when your content is most viewed
            </p>
          </div>
          <BarChart3 className="w-5 h-5 text-gray-400" />
        </div>
        <HeatmapChart
          data={dashboardData?.heatmap || []}
          loading={loading}
        />
      </div>

      {/* Export Status Toast */}
      {exporting && (
        <div className="fixed bottom-4 right-4 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 flex items-center gap-3">
          <RefreshCw className="w-5 h-5 animate-spin text-blue-500" />
          <span className="text-sm text-gray-700 dark:text-gray-300">
            Generating report...
          </span>
        </div>
      )}
    </div>
  )
}
