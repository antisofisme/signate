// ============================================================================
// Analytics API Service
// ============================================================================

import { apiClient } from './client'
import type {
  DashboardData,
  DateRange,
  AnalyticsQueryParams,
  ReportGenerateRequest,
  Report,
  ExportOptions,
} from '../../types/analytics'

/**
 * Analytics API Service
 *
 * Provides methods for:
 * - Fetching dashboard analytics data
 * - Generating and exporting reports
 * - Real-time analytics updates
 */

const BASE_PATH = '/analytics'

/**
 * Get comprehensive dashboard data
 */
export async function getDashboard(
  dateRange: DateRange,
  params?: AnalyticsQueryParams
): Promise<DashboardData> {
  const response = await apiClient.get<DashboardData>(`${BASE_PATH}/dashboard`, {
    params: {
      start_date: typeof dateRange.start === 'string'
        ? dateRange.start
        : dateRange.start.toISOString(),
      end_date: typeof dateRange.end === 'string'
        ? dateRange.end
        : dateRange.end.toISOString(),
      ...params,
    },
  })
  return response.data
}

/**
 * Get real-time overview metrics
 */
export async function getOverview(dateRange?: DateRange) {
  const response = await apiClient.get(`${BASE_PATH}/overview`, {
    params: dateRange ? {
      start_date: typeof dateRange.start === 'string'
        ? dateRange.start
        : dateRange.start.toISOString(),
      end_date: typeof dateRange.end === 'string'
        ? dateRange.end
        : dateRange.end.toISOString(),
    } : undefined,
  })
  return response.data
}

/**
 * Get top performing content
 */
export async function getTopContent(params?: {
  limit?: number
  dateRange?: DateRange
}) {
  const response = await apiClient.get(`${BASE_PATH}/content/top`, {
    params: {
      limit: params?.limit || 10,
      ...(params?.dateRange && {
        start_date: typeof params.dateRange.start === 'string'
          ? params.dateRange.start
          : params.dateRange.start.toISOString(),
        end_date: typeof params.dateRange.end === 'string'
          ? params.dateRange.end
          : params.dateRange.end.toISOString(),
      }),
    },
  })
  return response.data
}

/**
 * Get device analytics
 */
export async function getDeviceAnalytics(params?: AnalyticsQueryParams) {
  const response = await apiClient.get(`${BASE_PATH}/devices`, {
    params,
  })
  return response.data
}

/**
 * Get system health metrics
 */
export async function getSystemHealth() {
  const response = await apiClient.get(`${BASE_PATH}/system/health`)
  return response.data
}

/**
 * Get time series trends
 */
export async function getTrends(params: {
  dateRange: DateRange
  interval?: 'hour' | 'day' | 'week' | 'month'
  metric?: string
}) {
  const response = await apiClient.get(`${BASE_PATH}/trends`, {
    params: {
      start_date: typeof params.dateRange.start === 'string'
        ? params.dateRange.start
        : params.dateRange.start.toISOString(),
      end_date: typeof params.dateRange.end === 'string'
        ? params.dateRange.end
        : params.dateRange.end.toISOString(),
      interval: params.interval || 'day',
      metric: params.metric,
    },
  })
  return response.data
}

/**
 * Get error rate data
 */
export async function getErrorRate(dateRange: DateRange) {
  const response = await apiClient.get(`${BASE_PATH}/errors/rate`, {
    params: {
      start_date: typeof dateRange.start === 'string'
        ? dateRange.start
        : dateRange.start.toISOString(),
      end_date: typeof dateRange.end === 'string'
        ? dateRange.end
        : dateRange.end.toISOString(),
    },
  })
  return response.data
}

/**
 * Get viewing pattern heatmap
 */
export async function getHeatmap(dateRange: DateRange) {
  const response = await apiClient.get(`${BASE_PATH}/heatmap`, {
    params: {
      start_date: typeof dateRange.start === 'string'
        ? dateRange.start
        : dateRange.start.toISOString(),
      end_date: typeof dateRange.end === 'string'
        ? dateRange.end
        : dateRange.end.toISOString(),
    },
  })
  return response.data
}

