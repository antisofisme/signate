/**
 * Semantic Search Page
 *
 * Features:
 * - Natural language search for decisions
 * - Filter by group, feature, tags
 * - Check alignment for new proposals
 * - Search result highlighting
 */

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { clsx } from 'clsx'
import { Link } from 'react-router-dom'
import { api } from '../shared/api'
import {
  GROUPS,
  GROUP_LABELS,
  GROUP_COLORS,
  FEATURES,
  FEATURE_LABELS,
  AREA_TAGS,
  TAG_COLORS,
} from '../shared/constants'

// Types
interface SearchHit {
  decision_id: string
  decision_code: string
  statement: string
  rationale: string
  score: number
  group_id: string
  feature_id: string
  version: string
  tags: string[]
  matched_fields: string[]
}

interface SemanticSearchResponse {
  status: string
  hits: SearchHit[]
  total_count: number
  query: string
  filters_applied: Record<string, any>
  execution_time_ms: number
  cached: boolean
  error_message?: string
}

interface AlignmentResponse {
  status: string
  aligned_with: SearchHit[]
  conflicts_with: SearchHit[]
  related_decisions: SearchHit[]
  recommendations: string[]
  execution_time_ms: number
  error_message?: string
}

// Search mode tabs
type SearchMode = 'search' | 'alignment'

