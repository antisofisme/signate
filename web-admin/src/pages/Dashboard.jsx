import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { devicesAPI, contentAPI, tagsAPI } from '../services/api'
import { Monitor, FileImage, Activity, TrendingUp, Tag, Tv, Wifi, WifiOff } from 'lucide-react'
import { LoadingSkeleton } from '../components/shared'

export default function Dashboard() {
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

  const stats = useMemo(() => [
    {
      name: 'Total Devices',
      value: devices?.total || 0,
      subtitle: `${deviceStats.tvDevices} TVs • ${deviceStats.monitorDevices} Monitors`,
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
      name: 'Total Content',
      value: content?.total || 0,
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
  ], [devices?.total, deviceStats, content?.total, content?.items, tags?.total])

  // Show loading skeleton while fetching
  if (isLoading) {
    return (
      <div>
        <div className="sticky top-0 z-50 bg-white pb-4 mb-4 border-b border-gray-200 px-6">
          <h1 className="text-3xl font-bold text-gray-800 pt-4">Dashboard</h1>
        </div>

        {/* Loading Stats */}
        <LoadingSkeleton variant="stats" count={4} />

        {/* Loading Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
          <LoadingSkeleton variant="list" count={5} />
          <LoadingSkeleton variant="list" count={5} />
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="sticky top-0 z-50 bg-white pb-4 mb-4 border-b border-gray-200 px-6">
        <h1 className="text-3xl font-bold text-gray-800 pt-4">Dashboard</h1>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat) => {
          const Icon = stat.icon
          const bgColors = {
            blue: 'bg-blue-100',
            green: 'bg-green-100',
            purple: 'bg-purple-100',
            orange: 'bg-orange-100'
          }
          const textColors = {
            blue: 'text-blue-600',
            green: 'text-green-600',
            purple: 'text-purple-600',
            orange: 'text-orange-600'
          }

          return (
            <div
              key={stat.name}
              className="bg-white rounded-xl shadow-lg border border-gray-300 p-6 hover:shadow-xl transition-shadow"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex-1">
                  <p className="text-sm text-gray-600 font-medium">{stat.name}</p>
                  <p className="text-3xl font-bold text-gray-800 mt-2">{stat.value}</p>
                  <p className="text-xs text-gray-500 mt-1">{stat.subtitle}</p>
                </div>
                <div className={`p-3 rounded-full ${bgColors[stat.color]}`}>
                  <Icon className={`w-6 h-6 ${textColors[stat.color]}`} />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Recent Devices & Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Devices */}
        <div className="bg-white rounded-xl shadow-lg border border-gray-300 p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Recent Devices</h2>
          {devicesList && devicesList.length > 0 ? (
            <div className="space-y-3">
              {devicesList.slice(0, 5).map((device) => {
                const online = isDeviceOnline(device.last_seen)
                return (
                  <div
                    key={device.id}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex items-center flex-1">
                      {device.device_type === 'tv' ? (
                        <Tv className="w-5 h-5 text-blue-600 mr-3" />
                      ) : (
                        <Monitor className="w-5 h-5 text-green-600 mr-3" />
                      )}
                      <div className="flex-1">
                        <div className="flex items-center">
                          <p className="font-medium text-gray-800">{device.device_name}</p>
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
                        <p className="text-sm text-gray-600">
                          {device.device_type.toUpperCase()} • {device.ip_address || device.unique_code || 'N/A'}
                        </p>
                        {device.last_seen && (
                          <p className="text-xs text-gray-500">
                            Last seen: {new Date(device.last_seen).toLocaleString()}
                          </p>
                        )}
                      </div>
                    </div>
                    <span
                      className={`px-3 py-1 rounded-full text-sm font-medium ${
                        device.status === 'active'
                          ? 'bg-green-100 text-green-700'
                          : device.status === 'pending'
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {device.status}
                    </span>
                  </div>
                )
              })}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No devices registered yet</p>
          )}
        </div>

        {/* Recent Content */}
        <div className="bg-white rounded-xl shadow-lg border border-gray-300 p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Recent Content</h2>
          {content?.items && content.items.length > 0 ? (
            <div className="space-y-3">
              {content.items.slice(0, 5).map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center flex-1">
                    <FileImage className="w-5 h-5 text-purple-600 mr-3" />
                    <div className="flex-1">
                      <p className="font-medium text-gray-800">{item.title}</p>
                      <p className="text-sm text-gray-600">
                        {item.content_type.toUpperCase()} • {item.duration}s
                      </p>
                    </div>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-sm font-medium ${
                      item.is_active
                        ? 'bg-green-100 text-green-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}
                  >
                    {item.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No content uploaded yet</p>
          )}
        </div>
      </div>
    </div>
  )
}
