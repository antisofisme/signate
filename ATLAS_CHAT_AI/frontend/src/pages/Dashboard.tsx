import { useQuery } from '@tanstack/react-query'
import { BarChart3, Users, MessageSquare, Building2, Brain, Database } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui'
import { getSystemStats } from '@/lib/api'

export function Dashboard() {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['systemStats'],
    queryFn: getSystemStats,
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center text-red-500 p-4">
        Failed to load stats. Please try again.
      </div>
    )
  }

  const statCards = [
    {
      title: 'Active Tenants',
      value: stats?.active_tenants || 0,
      total: stats?.total_tenants || 0,
      icon: Building2,
      color: 'text-blue-600',
      bg: 'bg-blue-100',
    },
    {
      title: 'Total Users',
      value: stats?.total_users || 0,
      icon: Users,
      color: 'text-green-600',
      bg: 'bg-green-100',
    },
    {
      title: 'Sessions Today',
      value: stats?.active_sessions_today || 0,
      icon: MessageSquare,
      color: 'text-purple-600',
      bg: 'bg-purple-100',
    },
    {
      title: 'Messages Today',
      value: stats?.total_messages_today || 0,
      icon: BarChart3,
      color: 'text-orange-600',
      bg: 'bg-orange-100',
    },
    {
      title: 'Documents',
      value: stats?.total_documents || 0,
      icon: Database,
      color: 'text-cyan-600',
      bg: 'bg-cyan-100',
    },
    {
      title: 'User Facts',
      value: stats?.total_facts || 0,
      icon: Brain,
      color: 'text-pink-600',
      bg: 'bg-pink-100',
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-gray-500">ATLAS Chat AI System Overview</p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {statCards.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-500">
                {stat.title}
              </CardTitle>
              <div className={`rounded-lg p-2 ${stat.bg}`}>
                <stat.icon className={`h-5 w-5 ${stat.color}`} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stat.value.toLocaleString()}
                {stat.total !== undefined && (
                  <span className="text-sm font-normal text-gray-500">
                    {' '}/ {stat.total}
                  </span>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Performance Stats */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Cache Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Cache Hit Rate</span>
                  <span className="font-medium">
                    {((stats?.cache_hit_rate || 0) * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-green-500 transition-all"
                    style={{ width: `${(stats?.cache_hit_rate || 0) * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Response Time</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Average Response Time</span>
                  <span className="font-medium">
                    {(stats?.average_response_time_ms || 0).toFixed(0)} ms
                  </span>
                </div>
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 transition-all"
                    style={{
                      width: `${Math.min((stats?.average_response_time_ms || 0) / 20, 100)}%`,
                    }}
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
