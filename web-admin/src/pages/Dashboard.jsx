import { useQuery } from '@tanstack/react-query'
import { devicesAPI, contentAPI } from '../services/api'
import { Monitor, FileImage, Activity, TrendingUp } from 'lucide-react'

export default function Dashboard() {
  const { data: devices } = useQuery({
    queryKey: ['devices'],
    queryFn: () => devicesAPI.list().then(res => res.data),
  })

  const { data: content } = useQuery({
    queryKey: ['content'],
    queryFn: () => contentAPI.list().then(res => res.data),
  })

  const stats = [
    {
      name: 'Total Devices',
      value: devices?.total || 0,
      icon: Monitor,
      color: 'blue',
    },
    {
      name: 'Active Devices',
      value: devices?.items?.filter(d => d.status === 'active').length || 0,
      icon: Activity,
      color: 'green',
    },
    {
      name: 'Total Content',
      value: content?.total || 0,
      icon: FileImage,
      color: 'purple',
    },
    {
      name: 'Active Content',
      value: content?.items?.filter(c => c.is_active).length || 0,
      icon: TrendingUp,
      color: 'orange',
    },
  ]

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-800 mb-8">Dashboard</h1>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat) => {
          const Icon = stat.icon
          const bgColor = `bg-${stat.color}-100`
          const textColor = `text-${stat.color}-600`

          return (
            <div
              key={stat.name}
              className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 font-medium">{stat.name}</p>
                  <p className="text-3xl font-bold text-gray-800 mt-2">{stat.value}</p>
                </div>
                <div className={`p-3 rounded-full ${bgColor}`}>
                  <Icon className={`w-6 h-6 ${textColor}`} />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Recent Devices */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4">Recent Devices</h2>
        {devices?.items && devices.items.length > 0 ? (
          <div className="space-y-3">
            {devices.items.slice(0, 5).map((device) => (
              <div
                key={device.id}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center">
                  <Monitor className="w-5 h-5 text-gray-600 mr-3" />
                  <div>
                    <p className="font-medium text-gray-800">{device.device_name}</p>
                    <p className="text-sm text-gray-600">
                      {device.device_type.toUpperCase()} • {device.ip_address || 'N/A'}
                    </p>
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
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">No devices registered yet</p>
        )}
      </div>
    </div>
  )
}
