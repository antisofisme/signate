/**
 * Domain Page - Per-domain view with Aspects and Projections tabs
 * Per MANTRA-LAW-001 §3
 */

import { useState, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { clsx } from 'clsx'
import { api } from '../shared/api'
import {
  ASPECTS,
  DOMAIN_LABELS,
  DOMAIN_SCOPES,
  ASPECT_LABELS,
} from '../shared/constants'
import { SkeletonPage } from '../components/ui/skeleton'
import { buildSupersededSet } from '../shared/decisionUtils'

interface Decision {
  decision_id: string
  decision_code: string | null  // Human-readable code: INT-A01-001-v1.0.0
  version: string
  statement: string
  rationale: string
  domain_id: string
  aspect_id: string
  scope: string
  blast_radius: string
  created_at: string
  supersedes: string | null
  related_decisions: string[]
}

const DOMAIN_COLORS: Record<string, { bg: string; text: string; border: string; light: string }> = {
  'INT': { bg: 'bg-blue-600', text: 'text-blue-600', border: 'border-blue-200', light: 'bg-blue-50' },
  'ARCH': { bg: 'bg-green-600', text: 'text-green-600', border: 'border-green-200', light: 'bg-green-50' },
  'CTL': { bg: 'bg-orange-600', text: 'text-orange-600', border: 'border-orange-200', light: 'bg-orange-50' },
  'EVO': { bg: 'bg-purple-600', text: 'text-purple-600', border: 'border-purple-200', light: 'bg-purple-50' },
}

const PATH_TO_DOMAIN: Record<string, string> = {
  'int': 'INT',
  'arch': 'ARCH',
  'ctl': 'CTL',
  'evo': 'EVO',
}

export default function DomainPage() {
  const { domainId: domainParam } = useParams<{ domainId: string }>()
  const domainId = PATH_TO_DOMAIN[domainParam?.toLowerCase() || ''] || 'INT'
  const [activeTab, setActiveTab] = useState<'aspects' | 'projections'>('aspects')

  const colors = DOMAIN_COLORS[domainId] || DOMAIN_COLORS['INT']
  const aspects = ASPECTS[domainId] || []

  const { data, isLoading } = useQuery({
    queryKey: ['decisions'],
    queryFn: () => api.get('/api/v1/decisions').then(r => r.data),
  })

  if (isLoading) {
    return <SkeletonPage />
  }

  const allDecisions: Decision[] = data?.decisions || []
  // Support both old (group_id) and new (domain_id) field names
  const domainDecisions = allDecisions.filter(d => (d as any).group_id === domainId || d.domain_id === domainId)

  // Build superseded set for filtering
  const supersededSet = useMemo(() => {
    return buildSupersededSet(allDecisions as any[])
  }, [allDecisions])

  // Current decisions in this domain
  const currentDomainDecisions = useMemo(() => {
    return domainDecisions.filter(d => !supersededSet.has(d.decision_id))
  }, [domainDecisions, supersededSet])

  // Historical count
  const historicalCount = domainDecisions.length - currentDomainDecisions.length

  // Count CURRENT decisions per aspect
  const currentAspectCounts: Record<string, number> = {}
  const totalAspectCounts: Record<string, number> = {}
  aspects.forEach(a => {
    // Support both old (feature_id) and new (aspect_id) field names
    const aspectDecisions = domainDecisions.filter(d => (d as any).feature_id === a || d.aspect_id === a)
    totalAspectCounts[a] = aspectDecisions.length
    currentAspectCounts[a] = aspectDecisions.filter(d => !supersededSet.has(d.decision_id)).length
  })

  // Cross-domain relationships
  const crossDomainRefs = domainDecisions.filter(d =>
    d.related_decisions?.some(relId => {
      const related = allDecisions.find(r => r.decision_id === relId)
      const relatedDomainId = (related as any)?.group_id || related?.domain_id
      return related && relatedDomainId !== domainId
    })
  )

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="flex items-center space-x-2 text-sm">
        <Link to="/" className="text-gray-500 hover:text-gray-700">Dashboard</Link>
        <span className="text-gray-300">/</span>
        <span className={`px-2 py-0.5 rounded text-xs font-medium ${
          domainId === 'INT' ? 'bg-blue-100 text-blue-800' :
          domainId === 'ARCH' ? 'bg-green-100 text-green-800' :
          domainId === 'CTL' ? 'bg-orange-100 text-orange-800' :
          'bg-purple-100 text-purple-800'
        }`}>
          {DOMAIN_LABELS[domainId]}
        </span>
      </nav>

      {/* Header */}
      <div className={clsx("rounded-lg p-6", colors.light)}>
        <div className="flex items-center gap-4">
          <div className={clsx("w-12 h-12 rounded-lg flex items-center justify-center text-white", colors.bg)}>
            <span className="font-bold text-lg">{domainId}</span>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{DOMAIN_LABELS[domainId]}</h1>
            <p className="text-gray-600">{domainId} - {DOMAIN_SCOPES[domainId]}</p>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-4 gap-4 mt-6">
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-2xl font-bold text-gray-900">{currentDomainDecisions.length}</div>
            <div className="text-sm text-gray-500">Current Decisions</div>
            {historicalCount > 0 && (
              <div className="text-xs text-gray-400">({domainDecisions.length} total)</div>
            )}
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-2xl font-bold text-gray-900">{aspects.length}</div>
            <div className="text-sm text-gray-500">Aspects</div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-2xl font-bold text-gray-900">{historicalCount}</div>
            <div className="text-sm text-gray-500">Historical Versions</div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-2xl font-bold text-gray-900">{crossDomainRefs.length}</div>
            <div className="text-sm text-gray-500">Cross-Domain Refs</div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-4">
          <button
            onClick={() => setActiveTab('aspects')}
            className={clsx(
              "px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors",
              activeTab === 'aspects'
                ? clsx("border-current", colors.text)
                : "border-transparent text-gray-500 hover:text-gray-700"
            )}
          >
            Aspects ({aspects.length})
          </button>
          <button
            onClick={() => setActiveTab('projections')}
            className={clsx(
              "px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors",
              activeTab === 'projections'
                ? clsx("border-current", colors.text)
                : "border-transparent text-gray-500 hover:text-gray-700"
            )}
          >
            Projections
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'aspects' && (
        <div className="grid grid-cols-2 gap-4">
          {aspects.map(aspectId => {
            const currentCount = currentAspectCounts[aspectId]
            const totalCount = totalAspectCounts[aspectId]
            const hasHistorical = totalCount > currentCount
            // Show only current decisions in the preview
            // Support both old (feature_id) and new (aspect_id) field names
            const currentAspectDecisions = domainDecisions
              .filter(d => ((d as any).feature_id === aspectId || d.aspect_id === aspectId) && !supersededSet.has(d.decision_id))

            return (
              <div key={aspectId} className="bg-white rounded-lg border shadow-sm overflow-hidden">
                <div className={clsx("px-4 py-3 border-b", colors.light)}>
                  <div className="flex items-center justify-between">
                    <div>
                      <span className={clsx("font-medium", colors.text)}>{aspectId}</span>
                      <span className="text-gray-600 ml-2">{ASPECT_LABELS[aspectId]}</span>
                    </div>
                    <div className="text-right">
                      <span className="bg-white px-2 py-1 rounded text-sm font-medium text-gray-600">
                        {currentCount} current
                      </span>
                      {hasHistorical && (
                        <span className="text-xs text-gray-400 ml-1">({totalCount} total)</span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="p-4">
                  {currentAspectDecisions.length > 0 ? (
                    <div className="space-y-2">
                      {currentAspectDecisions.slice(0, 3).map(decision => (
                        <Link
                          key={decision.decision_id}
                          to={`/decisions/${decision.decision_id}`}
                          className="block p-3 bg-gray-50 rounded hover:bg-gray-100 transition-colors"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-mono text-xs text-indigo-600 font-medium">
                              {decision.decision_code || decision.decision_id.slice(0, 12) + '...'}
                            </span>
                            <span className="text-xs text-gray-400">v{decision.version}</span>
                          </div>
                          <p className="text-sm text-gray-700 mt-1 line-clamp-2">
                            {decision.statement}
                          </p>
                        </Link>
                      ))}
                      {currentAspectDecisions.length > 3 && (
                        <Link
                          to={`/decisions?domain=${domainId}&aspect=${aspectId}`}
                          className={clsx("block text-center text-sm py-2", colors.text, "hover:underline")}
                        >
                          View all {currentCount} current decisions
                        </Link>
                      )}
                    </div>
                  ) : (
                    <p className="text-gray-400 text-sm text-center py-4">
                      No current decisions for this aspect
                    </p>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {activeTab === 'projections' && (
        <div className="space-y-6">
          {/* Evolution Timeline for this domain */}
          <div className="bg-white rounded-lg border shadow-sm">
            <div className="px-4 py-3 border-b bg-gray-50">
              <h3 className="font-medium text-gray-900">Evolution Timeline</h3>
              <p className="text-sm text-gray-500">Version chains in {DOMAIN_LABELS[domainId]}</p>
            </div>
            <div className="p-4">
              {domainDecisions.filter(d => d.supersedes).length > 0 ? (
                <div className="space-y-3">
                  {domainDecisions.filter(d => d.supersedes).map(decision => {
                    const supersededDecision = allDecisions.find(d => d.decision_id === decision.supersedes)
                    const aspectId = (decision as any).feature_id || decision.aspect_id
                    return (
                      <div key={decision.decision_id} className="flex items-center gap-3 p-3 bg-gray-50 rounded">
                        <Link
                          to={`/decisions/${decision.supersedes}`}
                          className="font-mono text-xs text-gray-500 hover:text-gray-700"
                        >
                          {supersededDecision?.decision_code || decision.supersedes?.slice(0, 8) + '...'}
                        </Link>
                        <span className="text-gray-400">-&gt;</span>
                        <Link
                          to={`/decisions/${decision.decision_id}`}
                          className={clsx("font-mono text-xs", colors.text, "hover:underline")}
                        >
                          {decision.decision_code || decision.decision_id.slice(0, 8) + '...'}
                        </Link>
                        <span className="text-xs text-gray-400 ml-auto">
                          {aspectId}
                        </span>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <p className="text-gray-400 text-sm text-center py-4">
                  No version chains in this domain
                </p>
              )}
            </div>
          </div>

          {/* Cross-Domain References */}
          <div className="bg-white rounded-lg border shadow-sm">
            <div className="px-4 py-3 border-b bg-gray-50">
              <h3 className="font-medium text-gray-900">Cross-Domain References</h3>
              <p className="text-sm text-gray-500">Decisions referencing other domains</p>
            </div>
            <div className="p-4">
              {crossDomainRefs.length > 0 ? (
                <div className="space-y-3">
                  {crossDomainRefs.map(decision => {
                    const aspectId = (decision as any).feature_id || decision.aspect_id
                    return (
                      <div key={decision.decision_id} className="p-3 bg-gray-50 rounded">
                        <div className="flex items-center gap-2">
                          <Link
                            to={`/decisions/${decision.decision_id}`}
                            className={clsx("font-mono text-xs", colors.text, "hover:underline")}
                          >
                            {decision.decision_code || decision.decision_id.slice(0, 12) + '...'}
                          </Link>
                          <span className="text-xs text-gray-400">({aspectId})</span>
                        </div>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {decision.related_decisions?.map(relId => {
                            const related = allDecisions.find(r => r.decision_id === relId)
                            const relatedDomainId = (related as any)?.group_id || related?.domain_id
                            if (!related || relatedDomainId === domainId) return null
                            return (
                              <Link
                                key={relId}
                                to={`/decisions/${relId}`}
                                className="text-xs px-2 py-1 bg-gray-200 rounded hover:bg-gray-300"
                              >
                                {relatedDomainId} - {related.decision_code || relId.slice(0, 8)}
                              </Link>
                            )
                          })}
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <p className="text-gray-400 text-sm text-center py-4">
                  No cross-domain references from this domain
                </p>
              )}
            </div>
          </div>

          {/* Recent Decisions */}
          <div className="bg-white rounded-lg border shadow-sm">
            <div className="px-4 py-3 border-b bg-gray-50">
              <h3 className="font-medium text-gray-900">Recent Decisions</h3>
              <p className="text-sm text-gray-500">Latest decisions in {DOMAIN_LABELS[domainId]}</p>
            </div>
            <div className="p-4">
              {domainDecisions.length > 0 ? (
                <div className="space-y-2">
                  {[...domainDecisions]
                    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
                    .slice(0, 5)
                    .map(decision => {
                      const aspectId = (decision as any).feature_id || decision.aspect_id
                      return (
                        <Link
                          key={decision.decision_id}
                          to={`/decisions/${decision.decision_id}`}
                          className="flex items-center justify-between p-3 bg-gray-50 rounded hover:bg-gray-100 transition-colors"
                        >
                          <div>
                            <span className="font-mono text-xs text-indigo-600 font-medium">
                              {decision.decision_code || decision.decision_id.slice(0, 12) + '...'}
                            </span>
                            <span className="text-xs text-gray-400 ml-2">
                              {aspectId}
                            </span>
                          </div>
                          <span className="text-xs text-gray-400">
                            {new Date(decision.created_at).toLocaleDateString()}
                          </span>
                        </Link>
                      )
                    })}
                </div>
              ) : (
                <p className="text-gray-400 text-sm text-center py-4">
                  No decisions in this domain yet
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Structural Note */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <h4 className="text-sm font-medium text-amber-800 mb-1">Projection Note</h4>
        <p className="text-xs text-amber-700">
          All views are read-only projections. No status, priority, or validity judgment is implied.
          Per MANTRA-L1-PROJECTION-CATALOG-001.
        </p>
      </div>
    </div>
  )
}
