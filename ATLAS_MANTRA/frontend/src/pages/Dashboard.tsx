import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../shared/api'
import { GROUPS, GROUP_LABELS, FEATURES, FEATURE_LABELS } from '../shared/constants'

const GROUP_COLORS: Record<string, { bg: string; text: string; light: string }> = {
  'GROUP-1': { bg: 'bg-blue-600', text: 'text-blue-600', light: 'bg-blue-50' },
  'GROUP-2': { bg: 'bg-green-600', text: 'text-green-600', light: 'bg-green-50' },
  'GROUP-3': { bg: 'bg-orange-600', text: 'text-orange-600', light: 'bg-orange-50' },
  'GROUP-4': { bg: 'bg-purple-600', text: 'text-purple-600', light: 'bg-purple-50' },
}

export default function Dashboard() {
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.get('/api/v1/health').then(r => r.data),
  })

  const { data: decisions } = useQuery({
    queryKey: ['decisions'],
    queryFn: () => api.get('/api/v1/decisions').then(r => r.data),
  })

  // Neutral metrics - structural counts only
  const groupCounts = decisions?.decisions?.reduce((acc: Record<string, number>, d: any) => {
    acc[d.group_id] = (acc[d.group_id] || 0) + 1
    return acc
  }, {} as Record<string, number>) || {}

  const hasSupersedes = decisions?.decisions?.filter((d: any) => d.supersedes).length ?? 0

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-gray-600">
          Constitutional governance framework for decision management
        </p>
      </div>

      {/* Constitutional Notice */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl p-6 text-white">
        <h3 className="font-semibold mb-4">Constitutional Notice</h3>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-4 bg-white/10 rounded-lg backdrop-blur">
            <div className="text-2xl font-bold text-red-300">ZERO</div>
            <div className="text-white/80 text-sm">AI Authority</div>
          </div>
          <div className="text-center p-4 bg-white/10 rounded-lg backdrop-blur">
            <div className="text-2xl font-bold text-green-300">HUMAN</div>
            <div className="text-white/80 text-sm">Decision Authority</div>
          </div>
          <div className="text-center p-4 bg-white/10 rounded-lg backdrop-blur">
            <div className="text-2xl font-bold text-yellow-300">ABSOLUTE</div>
            <div className="text-white/80 text-sm">Immutability</div>
          </div>
        </div>
      </div>

      {/* Structural Metrics */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="text-sm text-gray-500">Total Decisions</div>
          <div className="text-3xl font-bold text-gray-900 mt-1">
            {decisions?.total_count ?? 0}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="text-sm text-gray-500">Groups</div>
          <div className="text-3xl font-bold text-indigo-600 mt-1">4</div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="text-sm text-gray-500">Features</div>
          <div className="text-3xl font-bold text-indigo-600 mt-1">16</div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="text-sm text-gray-500">Version Chains</div>
          <div className="text-3xl font-bold text-gray-500 mt-1">
            {hasSupersedes}
          </div>
        </div>
      </div>

      {/* Decision Groups */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Decision Groups</h3>
        <div className="grid grid-cols-2 gap-4">
          {GROUPS.map(groupId => {
            const colors = GROUP_COLORS[groupId]
            const count = groupCounts[groupId] ?? 0
            const groupNum = groupId.split('-')[1]
            const features = FEATURES[groupId] || []

            return (
              <Link
                key={groupId}
                to={`/group/${groupNum}`}
                className="bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium text-white ${colors.bg}`}>
                      Group {groupNum}
                    </span>
                    <h4 className="text-lg font-medium text-gray-900 mt-2">
                      {GROUP_LABELS[groupId]}
                    </h4>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-gray-900">{count}</div>
                    <div className="text-xs text-gray-500">decisions</div>
                  </div>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  {features.slice(0, 4).map(featureId => (
                    <span
                      key={featureId}
                      className={`text-xs px-2 py-1 rounded ${colors.light} ${colors.text}`}
                    >
                      {FEATURE_LABELS[featureId]}
                    </span>
                  ))}
                </div>
              </Link>
            )
          })}
        </div>
      </div>

      {/* Quick Links */}
      <div className="grid grid-cols-2 gap-4">
        <Link
          to="/matrix"
          className="bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow"
        >
          <h3 className="font-semibold text-gray-900">Decision Matrix</h3>
          <p className="text-gray-500 text-sm mt-1">
            4 Groups x 4 Features = 16 Categories
          </p>
        </Link>
        <Link
          to="/validate"
          className="bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow"
        >
          <h3 className="font-semibold text-gray-900">Validator</h3>
          <p className="text-gray-500 text-sm mt-1">
            44 validation rules across 3 levels
          </p>
        </Link>
      </div>

      {/* Service Status */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Service Status</h3>
        <div className="flex items-center space-x-3">
          <span className={`w-3 h-3 rounded-full ${health ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-gray-600">
            {health ? 'Backend API Connected' : 'Backend API Unavailable'}
          </span>
        </div>
      </div>
    </div>
  )
}
