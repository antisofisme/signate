/**
 * Analytics API Client
 * API functions for analytics and reporting
 */

import { apiClient } from '@/lib/api/client'
import type {
  AnalyticsDashboard,
  PlaybackStats,
  ContentPerformance,
  DeviceEngagement,
  TimelineDataPoint,
  AnalyticsQueryParams,
  TimelineQueryParams,
  PlaybackLogRequest,
  PlaybackEndRequest,
  PlaybackLogResponse,
  // New types for real analytics
  MenuAnalyticsTrend,
  DeviceHealthTrend,
} from '../types'

const BASE_URL = '/api/v1/analytics'

export const analyticsApi = {
  /**
   * Get complete analytics dashboard
   */
  getDashboard: async (params?: AnalyticsQueryParams): Promise<AnalyticsDashboard> => {
    const response = await apiClient.get<AnalyticsDashboard>(`${BASE_URL}/dashboard`, {
      params,
    })
    return response.data
  },

  /**
   * Get overall playback statistics
   */
  getStats: async (params?: AnalyticsQueryParams): Promise<PlaybackStats> => {
    const response = await apiClient.get<PlaybackStats>(`${BASE_URL}/stats`, {
      params,
    })
    return response.data
  },

  /**
   * Get content performance analytics
   */
  getContentPerformance: async (
    params?: AnalyticsQueryParams
  ): Promise<ContentPerformance[]> => {
    const response = await apiClient.get<ContentPerformance[]>(
      `${BASE_URL}/content-performance`,
      { params }
    )
    return response.data
  },

  /**
   * Get device engagement analytics
   */
  getDeviceEngagement: async (
    params?: AnalyticsQueryParams
  ): Promise<DeviceEngagement[]> => {
    const response = await apiClient.get<DeviceEngagement[]>(
      `${BASE_URL}/device-engagement`,
      { params }
    )
    return response.data
  },

  /**
   * Get playback timeline data
   */
  getTimeline: async (params?: TimelineQueryParams): Promise<TimelineDataPoint[]> => {
    const response = await apiClient.get<TimelineDataPoint[]>(`${BASE_URL}/timeline`, {
      params,
    })
    return response.data
  },

  /**
   * Log playback start (called by player)
   */
  logPlaybackStart: async (
    contentId: number,
    data: PlaybackLogRequest
  ): Promise<PlaybackLogResponse> => {
    const response = await apiClient.post<PlaybackLogResponse>(
      `${BASE_URL}/playback/start`,
      {
        content_id: contentId,
        ...data,
      }
    )
    return response.data
  },

  /**
   * Update playback end (called by player)
   */
  updatePlaybackEnd: async (
    logId: number,
    data: PlaybackEndRequest
  ): Promise<PlaybackLogResponse> => {
    const response = await apiClient.put<PlaybackLogResponse>(
      `${BASE_URL}/playback/${logId}/end`,
      data
    )
    return response.data
  },

  // ============================================================================
  // REAL ANALYTICS ENDPOINTS (Menu & Device Health)
  // ============================================================================

  /**
   * Get menu analytics trends (REAL data from menu_views table)
   */
  getMenuTrends: async (params?: AnalyticsQueryParams): Promise<MenuAnalyticsTrend> => {
    const response = await apiClient.get<MenuAnalyticsTrend>(`${BASE_URL}/menu-trends`, {
      params,
    })
    return response.data
  },

  /**
   * Get device health trends (REAL data from device_health_metrics table)
   */
  getDeviceHealthTrends: async (params?: AnalyticsQueryParams): Promise<DeviceHealthTrend> => {
    const response = await apiClient.get<DeviceHealthTrend>(`${BASE_URL}/device-health-trends`, {
      params,
    })
    return response.data
  },
}
