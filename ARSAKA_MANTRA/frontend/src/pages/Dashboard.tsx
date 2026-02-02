import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { useState, useMemo } from 'react'
import { api, Decision } from '../shared/api'
import { DOMAINS, DOMAIN_LABELS, ASPECTS, ASPECT_LABELS } from '../shared/constants'
import { getDecisionCounts, getCurrentCountsByGroup } from '../shared/decisionUtils'
// Skeleton components available via ../components/ui/skeleton when needed

const DOMAIN_COLORS: Record<string, { bg: string; text: string; light: string }> = {
  'INT': { bg: 'bg-blue-600', text: 'text-blue-600', light: 'bg-blue-50' },
  'ARCH': { bg: 'bg-green-600', text: 'text-green-600', light: 'bg-green-50' },
  'CTL': { bg: 'bg-orange-600', text: 'text-orange-600', light: 'bg-orange-50' },
  'EVO': { bg: 'bg-purple-600', text: 'text-purple-600', light: 'bg-purple-50' },
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')
  const [showResults, setShowResults] = useState(false)

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.get('/api/v1/health').then(r => r.data),
  })

  const { data: decisions } = useQuery({
    queryKey: ['decisions'],
    queryFn: () => api.get('/api/v1/decisions').then(r => r.data),
  })

  const { data: pendingApprovals } = useQuery({
    queryKey: ['pending-approvals'],
    queryFn: () => api.get('/api/v1/approvals/pending').then(r => r.data).catch(() => ({ approvals: [] })),
  })

  const { data: searchStats } = useQuery({
    queryKey: ['search-stats'],
    queryFn: () => api.get('/api/v1/search/stats').then(r => r.data).catch(() => null),
  })

  // Global search - filter decisions by code, statement, or rationale
  const searchResults = useMemo(() => {
    if (!searchQuery.trim() || !decisions?.decisions) return []
    const query = searchQuery.toLowerCase()
    return (decisions.decisions as Decision[])
      .filter(d => {
        const domainId = (d as any).domain_id || (d as any).group_id
        const aspectId = (d as any).aspect_id || (d as any).feature_id
        return (
          d.decision_code?.toLowerCase().includes(query) ||
          d.decision_id.toLowerCase().includes(query) ||
          d.statement.toLowerCase().includes(query) ||
          d.rationale?.toLowerCase().includes(query) ||
          DOMAIN_LABELS[domainId]?.toLowerCase().includes(query) ||
          ASPECT_LABELS[aspectId]?.toLowerCase().includes(query)
        )
      })
      .slice(0, 8) // Limit results
  }, [searchQuery, decisions?.decisions])

  // Decision counts - current vs total
  const decisionCounts = useMemo(() => {
    return getDecisionCounts(decisions?.decisions || [])
  }, [decisions?.decisions])

  // Domain counts for CURRENT decisions only
  const currentDomainCounts = useMemo(() => {
    return getCurrentCountsByGroup(decisions?.decisions || [])
  }, [decisions?.decisions])

  // Total domain counts (for comparison)
  const totalDomainCounts = decisions?.decisions?.reduce((acc: Record<string, number>, d: any) => {
    const domainId = d.domain_id || d.group_id
    acc[domainId] = (acc[domainId] || 0) + 1
    return acc
  }, {} as Record<string, number>) || {}

  const handleSearchSelect = (decisionId: string) => {
    setSearchQuery('')
    setShowResults(false)
    navigate(`/decisions/${decisionId}`)
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-gray-600">
          Constitutional governance framework for decision management
        </p>
      </div>

      {/* Global Search */}
      <div className="relative">
        <div className="relative">
          <input
            type="text"
            placeholder="Search decisions by code (INT-F01-...), statement, or rationale..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value)
              setShowResults(e.target.value.length > 0)
            }}
            onFocus={() => searchQuery.length > 0 && setShowResults(true)}
            onBlur={() => setTimeout(() => setShowResults(false), 200)}
            className="w-full pl-12 pr-4 py-3 bg-white border border-gray-200 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-900 placeholder-gray-400"
          />
          <svg
            className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          {searchQuery && (
            <button
              onClick={() => {
                setSearchQuery('')
                setShowResults(false)
              }}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>

        {/* Search Results Dropdown */}
        {showResults && searchResults.length > 0 && (
          <div className="absolute z-50 w-full mt-2 bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
            <div className="py-2">
              {searchResults.map((decision: Decision) => {
                const domainId = (decision as any).domain_id || (decision as any).group_id
                const aspectId = (decision as any).aspect_id || (decision as any).feature_id
                return (
                  <button
                    key={decision.decision_id}
                    onClick={() => handleSearchSelect(decision.decision_id)}
                    className="w-full px-4 py-3 text-left hover:bg-gray-50 transition-colors border-b border-gray-100 last:border-b-0"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-sm text-indigo-600 font-semibold">
                        {decision.decision_code || decision.decision_id.slice(0, 12) + '...'}
                      </span>
                      <span className={`px-2 py-0.5 rounded text-xs ${
                        domainId === 'INT' ? 'bg-blue-100 text-blue-700' :
                        domainId === 'ARCH' ? 'bg-green-100 text-green-700' :
                        domainId === 'CTL' ? 'bg-orange-100 text-orange-700' :
                        'bg-purple-100 text-purple-700'
                      }`}>
                        {DOMAIN_LABELS[domainId]}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1 truncate">
                      {decision.statement}
                    </p>
                    <div className="text-xs text-gray-400 mt-1">
                      {ASPECT_LABELS[aspectId]} - v{decision.version}
                    </div>
                  </button>
                )
              })}
            </div>
            <div className="px-4 py-2 bg-gray-50 border-t border-gray-200">
              <Link
                to={`/decisions?search=${encodeURIComponent(searchQuery)}`}
                className="text-sm text-indigo-600 hover:text-indigo-500"
                onClick={() => setShowResults(false)}
              >
                View all results
              </Link>
            </div>
          </div>
        )}

        {showResults && searchQuery && searchResults.length === 0 && (
          <div className="absolute z-50 w-full mt-2 bg-white rounded-xl shadow-lg border border-gray-200 p-6 text-center">
            <div className="text-gray-400 mb-2">
              <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-gray-500">No decisions found for "{searchQuery}"</p>
            <p className="text-sm text-gray-400 mt-1">Try searching by code, statement, or domain name</p>
          </div>
        )}
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
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="text-sm text-gray-500">Current Decisions</div>
          <div className="text-3xl font-bold text-gray-900 mt-1">
            {decisionCounts.current}
          </div>
          {decisionCounts.superseded > 0 && (
            <div className="text-xs text-gray-400 mt-1">
              {decisionCounts.total} total ({decisionCounts.superseded} historical)
            </div>
          )}
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="text-sm text-gray-500">Domains</div>
          <div className="text-3xl font-bold text-indigo-600 mt-1">4</div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="text-sm text-gray-500">Aspects</div>
          <div className="text-3xl font-bold text-indigo-600 mt-1">16</div>
        </div>
        <Link
          to="/timeline"
          className="bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow"
        >
          <div className="text-sm text-gray-500">Historical Versions</div>
          <div className="text-3xl font-bold text-gray-500 mt-1">
            {decisionCounts.superseded}
          </div>
        </Link>
        <Link
          to="/approvals"
          className="bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow"
        >
          <div className="text-sm text-gray-500">Pending Approvals</div>
          <div className={`text-3xl font-bold mt-1 ${
            (pendingApprovals?.approvals?.length ?? 0) > 0 ? 'text-amber-600' : 'text-gray-400'
          }`}>
            {pendingApprovals?.approvals?.length ?? 0}
          </div>
        </Link>
      </div>

      {/* Decision Domains */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Decision Domains</h3>
        <div className="grid grid-cols-2 gap-4">
          {DOMAINS.map(domainId => {
            const colors = DOMAIN_COLORS[domainId]
            const currentCount = currentDomainCounts[domainId] ?? 0
            const totalCount = totalDomainCounts[domainId] ?? 0
            const hasHistorical = totalCount > currentCount
            const aspects = ASPECTS[domainId] || []

            return (
              <Link
                key={domainId}
                to={`/domain/${domainId.toLowerCase()}`}
                className="bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium text-white ${colors.bg}`}>
                      {domainId}
                    </span>
                    <h4 className="text-lg font-medium text-gray-900 mt-2">
                      {DOMAIN_LABELS[domainId]}
                    </h4>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-gray-900">{currentCount}</div>
                    <div className="text-xs text-gray-500">current</div>
                    {hasHistorical && (
                      <div className="text-xs text-gray-400">({totalCount} total)</div>
                    )}
                  </div>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  {aspects.slice(0, 4).map(aspectId => (
                    <span
                      key={aspectId}
                      className={`text-xs px-2 py-1 rounded ${colors.light} ${colors.text}`}
                    >
                      {ASPECT_LABELS[aspectId]}
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
            4 Domains x 4 Aspects = 16 Categories
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
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="flex items-center space-x-3">
            <span className={`w-3 h-3 rounded-full ${health ? 'bg-green-500' : 'bg-red-500'}`} />
            <div>
              <div className="text-sm font-medium text-gray-700">Backend API</div>
              <div className="text-xs text-gray-500">{health ? 'Connected' : 'Unavailable'}</div>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <span className={`w-3 h-3 rounded-full ${health?.mics_enabled ? 'bg-green-500' : 'bg-gray-300'}`} />
            <div>
              <div className="text-sm font-medium text-gray-700">MICS</div>
              <div className="text-xs text-gray-500">{health?.mics_enabled ? 'Active' : 'Disabled'}</div>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <span className={`w-3 h-3 rounded-full ${searchStats?.qdrant_status === 'connected' ? 'bg-green-500' : 'bg-amber-500'}`} />
            <div>
              <div className="text-sm font-medium text-gray-700">Search Index</div>
              <div className="text-xs text-gray-500">
                {searchStats?.total_indexed ?? 0} indexed
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <span className={`w-3 h-3 rounded-full ${health?.validation_rules ? 'bg-green-500' : 'bg-amber-500'}`} />
            <div>
              <div className="text-sm font-medium text-gray-700">Validation</div>
              <div className="text-xs text-gray-500">{health?.validation_rules ?? 44} rules</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
