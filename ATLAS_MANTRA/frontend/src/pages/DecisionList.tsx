import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../shared/api'
import { GROUP_LABELS, FEATURE_LABELS } from '../shared/constants'
import { useState, useMemo, useEffect } from 'react'
// Decision type imported via AnnotatedDecision from decisionUtils
import { SkeletonTable } from '../components/ui/skeleton'
import { ScrollTable } from '../components/ui/scroll-table'
import { useDebounce } from '../hooks/useDebounce'
import { InfoTooltip } from '../components/ui/tooltip'
import { annotateDecisions, getDecisionCounts, AnnotatedDecision } from '../shared/decisionUtils'

export default function DecisionList() {
  const [searchParams] = useSearchParams()
  const initialSearch = searchParams.get('search') || ''
  const initialGroup = searchParams.get('group') || ''
  const initialFeature = searchParams.get('feature') || ''

  const [searchQuery, setSearchQuery] = useState(initialSearch)
  const [filterGroup, setFilterGroup] = useState<string>(initialGroup)
  const [filterFeature, setFilterFeature] = useState<string>(initialFeature)
  const [showHistorical, setShowHistorical] = useState(false)

  // Debounce search query for better performance
  const debouncedSearch = useDebounce(searchQuery, 300)

  // Update state when URL params change
  useEffect(() => {
    setSearchQuery(searchParams.get('search') || '')
    setFilterGroup(searchParams.get('group') || '')
    setFilterFeature(searchParams.get('feature') || '')
  }, [searchParams])

  const { data, isLoading } = useQuery({
    queryKey: ['decisions'],
    queryFn: () => api.get('/api/v1/decisions').then(r => r.data),
  })

  // Decision counts for display
  const decisionCounts = useMemo(() => {
    return getDecisionCounts(data?.decisions || [])
  }, [data?.decisions])

  // Annotate decisions with currency info
  const annotatedDecisions = useMemo(() => {
    if (!data?.decisions) return []
    return annotateDecisions(data.decisions)
  }, [data?.decisions])

  // Filter and search decisions
  const filteredDecisions = useMemo(() => {
    if (!annotatedDecisions.length) return []

    return annotatedDecisions.filter((decision: AnnotatedDecision) => {
      // Historical filter - hide superseded unless toggle is on
      if (!showHistorical && !decision._isCurrent) return false

      // Group filter
      if (filterGroup && decision.group_id !== filterGroup) return false

      // Feature filter
      if (filterFeature && decision.feature_id !== filterFeature) return false

      // Search query (using debounced value for filtering)
      if (debouncedSearch) {
        const query = debouncedSearch.toLowerCase()
        const searchFields = [
          decision.decision_code,
          decision.decision_id,
          decision.statement,
          decision.rationale,
          GROUP_LABELS[decision.group_id],
          FEATURE_LABELS[decision.feature_id],
          decision.version,
        ].filter(Boolean)

        return searchFields.some(field =>
          field?.toLowerCase().includes(query)
        )
      }

      return true
    })
  }, [annotatedDecisions, debouncedSearch, filterGroup, filterFeature, showHistorical])

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <div className="h-8 w-32 bg-gray-200 rounded animate-pulse mb-2" />
          <div className="h-4 w-48 bg-gray-200 rounded animate-pulse" />
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-4">
          <div className="flex gap-4">
            <div className="h-10 flex-1 bg-gray-200 rounded animate-pulse" />
            <div className="h-10 w-32 bg-gray-200 rounded animate-pulse" />
            <div className="h-10 w-32 bg-gray-200 rounded animate-pulse" />
          </div>
        </div>
        <SkeletonTable rows={8} />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Decisions</h1>
          <p className="mt-1 text-gray-600">
            {decisionCounts.current} current decisions
            {decisionCounts.superseded > 0 && (
              <span className="text-gray-400 ml-1">
                ({decisionCounts.total} total incl. {decisionCounts.superseded} historical)
              </span>
            )}
            {filteredDecisions.length !== (showHistorical ? decisionCounts.total : decisionCounts.current) && (
              <span className="text-indigo-600 ml-2">
                (showing {filteredDecisions.length} filtered)
              </span>
            )}
          </p>
        </div>
      </div>

      {/* Search and Filter Bar */}
      <div className="bg-white rounded-lg shadow-sm border p-4">
        <div className="flex flex-wrap gap-4 items-center">
          {/* Search Input */}
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <input
                type="text"
                placeholder="Search by code, statement, or rationale..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <svg
                className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
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
            </div>
          </div>

          {/* Group Filter */}
          <select
            value={filterGroup}
            onChange={(e) => setFilterGroup(e.target.value)}
            className="px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Groups</option>
            <option value="INT">INT: Intent</option>
            <option value="ARCH">ARCH: Architecture</option>
            <option value="CTL">CTL: Control</option>
            <option value="EVO">EVO: Evolution</option>
          </select>

          {/* Feature Filter */}
          <select
            value={filterFeature}
            onChange={(e) => setFilterFeature(e.target.value)}
            className="px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Features</option>
            {Array.from({ length: 16 }, (_, i) => {
              const featureId = `F${String(i + 1).padStart(2, '0')}`
              return (
                <option key={featureId} value={featureId}>
                  {featureId}: {FEATURE_LABELS[featureId] || 'Unknown'}
                </option>
              )
            })}
          </select>

          {/* Historical Toggle */}
          {decisionCounts.superseded > 0 && (
            <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
              <input
                type="checkbox"
                checked={showHistorical}
                onChange={(e) => setShowHistorical(e.target.checked)}
                className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
              Show historical ({decisionCounts.superseded})
            </label>
          )}

          {/* Clear Filters */}
          {(searchQuery || filterGroup || filterFeature) && (
            <button
              onClick={() => {
                setSearchQuery('')
                setFilterGroup('')
                setFilterFeature('')
              }}
              className="px-3 py-2 text-gray-500 hover:text-gray-700"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
        <ScrollTable>
        <table className="w-full min-w-[800px]">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Code</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Group</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Feature</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Statement</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">
                <span className="flex items-center gap-1">
                  Blast Radius
                  <InfoTooltip content="Impact scope: CRITICAL (org-wide), HIGH (multi-team), MEDIUM (team), LOW (component)" />
                </span>
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">
                <span className="flex items-center gap-1">
                  Supersedes
                  <InfoTooltip content="Decision that this one replaces (version chain)" />
                </span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filteredDecisions.map((decision: AnnotatedDecision) => (
              <tr
                key={decision.decision_id}
                className={`hover:bg-gray-50 transition-colors ${!decision._isCurrent ? 'opacity-60 bg-gray-50' : ''}`}
              >
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <Link
                      to={`/decisions/${decision.decision_id}`}
                      className="text-indigo-600 hover:text-indigo-500 font-mono text-sm font-semibold"
                    >
                      {decision.decision_code || decision.decision_id.slice(0, 12) + '...'}
                    </Link>
                    {!decision._isCurrent && decision._supersededBy && (
                      <Link
                        to={`/decisions/${decision._supersededBy}`}
                        className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-gray-200 text-gray-600 text-xs rounded hover:bg-gray-300 transition-colors"
                        title={`Superseded by ${decision._supersededByCode || decision._supersededBy.slice(0, 8)}`}
                      >
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                        </svg>
                        Superseded
                      </Link>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3 text-sm">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                    decision.group_id === 'INT' ? 'bg-blue-100 text-blue-800' :
                    decision.group_id === 'ARCH' ? 'bg-green-100 text-green-800' :
                    decision.group_id === 'CTL' ? 'bg-purple-100 text-purple-800' :
                    'bg-orange-100 text-orange-800'
                  }`}>
                    {GROUP_LABELS[decision.group_id]}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm">
                  <span className="text-gray-700 font-medium">{decision.feature_id}</span>
                  <span className="text-xs text-gray-500 block">{FEATURE_LABELS[decision.feature_id]}</span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-600 max-w-md">
                  <div className="truncate" title={decision.statement}>
                    {decision.statement}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    decision.blast_radius === 'CRITICAL' ? 'bg-red-100 text-red-800' :
                    decision.blast_radius === 'HIGH' ? 'bg-orange-100 text-orange-800' :
                    decision.blast_radius === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {decision.blast_radius}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm">
                  {decision.supersedes ? (
                    <Link
                      to={`/decisions/${decision.supersedes}`}
                      className="text-orange-600 hover:text-orange-500 font-mono text-xs"
                    >
                      {decision.supersedes.slice(0, 8)}...
                    </Link>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
              </tr>
            ))}
            {filteredDecisions.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                  {debouncedSearch || filterGroup || filterFeature
                    ? 'No decisions match your filters'
                    : 'No decisions found'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
        </ScrollTable>
      </div>
    </div>
  )
}
