import { Building2, Users, Monitor, FileImage, Activity, TrendingUp, AlertCircle, CheckCircle2, Clock } from 'lucide-react'

/**
 * SuperDashboard Component
 * Main dashboard for Super Admin with global statistics
 *
 * Features:
 * - Global statistics cards
 * - Recent activities across all tenants
 * - System health indicators
 * - Quick actions
 *
 * Uses mock data - ready to connect to API
 */
export default function SuperDashboard() {
  // Mock data - replace with API calls
  const stats = [
    {
      label: 'Total Organizations',
      value: '24',
      change: '+3 this month',
      icon: Building2,
      color: 'blue',
      trend: 'up'
    },
    {
      label: 'Active Users',
      value: '342',
      change: '+18 this week',
      icon: Users,
      color: 'green',
      trend: 'up'
    },
    {
      label: 'Total Devices',
      value: '1,247',
      change: '+52 this month',
      icon: Monitor,
      color: 'purple',
      trend: 'up'
    },
    {
      label: 'Total Content',
      value: '8,451',
      change: '+156 this week',
      icon: FileImage,
      color: 'orange',
      trend: 'up'
    }
  ]

  const recentActivities = [
    {
      id: 1,
      type: 'tenant_created',
      message: 'New organization "Hotel Santika" created',
      tenant: 'Hotel Santika',
      timestamp: '2 minutes ago',
      icon: Building2,
      color: 'green'
    },
    {
      id: 2,
      type: 'user_created',
      message: 'New user registered in "PT. Retail Indonesia"',
      tenant: 'PT. Retail Indonesia',
      timestamp: '15 minutes ago',
      icon: Users,
      color: 'blue'
    },
    {
      id: 3,
      type: 'device_registered',
      message: '5 new devices registered in "Mall Plaza"',
      tenant: 'Mall Plaza',
      timestamp: '1 hour ago',
      icon: Monitor,
      color: 'purple'
    },
    {
      id: 4,
      type: 'content_uploaded',
      message: '23 new content items uploaded in "Hotel Bali Resort"',
      tenant: 'Hotel Bali Resort',
      timestamp: '2 hours ago',
      icon: FileImage,
      color: 'orange'
    },
    {
      id: 5,
      type: 'tenant_suspended',
      message: 'Organization "Demo Company" suspended (payment overdue)',
      tenant: 'Demo Company',
      timestamp: '3 hours ago',
      icon: AlertCircle,
      color: 'red'
    }
  ]

  const systemHealth = [
    { label: 'API Server', status: 'healthy', uptime: '99.9%' },
    { label: 'Database', status: 'healthy', uptime: '99.8%' },
    { label: 'Storage', status: 'warning', uptime: '85% used' },
    { label: 'CDN', status: 'healthy', uptime: '99.9%' }
  ]

  const getColorClasses = (color) => {
    const colors = {
      blue: 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
      green: 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400',
      purple: 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400',
      orange: 'bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400',
      red: 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400'
    }
    return colors[color] || colors.blue
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Dashboard Overview
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Monitor all organizations and system health
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => {
          const Icon = stat.icon
          return (
            <div
              key={index}
              className="bg-white dark:bg-gray-800 rounded-xl border border-gray-300 dark:border-gray-600 p-6 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-center justify-between mb-4">
                <div className={`p-3 rounded-lg ${getColorClasses(stat.color)}`}>
                  <Icon className="w-6 h-6" />
                </div>
                <TrendingUp className="w-5 h-5 text-green-500" />
              </div>
              <h3 className="text-3xl font-bold text-gray-900 dark:text-white mb-1">
                {stat.value}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                {stat.label}
              </p>
              <p className="text-xs text-green-600 dark:text-green-400 font-medium">
                {stat.change}
              </p>
            </div>
          )
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activities */}
        <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-xl border border-gray-300 dark:border-gray-600 p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-bold text-gray-900 dark:text-white">
                Recent Activities
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Latest actions across all organizations
              </p>
            </div>
            <Activity className="w-5 h-5 text-gray-400" />
          </div>

          <div className="space-y-4">
            {recentActivities.map((activity) => {
              const Icon = activity.icon
              return (
                <div
                  key={activity.id}
                  className="flex items-start gap-4 p-4 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                >
                  <div className={`p-2 rounded-lg ${getColorClasses(activity.color)}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {activity.message}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {activity.tenant}
                      </span>
                      <span className="text-xs text-gray-400">•</span>
                      <span className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {activity.timestamp}
                      </span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

          <button className="w-full mt-4 py-2 text-sm text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors">
            View All Activities
          </button>
        </div>

        {/* System Health */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-300 dark:border-gray-600 p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-bold text-gray-900 dark:text-white">
                System Health
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Infrastructure status
              </p>
            </div>
            <CheckCircle2 className="w-5 h-5 text-green-500" />
          </div>

          <div className="space-y-4">
            {systemHealth.map((service, index) => (
              <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${
                    service.status === 'healthy' ? 'bg-green-500' :
                    service.status === 'warning' ? 'bg-yellow-500' :
                    'bg-red-500'
                  } ${service.status === 'healthy' ? 'animate-pulse' : ''}`} />
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {service.label}
                  </span>
                </div>
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {service.uptime}
                </span>
              </div>
            ))}
          </div>

          <div className="mt-6 p-4 bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <AlertCircle className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              <span className="text-sm font-semibold text-blue-900 dark:text-blue-300">
                Action Required
              </span>
            </div>
            <p className="text-xs text-gray-700 dark:text-gray-300">
              Storage is reaching capacity. Consider upgrading storage plan.
            </p>
            <button className="mt-3 w-full py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded-lg transition-colors">
              View Details
            </button>
          </div>
        </div>
      </div>

      {/* Quick Stats Footer */}
      <div className="bg-gradient-to-br from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 rounded-xl border border-purple-200 dark:border-purple-800 p-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div>
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Avg. Devices/Org</p>
            <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">52</p>
          </div>
          <div>
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Active Subscriptions</p>
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">21</p>
          </div>
          <div>
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Monthly Revenue</p>
            <p className="text-2xl font-bold text-green-600 dark:text-green-400">$24.5K</p>
          </div>
          <div>
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Uptime</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">99.9%</p>
          </div>
        </div>
      </div>
    </div>
  )
}
