/**
 * Dashboard API
 *
 * LAYER 2: DATA ACCESS
 * API calls for dashboard statistics and metrics
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';

// Types
export interface DashboardStats {
  total_devices: number;
  online_devices: number;
  offline_devices: number;
  warning_devices: number;
  error_devices: number;
  total_contents: number;
  total_storage_bytes: number;
  active_playlists: number;
  total_watch_time_seconds: number;
  avg_completion_rate: number;
  total_playback_events: number;
}

export interface DeviceHealthSummary {
  healthy: number;
  warning: number;
  error: number;
  offline: number;
  issues: {
    type: string;
    count: number;
    devices: string[];
  }[];
}

export interface LiveDevice {
  id: number;
  name: string;
  status: 'online' | 'offline' | 'warning' | 'error';
  location: string;
  current_content: string | null;
  last_seen: string;
  cpu_usage: number | null;
  memory_usage: number | null;
  storage_usage: number | null;
}

export interface ContentPerformance {
  content_id: number;
  content_name: string;
  content_type: string;
  total_plays: number;
  unique_devices: number;
  total_duration_seconds: number;
  avg_completion_rate: number;
  last_played: string;
}

export interface ActivePlaylistAssignment {
  playlist_id: number;
  playlist_name: string;
  device_count: number;
  content_count: number;
  total_duration_seconds: number;
  last_updated: string;
  devices: string[];
}

export interface PlaybackTimeline {
  date: string;
  playback_count: number;
  unique_devices: number;
  total_duration_seconds: number;
}

export interface RecentActivity {
  id: number;
  timestamp: string;
  action: string;
  user: string;
  resource_type: string;
  resource_name: string;
  details: string | null;
}

export interface SystemAlert {
  id: number;
  severity: 'info' | 'warning' | 'error' | 'critical';
  title: string;
  message: string;
  timestamp: string;
  acknowledged: boolean;
  device_id: number | null;
  device_name: string | null;
}

export interface SystemInfo {
  storage_total_bytes: number;
  storage_used_bytes: number;
  storage_free_bytes: number;
  content_by_type: {
    type: string;
    count: number;
    size_bytes: number;
  }[];
  database_size_bytes: number;
  uptime_seconds: number;
}

// API functions
export const dashboardApi = {
  getStats: async (): Promise<DashboardStats> => {
    const { data } = await apiClient.get('/api/v1/dashboard/stats');
    return data;
  },

  getDeviceHealth: async (): Promise<DeviceHealthSummary> => {
    const { data } = await apiClient.get('/api/v1/dashboard/device-health');
    return data;
  },

  getLiveDevices: async (): Promise<LiveDevice[]> => {
    const { data } = await apiClient.get('/api/v1/dashboard/live-devices');
    return data;
  },

  getContentPerformance: async (limit: number = 10): Promise<ContentPerformance[]> => {
    const { data } = await apiClient.get(`/api/v1/dashboard/content-performance?limit=${limit}`);
    return data;
  },

  getActivePlaylistAssignments: async (): Promise<ActivePlaylistAssignment[]> => {
    const { data } = await apiClient.get('/api/v1/dashboard/active-playlists');
    return data;
  },

  getPlaybackTimeline: async (days: number = 7): Promise<PlaybackTimeline[]> => {
    const { data } = await apiClient.get(`/api/v1/dashboard/playback-timeline?days=${days}`);
    return data;
  },

  getRecentActivity: async (limit: number = 20): Promise<RecentActivity[]> => {
    const { data } = await apiClient.get(`/api/v1/dashboard/recent-activity?limit=${limit}`);
    return data;
  },

  getSystemAlerts: async (): Promise<SystemAlert[]> => {
    const { data } = await apiClient.get('/api/v1/dashboard/alerts');
    return data;
  },

  acknowledgeAlert: async (alertId: number): Promise<void> => {
    await apiClient.post(`/api/v1/dashboard/alerts/${alertId}/acknowledge`);
  },

  getSystemInfo: async (): Promise<SystemInfo> => {
    const { data } = await apiClient.get('/api/v1/dashboard/system-info');
    return data;
  },
};

// React Query hooks
export const useDashboardStats = () => {
  return useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: dashboardApi.getStats,
    refetchInterval: 30000, // Refetch every 30 seconds
  });
};

export const useDeviceHealth = () => {
  return useQuery({
    queryKey: ['dashboard', 'device-health'],
    queryFn: dashboardApi.getDeviceHealth,
    refetchInterval: 30000,
  });
};

export const useLiveDevices = () => {
  return useQuery({
    queryKey: ['dashboard', 'live-devices'],
    queryFn: dashboardApi.getLiveDevices,
    refetchInterval: 10000, // Refetch every 10 seconds for live data
  });
};

export const useContentPerformance = (limit: number = 10) => {
  return useQuery({
    queryKey: ['dashboard', 'content-performance', limit],
    queryFn: () => dashboardApi.getContentPerformance(limit),
    refetchInterval: 60000, // Refetch every minute
  });
};

export const useActivePlaylistAssignments = () => {
  return useQuery({
    queryKey: ['dashboard', 'active-playlists'],
    queryFn: dashboardApi.getActivePlaylistAssignments,
    refetchInterval: 60000,
  });
};

export const usePlaybackTimeline = (days: number = 7) => {
  return useQuery({
    queryKey: ['dashboard', 'playback-timeline', days],
    queryFn: () => dashboardApi.getPlaybackTimeline(days),
    refetchInterval: 60000,
  });
};

export const useRecentActivity = (limit: number = 20) => {
  return useQuery({
    queryKey: ['dashboard', 'recent-activity', limit],
    queryFn: () => dashboardApi.getRecentActivity(limit),
    refetchInterval: 30000,
  });
};

export const useSystemAlerts = () => {
  return useQuery({
    queryKey: ['dashboard', 'alerts'],
    queryFn: dashboardApi.getSystemAlerts,
    refetchInterval: 30000,
  });
};

export const useSystemInfo = () => {
  return useQuery({
    queryKey: ['dashboard', 'system-info'],
    queryFn: dashboardApi.getSystemInfo,
    refetchInterval: 60000,
  });
};
