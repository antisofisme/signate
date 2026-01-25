import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../shared/api'
import { GROUP_LABELS } from '../shared/constants'

/**
 * Relationship / Impact Projection
 * Per MANTRA-L1-PROJECTION-CATALOG-001 §6
 *
 * Displays:
 * - related_decisions
 * - cross-feature reference
 * - cross-group reference
 *
 * Does NOT display:
 * - Dampak positif / negatif
 * - Kesimpulan risiko
 */

interface Decision {
  decision_id: string
  decision_code: string | null  // Human-readable code: INT-F01-001-v1.0.0
  version: string
  statement: string
  group_id: string
  feature_id: string
  related_decisions: string[]
  supersedes: string | null
}

interface Relationship {
  from: Decision
  to: Decision
  type: 'related' | 'supersedes' | 'cross-group' | 'cross-feature'
}

export default function RelationshipProjection() {
  const { data, isLoading } = useQuery({
    queryKey: ['decisions'],
    queryFn: () => api.get('/api/v1/decisions').then(r => r.data),
  })

  if (isLoading) {
    return <div className="text-gray-500">Loading relationships...</div>
  }

  const decisions: Decision[] = data?.decisions || []
  const decisionMap = new Map(decisions.map(d => [d.decision_id, d]))

  // Build relationships
  const relationships: Relationship[] = []
  const crossGroupRefs: Relationship[] = []
  const crossFeatureRefs: Relationship[] = []

  decisions.forEach(decision => {
    // Supersedes relationship
    if (decision.supersedes) {
      const target = decisionMap.get(decision.supersedes)
      if (target) {
        relationships.push({
          from: decision,
          to: target,
          type: 'supersedes',
        })
      }
    }

    // Related decisions
    decision.related_decisions?.forEach(relId => {
      const target = decisionMap.get(relId)
      if (target) {
        const rel: Relationship = {
          from: decision,
          to: target,
          type: 'related',
        }

        // Check if cross-group
        if (target.group_id !== decision.group_id) {
          rel.type = 'cross-group'
          crossGroupRefs.push(rel)
        } else if (target.feature_id !== decision.feature_id) {
          rel.type = 'cross-feature'
          crossFeatureRefs.push(rel)
        }

        relationships.push(rel)
      }
    })
  })

  // Group nodes by group/feature for visualization
  const nodesByGroup: Record<string, Decision[]> = {}
  decisions.forEach(d => {
    if (!nodesByGroup[d.group_id]) {
      nodesByGroup[d.group_id] = []
    }
    nodesByGroup[d.group_id].push(d)
  })

  // Calculate connectivity stats
  const stats = {
    totalDecisions: decisions.length,
    totalRelationships: relationships.length,
    crossGroupCount: crossGroupRefs.length,
    crossFeatureCount: crossFeatureRefs.length,
    isolatedNodes: decisions.filter(d =>
      !d.supersedes &&
      (!d.related_decisions || d.related_decisions.length === 0) &&
      !decisions.some(other => other.supersedes === d.decision_id) &&
      !decisions.some(other => other.related_decisions?.includes(d.decision_id))
    ).length,
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Relationship Projection</h1>
        <p className="mt-2 text-gray-600">
          Decision relationships and references (no impact judgment)
        </p>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-5 gap-4">
        <div className="bg-white rounded-lg shadow-sm border p-4 text-center">
          <div className="text-2xl font-bold text-gray-900">{stats.totalDecisions}</div>
          <div className="text-xs text-gray-500">Total Nodes</div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-4 text-center">
          <div className="text-2xl font-bold text-indigo-600">{stats.totalRelationships}</div>
          <div className="text-xs text-gray-500">Relationships</div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-4 text-center">
          <div className="text-2xl font-bold text-purple-600">{stats.crossGroupCount}</div>
          <div className="text-xs text-gray-500">Cross-Group</div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-4 text-center">
          <div className="text-2xl font-bold text-blue-600">{stats.crossFeatureCount}</div>
          <div className="text-xs text-gray-500">Cross-Feature</div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-4 text-center">
          <div className="text-2xl font-bold text-gray-400">{stats.isolatedNodes}</div>
          <div className="text-xs text-gray-500">Isolated</div>
        </div>
      </div>

      {/* Relationship Graph (Text-based) */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Relationship Map by Group</h3>
        <div className="space-y-6">
          {Object.entries(nodesByGroup).map(([groupId, groupDecisions]) => (
            <div key={groupId} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-indigo-600 font-medium">{GROUP_LABELS[groupId]}</span>
                <span className="text-xs text-gray-400">Group {groupId.split('-')[1]}</span>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {groupDecisions.map(decision => {
                  const outgoing = relationships.filter(r => r.from.decision_id === decision.decision_id)
                  const incoming = relationships.filter(r => r.to.decision_id === decision.decision_id)
                  const hasConnections = outgoing.length > 0 || incoming.length > 0

                  return (
                    <div
                      key={decision.decision_id}
                      className={`p-3 rounded ${hasConnections ? 'bg-gray-100' : 'bg-gray-50'}`}
                    >
                      <Link
                        to={`/decisions/${decision.decision_id}`}
                        className="text-indigo-600 hover:text-indigo-500 font-mono text-xs block font-medium"
                      >
                        {decision.decision_code || decision.decision_id.slice(0, 8)}
                      </Link>
                      <div className="text-xs text-gray-500 mt-1">
                        {decision.feature_id}
                      </div>
                      {hasConnections && (
                        <div className="flex gap-2 mt-2 text-xs">
                          {outgoing.length > 0 && (
                            <span className="text-green-600">↑{outgoing.length}</span>
                          )}
                          {incoming.length > 0 && (
                            <span className="text-blue-600">↓{incoming.length}</span>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Cross-Group Relationships */}
      {crossGroupRefs.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Cross-Group Relationships</h3>
          <div className="space-y-2">
            {crossGroupRefs.map((rel, index) => (
              <div key={index} className="flex items-center gap-3 p-2 bg-gray-50 rounded">
                <div className="flex-1">
                  <Link
                    to={`/decisions/${rel.from.decision_id}`}
                    className="text-indigo-600 hover:text-indigo-500 font-mono text-xs font-medium"
                  >
                    {rel.from.decision_code || rel.from.decision_id.slice(0, 8)}
                  </Link>
                  <span className="text-gray-500 text-xs ml-2">
                    (G{rel.from.group_id.split('-')[1]}/{rel.from.feature_id})
                  </span>
                </div>
                <span className="text-purple-500">→</span>
                <div className="flex-1">
                  <Link
                    to={`/decisions/${rel.to.decision_id}`}
                    className="text-indigo-600 hover:text-indigo-500 font-mono text-xs font-medium"
                  >
                    {rel.to.decision_code || rel.to.decision_id.slice(0, 8)}
                  </Link>
                  <span className="text-gray-500 text-xs ml-2">
                    (G{rel.to.group_id.split('-')[1]}/{rel.to.feature_id})
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Cross-Feature Relationships */}
      {crossFeatureRefs.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Cross-Feature Relationships (Same Group)</h3>
          <div className="space-y-2">
            {crossFeatureRefs.map((rel, index) => (
              <div key={index} className="flex items-center gap-3 p-2 bg-gray-50 rounded">
                <div className="flex-1">
                  <Link
                    to={`/decisions/${rel.from.decision_id}`}
                    className="text-indigo-600 hover:text-indigo-500 font-mono text-xs font-medium"
                  >
                    {rel.from.decision_code || rel.from.decision_id.slice(0, 8)}
                  </Link>
                  <span className="text-gray-500 text-xs ml-2">
                    ({rel.from.feature_id})
                  </span>
                </div>
                <span className="text-blue-500">→</span>
                <div className="flex-1">
                  <Link
                    to={`/decisions/${rel.to.decision_id}`}
                    className="text-indigo-600 hover:text-indigo-500 font-mono text-xs font-medium"
                  >
                    {rel.to.decision_code || rel.to.decision_id.slice(0, 8)}
                  </Link>
                  <span className="text-gray-500 text-xs ml-2">
                    ({rel.to.feature_id})
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Projection Note */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <h4 className="text-sm font-medium text-amber-800 mb-1">Projection Note</h4>
        <p className="text-xs text-amber-700">
          This projection shows structural relationships only.
          It does NOT indicate positive/negative impact or risk conclusions.
          Per MANTRA-L1-PROJECTION-CATALOG-001 §6.
        </p>
      </div>
    </div>
  )
}