export default function SemanticSearch() {
  const [mode, setMode] = useState<SearchMode>('search')
  const [query, setQuery] = useState('')
  const [statement, setStatement] = useState('')
  const [rationale, setRationale] = useState('')
  const [groupFilter, setGroupFilter] = useState('')
  const [featureFilter, setFeatureFilter] = useState('')
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [minScore, setMinScore] = useState(0.5)

  // Search mutation
  const searchMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post<SemanticSearchResponse>('/api/v1/search/semantic', {
        query,
        limit: 20,
        min_score: minScore,
        group_id: groupFilter || undefined,
        feature_id: featureFilter || undefined,
        tags: selectedTags.length > 0 ? selectedTags : undefined,
      })
      return response.data
    },
  })

  // Alignment check mutation
  const alignmentMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post<AlignmentResponse>('/api/v1/search/check-alignment', {
        statement,
        rationale,
        group_id: groupFilter || undefined,
        min_score: minScore,
      })
      return response.data
    },
  })

  const handleSearch = () => {
    if (mode === 'search' && query.trim()) {
      searchMutation.mutate()
    } else if (mode === 'alignment' && statement.trim()) {
      alignmentMutation.mutate()
    }
  }

  const toggleTag = (tag: string) => {
    setSelectedTags(prev =>
      prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag]
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Semantic Search</h1>
        <p className="mt-2 text-gray-600">
          Find decisions using natural language or check alignment for new proposals
        </p>
      </div>

      {/* Mode Tabs */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="flex border-b">
          <button
            onClick={() => setMode('search')}
            className={clsx(
              'flex-1 px-4 py-3 text-sm font-medium transition-colors',
              mode === 'search'
                ? 'text-indigo-600 border-b-2 border-indigo-600 bg-indigo-50'
                : 'text-gray-500 hover:text-gray-700'
            )}
          >
            <span className="mr-2">🔍</span> Search Decisions
          </button>
          <button
            onClick={() => setMode('alignment')}
            className={clsx(
              'flex-1 px-4 py-3 text-sm font-medium transition-colors',
              mode === 'alignment'
                ? 'text-indigo-600 border-b-2 border-indigo-600 bg-indigo-50'
                : 'text-gray-500 hover:text-gray-700'
            )}
          >
            <span className="mr-2">🎯</span> Check Alignment
          </button>
        </div>

        <div className="p-6">
          {/* Search Mode */}
          {mode === 'search' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Search Query
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                    placeholder="e.g., database technology, authentication method, API design..."
                    className="flex-1 px-4 py-3 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  <button
                    onClick={handleSearch}
                    disabled={!query.trim() || searchMutation.isPending}
                    className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                  >
                    {searchMutation.isPending ? 'Searching...' : 'Search'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Alignment Mode */}
          {mode === 'alignment' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Proposed Statement
                </label>
                <textarea
                  value={statement}
                  onChange={(e) => setStatement(e.target.value)}
                  placeholder="Enter your proposed decision statement..."
                  rows={3}
                  className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Rationale (optional)
                </label>
                <textarea
                  value={rationale}
                  onChange={(e) => setRationale(e.target.value)}
                  placeholder="Why this decision? What problem does it solve?"
                  rows={2}
                  className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <button
                onClick={handleSearch}
                disabled={!statement.trim() || alignmentMutation.isPending}
                className="w-full px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-300"
              >
                {alignmentMutation.isPending ? 'Checking...' : 'Check Alignment'}
              </button>
            </div>
          )}

          {/* Filters */}
          <div className="mt-6 pt-6 border-t">
            <h4 className="text-sm font-medium text-gray-700 mb-3">Filters</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Group Filter */}
              <div>
                <label className="block text-xs text-gray-500 mb-1">Group</label>
                <select
                  value={groupFilter}
                  onChange={(e) => {
                    setGroupFilter(e.target.value)
                    setFeatureFilter('')
                  }}
                  className="w-full px-3 py-2 border rounded text-sm"
                >
                  <option value="">All Groups</option>
                  {GROUPS.map(g => (
                    <option key={g} value={g}>{g} - {GROUP_LABELS[g]}</option>
                  ))}
                </select>
              </div>

              {/* Feature Filter */}
              <div>
                <label className="block text-xs text-gray-500 mb-1">Feature</label>
                <select
                  value={featureFilter}
                  onChange={(e) => setFeatureFilter(e.target.value)}
                  disabled={!groupFilter}
                  className="w-full px-3 py-2 border rounded text-sm disabled:bg-gray-100"
                >
                  <option value="">All Features</option>
                  {groupFilter && FEATURES[groupFilter]?.map(f => (
                    <option key={f} value={f}>{f} - {FEATURE_LABELS[f]}</option>
                  ))}
                </select>
              </div>

              {/* Min Score */}
              <div>
                <label className="block text-xs text-gray-500 mb-1">
                  Min Score: {(minScore * 100).toFixed(0)}%
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={minScore}
                  onChange={(e) => setMinScore(parseFloat(e.target.value))}
                  className="w-full"
                />
              </div>
            </div>

            {/* Tag Filters */}
            {mode === 'search' && (
              <div className="mt-4">
                <label className="block text-xs text-gray-500 mb-2">Tags</label>
                <div className="flex flex-wrap gap-2">
                  {AREA_TAGS.map(tag => (
                    <button
                      key={tag}
                      onClick={() => toggleTag(tag)}
                      className={clsx(
                        'px-3 py-1 text-xs rounded-full transition-all',
                        selectedTags.includes(tag)
                          ? TAG_COLORS[tag] || 'bg-indigo-100 text-indigo-700'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      )}
                    >
                      {tag}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Search Results */}
      {mode === 'search' && searchMutation.data && (
        <SearchResults data={searchMutation.data} />
      )}

      {/* Alignment Results */}
      {mode === 'alignment' && alignmentMutation.data && (
        <AlignmentResults data={alignmentMutation.data} />
      )}

      {/* Errors */}
      {(searchMutation.error || alignmentMutation.error) && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700">
            {searchMutation.error?.message || alignmentMutation.error?.message || 'Search failed'}
          </p>
        </div>
      )}
    </div>
  )
}

// =============================================================================
// Search Results Component
// =============================================================================
function SearchResults({ data }: { data: SemanticSearchResponse }) {
  if (data.status === 'ERROR') {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-700">{data.error_message}</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-900">
          Search Results ({data.total_count})
        </h3>
        <div className="flex items-center gap-3 text-xs text-gray-500">
          <span>{data.execution_time_ms.toFixed(0)}ms</span>
          {data.cached && <span className="text-green-600">Cached</span>}
        </div>
      </div>

      {data.hits.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No decisions found matching "{data.query}"
        </div>
      ) : (
        <div className="space-y-3">
          {data.hits.map(hit => (
            <SearchHitCard key={hit.decision_id} hit={hit} />
          ))}
        </div>
      )}
    </div>
  )
}

// =============================================================================
// Alignment Results Component
// =============================================================================
function AlignmentResults({ data }: { data: AlignmentResponse }) {
  if (data.status === 'ERROR') {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-700">{data.error_message}</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Conflicts */}
      {data.conflicts_with.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h3 className="font-semibold text-red-800 mb-3 flex items-center gap-2">
            <span>⚠️</span> Potential Conflicts ({data.conflicts_with.length})
          </h3>
          <div className="space-y-2">
            {data.conflicts_with.map(hit => (
              <SearchHitCard key={hit.decision_id} hit={hit} variant="conflict" />
            ))}
          </div>
        </div>
      )}

      {/* Aligned */}
      {data.aligned_with.length > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <h3 className="font-semibold text-green-800 mb-3 flex items-center gap-2">
            <span>✅</span> Aligned With ({data.aligned_with.length})
          </h3>
          <div className="space-y-2">
            {data.aligned_with.map(hit => (
              <SearchHitCard key={hit.decision_id} hit={hit} variant="aligned" />
            ))}
          </div>
        </div>
      )}

      {/* Related */}
      {data.related_decisions.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="font-semibold text-blue-800 mb-3 flex items-center gap-2">
            <span>🔗</span> Related Decisions ({data.related_decisions.length})
          </h3>
          <div className="space-y-2">
            {data.related_decisions.map(hit => (
              <SearchHitCard key={hit.decision_id} hit={hit} variant="related" />
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {data.recommendations.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-6">
          <h3 className="font-semibold text-amber-800 mb-3 flex items-center gap-2">
            <span>💡</span> Recommendations
          </h3>
          <ul className="space-y-2">
            {data.recommendations.map((rec, idx) => (
              <li key={idx} className="text-sm text-amber-700 flex items-start gap-2">
                <span>•</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* All Clear */}
      {data.conflicts_with.length === 0 && data.aligned_with.length === 0 && data.related_decisions.length === 0 && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
          <span className="text-3xl">✅</span>
          <p className="text-green-700 font-medium mt-2">No conflicts or similar decisions found</p>
          <p className="text-sm text-green-600">Your proposal appears to be unique</p>
        </div>
      )}

      {/* Execution time */}
      <div className="text-xs text-gray-500 text-right">
        Checked in {data.execution_time_ms.toFixed(0)}ms
      </div>
    </div>
  )
}

// =============================================================================
// Search Hit Card Component
// =============================================================================
function SearchHitCard({
  hit,
  variant = 'default',
}: {
  hit: SearchHit
  variant?: 'default' | 'conflict' | 'aligned' | 'related'
}) {
  const borderColors = {
    default: 'border-l-indigo-500',
    conflict: 'border-l-red-500',
    aligned: 'border-l-green-500',
    related: 'border-l-blue-500',
  }

  return (
    <div className={clsx(
      'bg-white rounded-lg border-l-4 p-4 shadow-sm',
      borderColors[variant]
    )}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          {/* Header */}
          <div className="flex items-center gap-2 mb-2">
            <span
              className="px-2 py-0.5 text-xs rounded text-white"
              style={{ backgroundColor: GROUP_COLORS[hit.group_id] || '#6B7280' }}
            >
              {hit.group_id}
            </span>
            <span className="font-mono text-sm text-gray-700">
              {hit.decision_code || hit.decision_id.slice(0, 8)}
            </span>
            <span className="text-xs text-gray-400">v{hit.version}</span>
          </div>

          {/* Statement */}
          <p className="text-sm text-gray-900 font-medium mb-1">{hit.statement}</p>

          {/* Rationale preview */}
          <p className="text-xs text-gray-500 line-clamp-2">{hit.rationale}</p>

          {/* Tags */}
          {hit.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {hit.tags.map(tag => (
                <span
                  key={tag}
                  className={clsx('px-2 py-0.5 text-xs rounded', TAG_COLORS[tag] || 'bg-gray-100 text-gray-600')}
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Score */}
        <div className="ml-4 text-right">
          <div className={clsx(
            'text-lg font-bold',
            hit.score >= 0.8 ? 'text-green-600' :
            hit.score >= 0.6 ? 'text-amber-600' : 'text-gray-500'
          )}>
            {(hit.score * 100).toFixed(0)}%
          </div>
          <Link
            to={`/decisions/${hit.decision_id}`}
            className="text-xs text-indigo-600 hover:text-indigo-500"
          >
            View →
          </Link>
        </div>
      </div>
    </div>
  )
}
