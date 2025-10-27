import { useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { devicesAPI, contentAPI, tagsAPI, playlistsAPI } from '../services/api'
import { Monitor, FileImage, Tag, Tv, Wifi, ListVideo, Link, CheckCircle, XCircle, Eye, WifiOff } from 'lucide-react'
import { LoadingSkeleton, Button } from '../components/shared'
import { showToast } from '../utils/toast'
import { useDashboardWebSocket } from '../hooks/useDashboardWebSocket'
import ActivityTimeline from '../components/dashboard/ActivityTimeline'

export default function Dashboard() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  // FASE 9.3: WebSocket real-time updates
  const { isConnected: wsConnected, connectionStatus: wsStatus } = useDashboardWebSocket()

  const { data: devices, isLoading } = useQuery({
    queryKey: ['devices'],
    queryFn: () => devicesAPI.list().then(res => res.data),
    refetchInterval: 10000, // Refresh every 10 seconds
  })

  const { data: content } = useQuery({
    queryKey: ['content'],
    queryFn: () => contentAPI.list().then(res => res.data),
  })

  const { data: tags } = useQuery({
    queryKey: ['tags'],
    queryFn: () => tagsAPI.list().then(res => res.data),
  })

  // Fetch playlists data (FASE 1.1)
  const { data: playlists } = useQuery({
    queryKey: ['playlists'],
    queryFn: () => playlistsAPI.list().then(res => res.data),
  })

  // Fetch all content assignments (FASE 1.2)
  const { data: allAssignments } = useQuery({
    queryKey: ['all-content-assignments'],
    queryFn: async () => {
      if (!content?.items) return {}

      const assignments = {}
      for (const contentItem of content.items) {
        try {
          const res = await contentAPI.getAssignments(contentItem.id)
          assignments[contentItem.id] = res.data
        } catch (err) {
          assignments[contentItem.id] = []
        }
      }
      return assignments
    },
    enabled: !!content?.items,
  })

  // FASE 2.1: Approve device mutation
  const approveDeviceMutation = useMutation({
    mutationFn: (deviceId) => devicesAPI.update(deviceId, { status: 'active' }),
    onSuccess: () => {
      queryClient.invalidateQueries(['devices'])
      showToast.success('Device approved successfully!')
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Failed to approve device')
    }
  })

  // FASE 2.1: Reject device mutation
  const rejectDeviceMutation = useMutation({
    mutationFn: devicesAPI.delete,
    onSuccess: () => {
      queryClient.invalidateQueries(['devices'])
      showToast.success('Device rejected successfully!')
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Failed to reject device')
    }
  })

  // Helper function to check if device is online
  const isDeviceOnline = (lastSeen) => {
    if (!lastSeen) {
      return false
    }
    // Backend sends UTC timestamps without 'Z', add it to ensure correct parsing
    const utcLastSeen = lastSeen.endsWith('Z') ? lastSeen : lastSeen + 'Z'
    const lastSeenTime = new Date(utcLastSeen).getTime()
    const now = Date.now()
    const timeout = 60000 // 60 seconds (2x heartbeat interval of 30s)
    const diff = now - lastSeenTime
    const isOnline = diff < timeout
    return isOnline
  }

  // Memoize devicesList to prevent array recreation on every render
  const devicesList = useMemo(() => devices?.devices || [], [devices?.devices])

  // FASE 2.1: Filter pending devices
  const pendingDevices = useMemo(() =>
    devicesList.filter(d => d.status === 'pending'),
    [devicesList]
  )

  // FASE 5.3: Top Tags by device count
  const topTags = useMemo(() => {
    return tags?.items
      ?.sort((a, b) => b.device_count - a.device_count)
      ?.slice(0, 5) || []
  }, [tags?.items])

  // Calculate stats - Memoized to prevent recalculation on every render
  const deviceStats = useMemo(() => {
    return {
      tvDevices: devicesList.filter(d => d.device_type === 'tv').length || 0,
      monitorDevices: devicesList.filter(d => d.device_type === 'monitor').length || 0,
      activeDevices: devicesList.filter(d => d.status === 'active').length || 0,
      pendingDevices: devicesList.filter(d => d.status === 'pending').length || 0,
      onlineDevices: devicesList.filter(d => isDeviceOnline(d.last_seen)).length || 0,
    }
  }, [devicesList])

  const stats = useMemo(() => {
    // FASE 1.3: Enhanced device breakdown (Browser vs App)
    const browserDevices = devicesList.filter(d => d.device_type === 'monitor').length || 0
    const appDevices = devicesList.filter(d => d.device_type === 'tv').length || 0

    // FASE 1.2: Content assignment stats
    const assignedContent = content?.items ? content.items.filter(c => {
      const assignments = allAssignments?.[c.id]
      return assignments && assignments.length > 0
    }).length : 0
    const totalContent = content?.total || 0
    const assignmentRate = totalContent > 0 ? Math.round((assignedContent / totalContent) * 100) : 0

    // FASE 1.1: Playlists stats
    const totalPlaylists = playlists?.total || 0
    const activePlaylists = playlists?.items?.filter(p => p.is_active).length || 0

    return [
      // Row 1 - Main Stats
      {
        name: 'Total Devices',
        value: devices?.total || 0,
        subtitle: `${browserDevices} browsers • ${appDevices} apps`,
        icon: Monitor,
        color: 'blue',
      },
      {
        name: 'Online Devices',
        value: deviceStats.onlineDevices,
        subtitle: `${deviceStats.activeDevices} active • ${deviceStats.pendingDevices} pending`,
        icon: Wifi,
        color: 'green',
      },
      {
        name: 'Total Contents',
        value: totalContent,
        subtitle: `${content?.items?.filter(c => c.is_active).length || 0} active`,
        icon: FileImage,
        color: 'purple',
      },
      {
        name: 'Tags',
        value: tags?.total || 0,
        subtitle: 'Device groups',
        icon: Tag,
        color: 'orange',
      },
      // Row 2 - Additional Stats
      {
        name: 'Playlists',
        value: totalPlaylists,
        subtitle: `${activePlaylists} active • ${totalPlaylists - activePlaylists} inactive`,
        icon: ListVideo,
        color: 'indigo',
      },
      {
        name: 'Assigned Contents',
        value: assignedContent,
        subtitle: `${assignmentRate}% assignment rate`,
        icon: Link,
        color: 'teal',
      },
      {
        name: 'Browser Displays',
        value: browserDevices,
        subtitle: 'Web-based viewers',
        icon: Monitor,
        color: 'purple',
      },
      {
        name: 'App Displays',
        value: appDevices,
        subtitle: 'App-based viewers',
        icon: Tv,
        color: 'blue',
      },
    ]
  }, [devices?.total, deviceStats, devicesList, content?.total, content?.items, tags?.total, playlists?.total, playlists?.items, allAssignments])

  // Show loading skeleton while fetching
  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-gray-900">
        <div className="fixed top-0 left-0 right-0 lg:left-64 z-40 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 sm:px-6 lg:px-8 py-3">
          <div className="pl-12 lg:pl-0">
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
            <div className="h-4 w-64 bg-gray-200 dark:bg-gray-700 rounded animate-pulse mt-1"></div>
          </div>
        </div>

        <div className="pt-20 sm:pt-24 lg:pt-20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            {/* Loading Stats - 8 cards in 2 cols mobile, 4 cols desktop */}
            <div className="grid grid-cols-2 md:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-8">
              <LoadingSkeleton variant="stats" count={8} />
            </div>

            {/* Loading Recent Devices & Content */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
              <LoadingSkeleton variant="list" count={5} />
              <LoadingSkeleton variant="list" count={5} />
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-gray-900">
      {/* FASE 9.1: Page Header with Description - Simple, no search/stats */}
      <div className="fixed top-0 left-0 right-0 lg:left-64 z-40 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-md transition-colors">
        <div className="px-4 sm:px-6 lg:px-8 py-3">
          <div className="flex items-center justify-between pl-12 lg:pl-0">
            <div>
              <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
              <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-300 mt-1">
                Overview of your digital signage system
              </p>
            </div>

          {/* FASE 9.3: WebSocket Status Indicator */}
          <div className="flex items-center gap-2 text-xs">
            {wsConnected ? (
              <div className="flex items-center gap-1 text-green-600 dark:text-green-400">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span>Live</span>
              </div>
            ) : (
              <div className="flex items-center gap-1 text-gray-500 dark:text-gray-400" title={wsStatus}>
                <WifiOff className="w-3 h-3" />
                <span>Auto-refresh</span>
              </div>
            )}
          </div>
        </div>
      </div>
      </div>

      {/* Content with padding to account for fixed header */}
      {/* Dashboard has simpler header, so needs less padding than other pages */}
      <div className="pt-20 sm:pt-24 lg:pt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {/* Stats Grid with fade-in animation - 2 cols mobile, 2 cols tablet, 4 cols desktop */}
          <div className="grid grid-cols-2 md:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-8 animate-fade-in">
            {stats.map((stat) => {
              const Icon = stat.icon
          const bgColors = {
            blue: 'bg-blue-100 dark:bg-blue-900/30',
            green: 'bg-green-100 dark:bg-green-900/30',
            purple: 'bg-purple-100 dark:bg-purple-900/30',
            orange: 'bg-orange-100 dark:bg-orange-900/30',
            indigo: 'bg-indigo-100 dark:bg-indigo-900/30',
            teal: 'bg-teal-100 dark:bg-teal-900/30'
          }
          const textColors = {
            blue: 'text-blue-600',
            green: 'text-green-600',
            purple: 'text-purple-600',
            orange: 'text-orange-600',
            indigo: 'text-indigo-600',
            teal: 'text-teal-600'
          }

          return (
            <div
              key={stat.name}
              className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-300 dark:border-gray-600 p-4 hover:shadow-xl transition-shadow"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="text-sm text-gray-600 dark:text-gray-400 font-medium">{stat.name}</p>
                  <p className="text-3xl font-bold text-gray-800 dark:text-gray-100 mt-2">{stat.value}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{stat.subtitle}</p>
                </div>
                <div className={`p-3 rounded-full ${bgColors[stat.color]}`}>
                  <Icon className={`w-6 h-6 ${textColors[stat.color]}`} />
                </div>
              </div>
            </div>
          )
            })}
          </div>

          {/* Pending Approvals Section */}
          {pendingDevices.length > 0 && (
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border-2 border-yellow-400 dark:border-yellow-700 rounded-xl p-4 sm:p-6 mb-8 animate-fade-in">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 bg-yellow-500 rounded-full animate-pulse"></div>
              <h2 className="text-xl font-bold text-yellow-800">
                Pending Approvals ({pendingDevices.length})
              </h2>
            </div>
            <Button
              variant="warning"
              leftIcon={<Eye className="w-4 h-4" />}
              onClick={() => navigate('/devices')}
            >
              View All
            </Button>
          </div>

          <div className="grid gap-3">
            {pendingDevices.slice(0, 3).map(device => (
              <div key={device.id} className="bg-white dark:bg-gray-800 rounded-lg p-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`flex items-center justify-center w-12 h-12 rounded-full ${
                    device.device_type === 'tv' ? 'bg-blue-100 dark:bg-blue-900/30' : 'bg-green-100 dark:bg-green-900/30'
                  }`}>
                    {device.device_type === 'tv' ? (
                      <Tv className="w-6 h-6 text-blue-600" />
                    ) : (
                      <Monitor className="w-6 h-6 text-green-600" />
                    )}
                  </div>
                  <div>
                    <p className="font-bold text-gray-800 dark:text-gray-100">{device.device_name}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {device.platform || device.device_type.charAt(0).toUpperCase() + device.device_type.slice(1)} • {device.ip_address || '-'}
                    </p>
                    {device.last_seen && (
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {new Date(device.last_seen).toLocaleString()}
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button
                    variant="success"
                    size="sm"
                    leftIcon={<CheckCircle className="w-4 h-4" />}
                    onClick={() => approveDeviceMutation.mutate(device.id)}
                    disabled={approveDeviceMutation.isLoading}
                  >
                    Approve
                  </Button>
                  <Button
                    variant="danger"
                    size="sm"
                    leftIcon={<XCircle className="w-4 h-4" />}
                    onClick={() => {
                      if (confirm(`Reject device "${device.device_name}"?`)) {
                        rejectDeviceMutation.mutate(device.id)
                      }
                    }}
                    disabled={rejectDeviceMutation.isLoading}
                  >
                    Reject
                  </Button>
                </div>
              </div>
            ))}
            {pendingDevices.length > 3 && (
              <p className="text-sm text-yellow-700 text-center pt-2">
                and {pendingDevices.length - 3} more pending device(s)...
              </p>
            )}
          </div>
            </div>
          )}

          {/* Recent Devices & Content Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 animate-fade-in">
            {/* Recent Devices */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-300 dark:border-gray-600 p-4 sm:p-6">
              <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100 mb-4">Recent Devices</h2>
              {devicesList && devicesList.length > 0 ? (
                <div className="space-y-3">
              {devicesList.slice(0, 5).map((device) => {
                const online = isDeviceOnline(device.last_seen)
                return (
                  <div
                    key={device.id}
                    className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-900 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  >
                    <div className="flex items-center flex-1">
                      {device.device_type === 'tv' ? (
                        <Tv className="w-5 h-5 text-blue-600 mr-3" />
                      ) : (
                        <Monitor className="w-5 h-5 text-green-600 mr-3" />
                      )}
                      <div className="flex-1">
                        <div className="flex items-center">
                          <p className="font-medium text-gray-800 dark:text-gray-100">{device.device_name}</p>
                          {device.status === 'active' && (
                            <div className="ml-2 flex items-center">
                              {online ? (
                                <div className="flex items-center">
                                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-1"></div>
                                  <span className="text-xs text-green-600 font-medium">Online</span>
                                </div>
                              ) : (
                                <div className="flex items-center">
                                  <div className="w-2 h-2 bg-red-500 rounded-full mr-1"></div>
                                  <span className="text-xs text-red-600 font-medium">Offline</span>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {device.platform || device.device_type.charAt(0).toUpperCase() + device.device_type.slice(1)} • {device.ip_address || device.unique_code || 'N/A'}
                        </p>
                        {device.last_seen && (
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            Last seen: {new Date(device.last_seen).toLocaleString()}
                          </p>
                        )}
                      </div>
                    </div>
                    <span
                      className={`px-3 py-1 rounded-full text-sm font-medium ${
                        device.status === 'active'
                          ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                          : device.status === 'pending'
                          ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                      }`}
                    >
                      {device.status}
                    </span>
                  </div>
                )
              })}
                </div>
              ) : (
                <p className="text-gray-500 dark:text-gray-400 text-center py-8">No devices registered yet</p>
              )}
            </div>

            {/* Recent Content */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-300 dark:border-gray-600 p-4 sm:p-6">
              <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100 mb-4">Recent Content</h2>
              {content?.items && content.items.length > 0 ? (
                <div className="space-y-3">
              {content.items.slice(0, 5).map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-900 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                  <div className="flex items-center flex-1">
                    <FileImage className="w-5 h-5 text-purple-600 mr-3" />
                    <div className="flex-1">
                      <p className="font-medium text-gray-800 dark:text-gray-100">{item.title}</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {item.content_type.toUpperCase()} • {item.duration}s
                      </p>
                    </div>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-sm font-medium ${
                      item.is_active
                        ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                    }`}
                  >
                    {item.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              ))}
                </div>
              ) : (
                <p className="text-gray-500 dark:text-gray-400 text-center py-8">No content uploaded yet</p>
              )}
            </div>
          </div>

          {/* FASE 3.2: Activity Timeline Section */}
          <div className="mt-4 sm:mt-6 animate-fade-in">
            <ActivityTimeline />
          </div>

          {/* FASE 5.3: Top Tags by Usage Section */}
          {topTags.length > 0 && (
            <div className="mt-4 sm:mt-6 animate-fade-in">
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-300 dark:border-gray-600 p-4 sm:p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100">Top Tags by Usage</h2>
                  <button
                    onClick={() => navigate('/tags')}
                    className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium transition-colors"
                  >
                    View All Tags →
                  </button>
                </div>
                <div className="space-y-3">
                  {topTags.map((tag, index) => (
                    <div
                      key={tag.id}
                      className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-900 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors group cursor-pointer"
                      onClick={() => navigate('/tags')}
                    >
                      <div className="flex items-center gap-4 flex-1">
                        {/* Ranking Number */}
                        <div className="flex items-center justify-center w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 text-white font-bold text-lg">
                          #{index + 1}
                        </div>

                        {/* Color Indicator */}
                        <div
                          className="w-4 h-4 rounded-full border-2 border-white dark:border-gray-800 shadow-md flex-shrink-0"
                          style={{ backgroundColor: tag.color }}
                        />

                        {/* Tag Name */}
                        <div className="flex-1">
                          <p className="font-semibold text-gray-800 dark:text-gray-100 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                            {tag.tag_name}
                          </p>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {tag.description || 'No description'}
                          </p>
                        </div>
                      </div>

                      {/* Device Count Badge */}
                      <div className="flex items-center gap-2 ml-4">
                        <Tag className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                        <span className="text-lg font-bold text-gray-700 dark:text-gray-300">
                          {tag.device_count}
                        </span>
                        <span className="text-sm text-gray-500 dark:text-gray-400">
                          {tag.device_count === 1 ? 'device' : 'devices'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Empty State for Tags */}
                {tags?.items && tags.items.length > 5 && (
                  <div className="mt-4 text-center">
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      and {tags.items.length - 5} more tag{tags.items.length - 5 !== 1 ? 's' : ''}...
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
