/**
 * Group Page - Per-group view with Features and Projections tabs
 * Per MANTRA-LAW-001 §3
 */

import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { clsx } from 'clsx'
import { api } from '../shared/api'
import {
  FEATURES,
  GROUP_LABELS,
  GROUP_SCOPES,
  FEATURE_LABELS,
} from '../shared/constants'

interface Decision {
  decision_id: string
  decision_code: string | null  // Human-readable code: INT-F01-001-v1.0.0
  version: string
  statement: string
  rationale: string
  group_id: string
  feature_id: string
  scope: string
  blast_radius: string
  created_at: string
  supersedes: string | null
  related_decisions: string[]
}

const GROUP_COLORS: Record<string, { bg: string; text: string; border: string; light: string }> = {
  'INT': { bg: 'bg-blue-600', text: 'text-blue-600', border: 'border-blue-200', light: 'bg-blue-50' },
  'ARCH': { bg: 'bg-green-600', text: 'text-green-600', border: 'border-green-200', light: 'bg-green-50' },
  'CTL': { bg: 'bg-orange-600', text: 'text-orange-600', border: 'border-orange-200', light: 'bg-orange-50' },
  'EVO': { bg: 'bg-purple-600', text: 'text-purple-600', border: 'border-purple-200', light: 'bg-purple-50' },
}

const PATH_TO_GROUP: Record<string, string> = {
  'int': 'INT',
  'arch': 'ARCH',
  'ctl': 'CTL',
  'evo': 'EVO',
}

