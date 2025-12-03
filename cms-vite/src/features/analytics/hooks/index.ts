/**
 * Analytics Hooks
 * TanStack Query hooks for analytics data fetching
 */

import { useQuery, type UseQueryOptions } from '@tanstack/react-query'
import { analyticsApi } from '../api'
import type {
  AnalyticsDashboard,
  PlaybackStats,
  ContentPerformance,
  DeviceEngagement,
  TimelineDataPoint,
  AnalyticsQueryParams,
  TimelineQueryParams,
  // New types for real analytics
  MenuAnalyticsTrend,
  DeviceHealthTrend,
} from '../types'

const ANALYTICS_KEYS = {
  all: ['analytics'] as const,
  dashboard: (params?: AnalyticsQueryParams) =>
    [...ANALYTICS_KEYS.all, 'dashboard', params] as const,
  stats: (params?: AnalyticsQueryParams) =>
    [...ANALYTICS_KEYS.all, 'stats', params] as const,
  contentPerformance: (params?: AnalyticsQueryParams) =>
    [...ANALYTICS_KEYS.all, 'content-performance', params] as const,
  deviceEngagement: (params?: AnalyticsQueryParams) =>
    [...ANALYTICS_KEYS.all, 'device-engagement', params] as const,
  timeline: (params?: TimelineQueryParams) =>
    [...ANALYTICS_KEYS.all, 'timeline', params] as const,
  // New keys for real analytics
  menuTrends: (params?: AnalyticsQueryParams) =>
    [...ANALYTICS_KEYS.all, 'menu-trends', params] as const,
  deviceHealthTrends: (params?: AnalyticsQueryParams) =>
    [...ANALYTICS_KEYS.all, 'device-health-trends', params] as const,
}

/**
 * Hook to fetch complete analytics dashboard
 *
 * NOTE: Auto-polling removed for performance optimization.
 * Use refetch() from returned query for manual refresh.
 */
export function useAnalyticsDashboard(
  params?: AnalyticsQueryParams,
  options?: Omit<UseQueryOptions<AnalyticsDashboard>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: ANALYTICS_KEYS.dashboard(params),
    queryFn: () => analyticsApi.getDashboard(params),
    staleTime: 60000, // 1 minute - analytics data is relatively stable
    ...options,
  })
}

/**
 * Hook to fetch playback statistics
 */
export function useAnalyticsStats(
  params?: AnalyticsQueryParams,
  options?: Omit<UseQueryOptions<PlaybackStats>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: ANALYTICS_KEYS.stats(params),
    queryFn: () => analyticsApi.getStats(params),
    staleTime: 60000, // 1 minute
    ...options,
  })
}

/**
 * Hook to fetch content performance data
 */
export function useContentPerformance(
  params?: AnalyticsQueryParams,
  options?: Omit<UseQueryOptions<ContentPerformance[]>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: ANALYTICS_KEYS.contentPerformance(params),
    queryFn: () => analyticsApi.getContentPerformance(params),
    staleTime: 120000, // 2 minutes - content performance is stable
    ...options,
  })
}

/**
 * Hook to fetch device engagement data
 */
export function useDeviceEngagement(
  params?: AnalyticsQueryParams,
  options?: Omit<UseQueryOptions<DeviceEngagement[]>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: ANALYTICS_KEYS.deviceEngagement(params),
    queryFn: () => analyticsApi.getDeviceEngagement(params),
    staleTime: 120000, // 2 minutes
    ...options,
  })
}

/**
 * Hook to fetch playback timeline data
 */
export function usePlaybackTimeline(
  params?: TimelineQueryParams,
  options?: Omit<UseQueryOptions<TimelineDataPoint[]>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: ANALYTICS_KEYS.timeline(params),
    queryFn: () => analyticsApi.getTimeline(params),
    staleTime: 300000, // 5 minutes - historical timeline data is stable
    ...options,
  })
}

// ============================================================================
// REAL ANALYTICS HOOKS (Menu & Device Health)
// ============================================================================

/**
 * Hook to fetch menu analytics trends (REAL data from menu_views table)
 */
export function useMenuAnalyticsTrends(
  params?: AnalyticsQueryParams,
  options?: Omit<UseQueryOptions<MenuAnalyticsTrend>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: ANALYTICS_KEYS.menuTrends(params),
    queryFn: () => analyticsApi.getMenuTrends(params),
    staleTime: 60000, // 1 minute
    ...options,
  })
}

/**
 * Hook to fetch device health trends (REAL data from device_health_metrics table)
 */
export function useDeviceHealthTrends(
  params?: AnalyticsQueryParams,
  options?: Omit<UseQueryOptions<DeviceHealthTrend>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: ANALYTICS_KEYS.deviceHealthTrends(params),
    queryFn: () => analyticsApi.getDeviceHealthTrends(params),
    staleTime: 60000, // 1 minute
    ...options,
  })
}

export { ANALYTICS_KEYS }
