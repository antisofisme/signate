/**
 * ATLAS_CHAT_AI Dashboard
 * System overview with domain-based quick access
 * MANTRA/PUGUH style layout
 */

import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  BarChart3,
  Users,
  MessageSquare,
  Building2,
  Brain,
  Database,
  Search,
  Key,
  Settings,
  Clock,
  Zap,
  History,
  ArrowRight,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui'
import { getSystemStats } from '@/lib/api'

// Domain colors matching sidebar
const DOMAIN_COLORS = {
  chat: {
    bg: 'bg-blue-600',
    bgLight: 'bg-blue-50',
    text: 'text-blue-600',
    border: 'border-blue-200',
  },
  admin: {
    bg: 'bg-emerald-600',
    bgLight: 'bg-emerald-50',
    text: 'text-emerald-600',
    border: 'border-emerald-200',
  },
}

export function Dashboard() {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['systemStats'],
    queryFn: getSystemStats,
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4" />
          <p className="text-gray-500">Loading system stats...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center text-red-500 p-8 bg-red-50 rounded-xl">
        <p className="font-medium">Failed to load stats</p>
        <p className="text-sm mt-1">Please check if the backend is running.</p>
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
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-gray-600">
          ATLAS Chat AI - RAG-powered conversations with 4-layer memory system
        </p>
      </div>

      {/* System Architecture Banner */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl p-6 text-white">
        <h3 className="font-semibold mb-4 text-lg">4-Layer Memory Architecture</h3>
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center p-4 bg-white/10 rounded-lg backdrop-blur">
            <div className="text-2xl font-bold text-yellow-300">L1</div>
            <div className="text-white/90 text-sm font-medium">Working</div>
            <div className="text-white/60 text-xs mt-1">Active context</div>
          </div>
          <div className="text-center p-4 bg-white/10 rounded-lg backdrop-blur">
            <div className="text-2xl font-bold text-green-300">L2</div>
            <div className="text-white/90 text-sm font-medium">Episodic</div>
            <div className="text-white/60 text-xs mt-1">Session summaries</div>
          </div>
          <div className="text-center p-4 bg-white/10 rounded-lg backdrop-blur">
            <div className="text-2xl font-bold text-blue-300">L3</div>
            <div className="text-white/90 text-sm font-medium">Semantic</div>
            <div className="text-white/60 text-xs mt-1">User facts</div>
          </div>
          <div className="text-center p-4 bg-white/10 rounded-lg backdrop-blur">
            <div className="text-2xl font-bold text-purple-300">L4</div>
            <div className="text-white/90 text-sm font-medium">Temporal</div>
            <div className="text-white/60 text-xs mt-1">Time patterns</div>
          </div>
        </div>
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

      {/* Domain Quick Access */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Chat & AI Domain */}
        <div className={`rounded-xl border-2 ${DOMAIN_COLORS.chat.border} overflow-hidden`}>
          <div className={`${DOMAIN_COLORS.chat.bg} p-4 text-white`}>
            <div className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              <h3 className="font-semibold">Chat & AI</h3>
            </div>
            <p className="text-white/80 text-sm mt-1">RAG chat with memory</p>
          </div>
          <div className="p-4 space-y-2">
            <Link
              to="/chat"
              className={`flex items-center justify-between p-3 rounded-lg ${DOMAIN_COLORS.chat.bgLight} hover:bg-blue-100 transition-colors`}
            >
              <div className="flex items-center gap-3">
                <MessageSquare className={`h-5 w-5 ${DOMAIN_COLORS.chat.text}`} />
                <span className="font-medium">Start Chat</span>
              </div>
              <ArrowRight className="h-4 w-4 text-gray-400" />
            </Link>
            <Link
              to="/search"
              className={`flex items-center justify-between p-3 rounded-lg ${DOMAIN_COLORS.chat.bgLight} hover:bg-blue-100 transition-colors`}
            >
              <div className="flex items-center gap-3">
                <Search className={`h-5 w-5 ${DOMAIN_COLORS.chat.text}`} />
                <span className="font-medium">Semantic Search</span>
              </div>
              <ArrowRight className="h-4 w-4 text-gray-400" />
            </Link>
            <Link
              to="/memory"
              className={`flex items-center justify-between p-3 rounded-lg ${DOMAIN_COLORS.chat.bgLight} hover:bg-blue-100 transition-colors`}
            >
              <div className="flex items-center gap-3">
                <Brain className={`h-5 w-5 ${DOMAIN_COLORS.chat.text}`} />
                <span className="font-medium">Memory Facts</span>
              </div>
              <ArrowRight className="h-4 w-4 text-gray-400" />
            </Link>
            <Link
              to="/sessions"
              className={`flex items-center justify-between p-3 rounded-lg ${DOMAIN_COLORS.chat.bgLight} hover:bg-blue-100 transition-colors`}
            >
              <div className="flex items-center gap-3">
                <History className={`h-5 w-5 ${DOMAIN_COLORS.chat.text}`} />
                <span className="font-medium">Chat Sessions</span>
              </div>
              <ArrowRight className="h-4 w-4 text-gray-400" />
            </Link>
          </div>
        </div>

        {/* Administration Domain */}
        <div className={`rounded-xl border-2 ${DOMAIN_COLORS.admin.border} overflow-hidden`}>
          <div className={`${DOMAIN_COLORS.admin.bg} p-4 text-white`}>
            <div className="flex items-center gap-2">
              <Building2 className="h-5 w-5" />
              <h3 className="font-semibold">Administration</h3>
            </div>
            <p className="text-white/80 text-sm mt-1">System management</p>
          </div>
          <div className="p-4 space-y-2">
            <Link
              to="/tenants"
              className={`flex items-center justify-between p-3 rounded-lg ${DOMAIN_COLORS.admin.bgLight} hover:bg-emerald-100 transition-colors`}
            >
              <div className="flex items-center gap-3">
                <Building2 className={`h-5 w-5 ${DOMAIN_COLORS.admin.text}`} />
                <span className="font-medium">Manage Tenants</span>
              </div>
              <ArrowRight className="h-4 w-4 text-gray-400" />
            </Link>
            <Link
              to="/users"
              className={`flex items-center justify-between p-3 rounded-lg ${DOMAIN_COLORS.admin.bgLight} hover:bg-emerald-100 transition-colors`}
            >
              <div className="flex items-center gap-3">
                <Users className={`h-5 w-5 ${DOMAIN_COLORS.admin.text}`} />
                <span className="font-medium">Manage Users</span>
              </div>
              <ArrowRight className="h-4 w-4 text-gray-400" />
            </Link>
            <Link
              to="/api-keys"
              className={`flex items-center justify-between p-3 rounded-lg ${DOMAIN_COLORS.admin.bgLight} hover:bg-emerald-100 transition-colors`}
            >
              <div className="flex items-center gap-3">
                <Key className={`h-5 w-5 ${DOMAIN_COLORS.admin.text}`} />
                <span className="font-medium">API Keys</span>
              </div>
              <ArrowRight className="h-4 w-4 text-gray-400" />
            </Link>
            <Link
              to="/settings"
              className={`flex items-center justify-between p-3 rounded-lg ${DOMAIN_COLORS.admin.bgLight} hover:bg-emerald-100 transition-colors`}
            >
              <div className="flex items-center gap-3">
                <Settings className={`h-5 w-5 ${DOMAIN_COLORS.admin.text}`} />
                <span className="font-medium">Settings</span>
              </div>
              <ArrowRight className="h-4 w-4 text-gray-400" />
            </Link>
          </div>
        </div>
      </div>

      {/* Performance Stats */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-yellow-500" />
              Cache Performance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Embedding Cache Hit Rate</span>
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
              <div className="text-sm text-gray-500">
                Cached embeddings reduce API calls and improve response time
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-blue-500" />
              Response Time
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Average Response Time</span>
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
              <div className="text-sm text-gray-500">
                End-to-end response time including RAG retrieval and LLM generation
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Service Status */}
      <Card>
        <CardHeader>
          <CardTitle>System Services</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <span className="w-3 h-3 rounded-full bg-green-500" />
              <div>
                <div className="text-sm font-medium">PostgreSQL</div>
                <div className="text-xs text-gray-500">Database</div>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <span className="w-3 h-3 rounded-full bg-green-500" />
              <div>
                <div className="text-sm font-medium">Qdrant</div>
                <div className="text-xs text-gray-500">Vector Store</div>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <span className="w-3 h-3 rounded-full bg-green-500" />
              <div>
                <div className="text-sm font-medium">Redis</div>
                <div className="text-xs text-gray-500">Cache</div>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <span className="w-3 h-3 rounded-full bg-green-500" />
              <div>
                <div className="text-sm font-medium">OpenAI</div>
                <div className="text-xs text-gray-500">LLM Provider</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