export default function GroupPage() {
  const { groupNum } = useParams<{ groupNum: string }>()
  const groupId = PATH_TO_GROUP[groupNum?.toLowerCase() || ''] || 'INT'
  const [activeTab, setActiveTab] = useState<'features' | 'projections'>('features')

  const colors = GROUP_COLORS[groupId] || GROUP_COLORS['INT']
  const features = FEATURES[groupId] || []

  const { data } = useQuery({
    queryKey: ['decisions'],
    queryFn: () => api.get('/api/v1/decisions').then(r => r.data),
  })

  const allDecisions: Decision[] = data?.decisions || []
  const groupDecisions = allDecisions.filter(d => d.group_id === groupId)

  // Count decisions per feature
  const featureCounts: Record<string, number> = {}
  features.forEach(f => {
    featureCounts[f] = groupDecisions.filter(d => d.feature_id === f).length
  })

  // Find version chains in this group
  const supersededIds = new Set(groupDecisions.map(d => d.supersedes).filter(Boolean))
  const chainHeads = groupDecisions.filter(d => !supersededIds.has(d.decision_id))
  const chainsCount = chainHeads.filter(d => d.supersedes).length

  // Cross-group relationships
  const crossGroupRefs = groupDecisions.filter(d =>
    d.related_decisions?.some(relId => {
      const related = allDecisions.find(r => r.decision_id === relId)
      return related && related.group_id !== groupId
    })
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className={clsx("rounded-lg p-6", colors.light)}>
        <div className="flex items-center gap-4">
          <div className={clsx("w-12 h-12 rounded-lg flex items-center justify-center text-white", colors.bg)}>
            <span className="font-bold text-lg">{groupId}</span>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{GROUP_LABELS[groupId]}</h1>
            <p className="text-gray-600">{groupId} • {GROUP_SCOPES[groupId]}</p>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-4 gap-4 mt-6">
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-2xl font-bold text-gray-900">{groupDecisions.length}</div>
            <div className="text-sm text-gray-500">Total Decisions</div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-2xl font-bold text-gray-900">{features.length}</div>
            <div className="text-sm text-gray-500">Features</div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-2xl font-bold text-gray-900">{chainsCount}</div>
            <div className="text-sm text-gray-500">Version Chains</div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-2xl font-bold text-gray-900">{crossGroupRefs.length}</div>
            <div className="text-sm text-gray-500">Cross-Group Refs</div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-4">
          <button
            onClick={() => setActiveTab('features')}
            className={clsx(
              "px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors",
              activeTab === 'features'
                ? clsx("border-current", colors.text)
                : "border-transparent text-gray-500 hover:text-gray-700"
            )}
          >
            Features ({features.length})
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
      {activeTab === 'features' && (
        <div className="grid grid-cols-2 gap-4">
          {features.map(featureId => {
            const count = featureCounts[featureId]
            const featureDecisions = groupDecisions.filter(d => d.feature_id === featureId)

            return (
              <div key={featureId} className="bg-white rounded-lg border shadow-sm overflow-hidden">
                <div className={clsx("px-4 py-3 border-b", colors.light)}>
                  <div className="flex items-center justify-between">
                    <div>
                      <span className={clsx("font-medium", colors.text)}>{featureId}</span>
                      <span className="text-gray-600 ml-2">{FEATURE_LABELS[featureId]}</span>
                    </div>
                    <span className="bg-white px-2 py-1 rounded text-sm font-medium text-gray-600">
                      {count} {count === 1 ? 'decision' : 'decisions'}
                    </span>
                  </div>
                </div>
                <div className="p-4">
                  {featureDecisions.length > 0 ? (
                    <div className="space-y-2">
                      {featureDecisions.slice(0, 3).map(decision => (
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
                      {featureDecisions.length > 3 && (
                        <Link
                          to={`/decisions?group=${groupId}&feature=${featureId}`}
                          className={clsx("block text-center text-sm py-2", colors.text, "hover:underline")}
                        >
                          View all {featureDecisions.length} decisions →
                        </Link>
                      )}
                    </div>
                  ) : (
                    <p className="text-gray-400 text-sm text-center py-4">
                      No decisions for this feature yet
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
          {/* Evolution Timeline for this group */}
          <div className="bg-white rounded-lg border shadow-sm">
            <div className="px-4 py-3 border-b bg-gray-50">
              <h3 className="font-medium text-gray-900">Evolution Timeline</h3>
              <p className="text-sm text-gray-500">Version chains in {GROUP_LABELS[groupId]}</p>
            </div>
            <div className="p-4">
              {groupDecisions.filter(d => d.supersedes).length > 0 ? (
                <div className="space-y-3">
                  {groupDecisions.filter(d => d.supersedes).map(decision => {
                    const supersededDecision = allDecisions.find(d => d.decision_id === decision.supersedes)
                    return (
                      <div key={decision.decision_id} className="flex items-center gap-3 p-3 bg-gray-50 rounded">
                        <Link
                          to={`/decisions/${decision.supersedes}`}
                          className="font-mono text-xs text-gray-500 hover:text-gray-700"
                        >
                          {supersededDecision?.decision_code || decision.supersedes?.slice(0, 8) + '...'}
                        </Link>
                        <span className="text-gray-400">→</span>
                        <Link
                          to={`/decisions/${decision.decision_id}`}
                          className={clsx("font-mono text-xs", colors.text, "hover:underline")}
                        >
                          {decision.decision_code || decision.decision_id.slice(0, 8) + '...'}
                        </Link>
                        <span className="text-xs text-gray-400 ml-auto">
                          {decision.feature_id}
                        </span>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <p className="text-gray-400 text-sm text-center py-4">
                  No version chains in this group
                </p>
              )}
            </div>
          </div>

          {/* Cross-Group References */}
          <div className="bg-white rounded-lg border shadow-sm">
            <div className="px-4 py-3 border-b bg-gray-50">
              <h3 className="font-medium text-gray-900">Cross-Group References</h3>
              <p className="text-sm text-gray-500">Decisions referencing other groups</p>
            </div>
            <div className="p-4">
              {crossGroupRefs.length > 0 ? (
                <div className="space-y-3">
                  {crossGroupRefs.map(decision => (
                    <div key={decision.decision_id} className="p-3 bg-gray-50 rounded">
                      <div className="flex items-center gap-2">
                        <Link
                          to={`/decisions/${decision.decision_id}`}
                          className={clsx("font-mono text-xs", colors.text, "hover:underline")}
                        >
                          {decision.decision_code || decision.decision_id.slice(0, 12) + '...'}
                        </Link>
                        <span className="text-xs text-gray-400">({decision.feature_id})</span>
                      </div>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {decision.related_decisions?.map(relId => {
                          const related = allDecisions.find(r => r.decision_id === relId)
                          if (!related || related.group_id === groupId) return null
                          return (
                            <Link
                              key={relId}
                              to={`/decisions/${relId}`}
                              className="text-xs px-2 py-1 bg-gray-200 rounded hover:bg-gray-300"
                            >
                              {related.group_id} → {related.decision_code || relId.slice(0, 8)}
                            </Link>
                          )
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-400 text-sm text-center py-4">
                  No cross-group references from this group
                </p>
              )}
            </div>
          </div>

          {/* Recent Decisions */}
          <div className="bg-white rounded-lg border shadow-sm">
            <div className="px-4 py-3 border-b bg-gray-50">
              <h3 className="font-medium text-gray-900">Recent Decisions</h3>
              <p className="text-sm text-gray-500">Latest decisions in {GROUP_LABELS[groupId]}</p>
            </div>
            <div className="p-4">
              {groupDecisions.length > 0 ? (
                <div className="space-y-2">
                  {[...groupDecisions]
                    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
                    .slice(0, 5)
                    .map(decision => (
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
                            {decision.feature_id}
                          </span>
                        </div>
                        <span className="text-xs text-gray-400">
                          {new Date(decision.created_at).toLocaleDateString()}
                        </span>
                      </Link>
                    ))}
                </div>
              ) : (
                <p className="text-gray-400 text-sm text-center py-4">
                  No decisions in this group yet
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
