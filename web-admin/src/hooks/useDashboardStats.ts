import { useMemo } from 'react'
import type {
  Device,
  DevicesResponse,
  ContentResponse,
  TagsResponse,
  PlaylistsResponse,
  ContentAssignmentsMap,
  Tag,
  DeviceStatistics,
} from '../types/api'

// ============================================================================
// Type Definitions
// ============================================================================

/** Dashboard stat card data structure */
export interface DashboardStatCard {
  /** Display name of the stat */
  name: string
  /** Numeric value to display */
  value: number
  /** Subtitle text (e.g., breakdown, percentage) */
  subtitle: string
  /** Color variant for the card */
  color: StatColor
}

/** Stat card color variants */
export type StatColor = 'blue' | 'green' | 'purple' | 'orange' | 'indigo' | 'teal'

/** Hook parameters */
export interface UseDashboardStatsParams {
  /** Devices data from API */
  devices: DevicesResponse | undefined
  /** Content data from API */
  content: ContentResponse | undefined
  /** Tags data from API */
  tags: TagsResponse | undefined
  /** Playlists data from API */
  playlists: PlaylistsResponse | undefined
  /** All content assignments data */
  allAssignments: ContentAssignmentsMap | undefined
}

/** Hook return type */
export interface UseDashboardStatsReturn {
  /** Helper function to check if device is online */
  isDeviceOnline: (lastSeen: string | null | undefined) => boolean
  /** Memoized devices list */
  devicesList: Device[]
  /** Devices with pending status */
  pendingDevices: Device[]
  /** Top 5 tags by device count */
  topTags: Tag[]
  /** Device statistics breakdown */
  deviceStats: DeviceStatistics
  /** Main dashboard stats array (8 stat cards) */
  stats: DashboardStatCard[]
}

// ============================================================================
// Hook Implementation
// ============================================================================

/**
 * useDashboardStats Custom Hook
 *
 * Extracts and encapsulates Dashboard business logic for stats calculation
 * Provides memoized stats to prevent unnecessary recalculations
 *
 * Features:
 * - Device online/offline detection based on heartbeat
 * - Device type and status statistics
 * - Content assignment rate calculation
 * - Top tags by device count
 * - Playlist statistics
 * - Memoized computations for performance
 *
 * @param params - Hook parameters containing API response data
 * @returns Dashboard statistics and computed data
 */
export function useDashboardStats({
  devices,
  content,
  tags,
  playlists,
  allAssignments,
}: UseDashboardStatsParams): UseDashboardStatsReturn {
  /**
   * Helper function to check if device is online
   * Device is considered online if last_seen is within 60 seconds (2x heartbeat interval)
   *
   * @param lastSeen - Last seen timestamp from device
   * @returns True if device is online, false otherwise
   */
  const isDeviceOnline = (lastSeen: string | null | undefined): boolean => {
    if (!lastSeen) {
      return false
    }
    // Backend sends UTC timestamps without 'Z', add it to ensure correct parsing
    const utcLastSeen = lastSeen.endsWith('Z') ? lastSeen : lastSeen + 'Z'
    const lastSeenTime = new Date(utcLastSeen).getTime()
    const now = Date.now()
    const timeout = 60000 // 60 seconds (2x heartbeat interval of 30s)
    const diff = now - lastSeenTime
    return diff < timeout
  }

  // Memoize devicesList to prevent array recreation on every render
  const devicesList = useMemo<Device[]>(() => devices?.devices || [], [devices?.devices])

  // Filter pending devices
  const pendingDevices = useMemo<Device[]>(
    () => devicesList.filter((d) => d.status === 'pending'),
    [devicesList]
  )

  // Top Tags by device count (top 5)
  const topTags = useMemo<Tag[]>(() => {
    return (
      tags?.items
        ?.sort((a, b) => b.device_count - a.device_count)
        ?.slice(0, 5) || []
    )
  }, [tags?.items])

  // Device statistics breakdown
  const deviceStats = useMemo<DeviceStatistics>(() => {
    return {
      tvDevices: devicesList.filter((d) => d.device_type === 'tv').length || 0,
      monitorDevices: devicesList.filter((d) => d.device_type === 'monitor').length || 0,
      activeDevices: devicesList.filter((d) => d.status === 'active').length || 0,
      pendingDevices: devicesList.filter((d) => d.status === 'pending').length || 0,
      onlineDevices: devicesList.filter((d) => isDeviceOnline(d.last_seen)).length || 0,
    }
  }, [devicesList])

  // Main dashboard stats array (8 stat cards)
  const stats = useMemo<DashboardStatCard[]>(() => {
    // Enhanced device breakdown (Browser vs App)
    const browserDevices = devicesList.filter((d) => d.device_type === 'monitor').length || 0
    const appDevices = devicesList.filter((d) => d.device_type === 'tv').length || 0

    // Content assignment stats
    const assignedContent = content?.items
      ? content.items.filter((c) => {
          const assignments = allAssignments?.[c.id]
          return assignments && assignments.length > 0
        }).length
      : 0
    const totalContent = content?.total || 0
    const assignmentRate = totalContent > 0 ? Math.round((assignedContent / totalContent) * 100) : 0

    // Playlists stats
    const totalPlaylists = playlists?.total || 0
    const activePlaylists = playlists?.items?.filter((p) => p.is_active).length || 0

    return [
      // Row 1 - Main Stats
      {
        name: 'Total Devices',
        value: devices?.total || 0,
        subtitle: `${browserDevices} browsers • ${appDevices} apps`,
        color: 'blue' as const,
      },
      {
        name: 'Online Devices',
        value: deviceStats.onlineDevices,
        subtitle: `${deviceStats.activeDevices} active • ${deviceStats.pendingDevices} pending`,
        color: 'green' as const,
      },
      {
        name: 'Total Contents',
        value: totalContent,
        subtitle: `${content?.items?.filter((c) => c.is_active).length || 0} active`,
        color: 'purple' as const,
      },
      {
        name: 'Tags',
        value: tags?.total || 0,
        subtitle: 'Device groups',
        color: 'orange' as const,
      },
      // Row 2 - Additional Stats
      {
        name: 'Playlists',
        value: totalPlaylists,
        subtitle: `${activePlaylists} active • ${totalPlaylists - activePlaylists} inactive`,
        color: 'indigo' as const,
      },
      {
        name: 'Assigned Contents',
        value: assignedContent,
        subtitle: `${assignmentRate}% assignment rate`,
        color: 'teal' as const,
      },
      {
        name: 'Browser Displays',
        value: browserDevices,
        subtitle: 'Web-based viewers',
        color: 'purple' as const,
      },
      {
        name: 'App Displays',
        value: appDevices,
        subtitle: 'App-based viewers',
        color: 'blue' as const,
      },
    ]
  }, [
    devices?.total,
    deviceStats,
    devicesList,
    content?.total,
    content?.items,
    tags?.total,
    playlists?.total,
    playlists?.items,
    allAssignments,
  ])

  return {
    // Helper functions
    isDeviceOnline,

    // Computed lists
    devicesList,
    pendingDevices,
    topTags,

    // Stats objects
    deviceStats,
    stats,
  }
}