// ============================================================================
// Report Generation & Export
// ============================================================================

/**
 * Generate a report
 */
export async function generateReport(
  request: ReportGenerateRequest
): Promise<Report> {
  const response = await apiClient.post<Report>('/reports/generate', {
    ...request,
    date_range: {
      start: typeof request.date_range.start === 'string'
        ? request.date_range.start
        : request.date_range.start.toISOString(),
      end: typeof request.date_range.end === 'string'
        ? request.date_range.end
        : request.date_range.end.toISOString(),
    },
  })
  return response.data
}

/**
 * Get report by ID
 */
export async function getReport(reportId: string): Promise<Report> {
  const response = await apiClient.get<Report>(`/reports/${reportId}`)
  return response.data
}

/**
 * List all reports
 */
export async function listReports(params?: {
  limit?: number
  offset?: number
  status?: string
}): Promise<{ reports: Report[]; total: number }> {
  const response = await apiClient.get<{ reports: Report[]; total: number }>(
    '/reports',
    { params }
  )
  return response.data
}

/**
 * Download report file
 */
export async function downloadReport(reportId: string): Promise<Blob> {
  const response = await apiClient.get(`/reports/${reportId}/download`, {
    responseType: 'blob',
  })
  return response.data
}

/**
 * Delete report
 */
export async function deleteReport(reportId: string): Promise<void> {
  await apiClient.delete(`/reports/${reportId}`)
}

/**
 * Export analytics data in specified format
 * Returns a Blob that can be downloaded
 */
export async function exportAnalytics(
  dateRange: DateRange,
  options: ExportOptions
): Promise<Blob> {
  const response = await apiClient.post(
    `${BASE_PATH}/export`,
    {
      start_date: typeof dateRange.start === 'string'
        ? dateRange.start
        : dateRange.start.toISOString(),
      end_date: typeof dateRange.end === 'string'
        ? dateRange.end
        : dateRange.end.toISOString(),
      format: options.format,
      include_charts: options.include_charts ?? true,
      orientation: options.orientation ?? 'portrait',
    },
    {
      responseType: 'blob',
    }
  )
  return response.data
}

/**
 * Helper function to trigger file download from blob
 */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * Export analytics to CSV
 */
export async function exportToCSV(
  dateRange: DateRange,
  filename?: string
): Promise<void> {
  const blob = await exportAnalytics(dateRange, {
    format: 'csv',
    filename,
  })

  const finalFilename = filename || `analytics_${Date.now()}.csv`
  downloadBlob(blob, finalFilename)
}

/**
 * Export analytics to Excel
 */
export async function exportToExcel(
  dateRange: DateRange,
  filename?: string
): Promise<void> {
  const blob = await exportAnalytics(dateRange, {
    format: 'excel',
    include_charts: true,
    filename,
  })

  const finalFilename = filename || `analytics_${Date.now()}.xlsx`
  downloadBlob(blob, finalFilename)
}

/**
 * Export analytics to PDF
 */
export async function exportToPDF(
  dateRange: DateRange,
  options?: {
    orientation?: 'portrait' | 'landscape'
    filename?: string
  }
): Promise<void> {
  const blob = await exportAnalytics(dateRange, {
    format: 'pdf',
    include_charts: true,
    orientation: options?.orientation || 'portrait',
    filename: options?.filename,
  })

  const finalFilename = options?.filename || `analytics_${Date.now()}.pdf`
  downloadBlob(blob, finalFilename)
}

// ============================================================================
// Export all analytics functions
// ============================================================================

export const analyticsAPI = {
  getDashboard,
  getOverview,
  getTopContent,
  getDeviceAnalytics,
  getSystemHealth,
  getTrends,
  getErrorRate,
  getHeatmap,
  generateReport,
  getReport,
  listReports,
  downloadReport,
  deleteReport,
  exportAnalytics,
  exportToCSV,
  exportToExcel,
  exportToPDF,
  downloadBlob,
}

export default analyticsAPI
