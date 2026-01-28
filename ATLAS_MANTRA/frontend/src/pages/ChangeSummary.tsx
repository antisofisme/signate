import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../shared/api'
import { ASPECT_LABELS } from '../shared/constants'
import { SkeletonPage } from '../components/ui/skeleton'

/**
 * Change Summary Projection
 * Per MANTRA-L1-PROJECTION-CATALOG-001 §7
 *
 * Displays:
 * - Decision baru
 * - Decision yang superseded
 * - Feature terdampak
 *
 * Does NOT display:
 * - Improvement claim
 * - Breaking change label
 */

interface Decision {
  decision_id: string
  decision_code: string | null  // Human-readable code: INT-A01-001-v1.0.0
  version: string
  statement: string
  rationale: string
  domain_id: string
  aspect_id: string
  supersedes: string | null
  created_at: string
}

export default function ChangeSummary() {
  const { data, isLoading } = useQuery({
    queryKey: ['decisions'],
    queryFn: () => api.get('/api/v1/decisions').then(r => r.data),
  })

  if (isLoading) {
    return <SkeletonPage />
  }

  const decisions: Decision[] = data?.decisions || []

  // Sort by created_at descending
  const sortedDecisions = [...decisions].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  )

  // Find superseded decisions (decisions that have been superseded by others)
  const supersededIds = new Set(decisions.map(d => d.supersedes).filter(Boolean))

  // Categorize decisions
  const newDecisions = sortedDecisions.filter(d => !d.supersedes)
  const revisions = sortedDecisions.filter(d => d.supersedes)
  const supersededDecisions = decisions.filter(d => supersededIds.has(d.decision_id))

  // Aspects affected (has at least one decision)
  const affectedAspects = new Set<string>()
  decisions.forEach(d => {
    affectedAspects.add(`${d.domain_id}/${d.aspect_id}`)
  })

  // Group changes by date
  const changesByDate: Record<string, Decision[]> = {}
  sortedDecisions.forEach(d => {
    const date = new Date(d.created_at).toLocaleDateString()
    if (!changesByDate[date]) {
      changesByDate[date] = []
    }
    changesByDate[date].push(d)
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Change Summary</h1>
        <p className="mt-2 text-gray-600">
          Factual record of decision changes (no improvement/breaking claims)
        </p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-sm border p-4 text-center">
          <div className="text-2xl font-bold text-gray-900">{decisions.length}</div>
          <div className="text-xs text-gray-500">Total Decisions</div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-4 text-center">
          <div className="text-2xl font-bold text-green-600">{newDecisions.length}</div>
          <div className="text-xs text-gray-500">Original Decisions</div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-4 text-center">
          <div className="text-2xl font-bold text-blue-600">{revisions.length}</div>
          <div className="text-xs text-gray-500">Revisions</div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-4 text-center">
          <div className="text-2xl font-bold text-gray-400">{supersededDecisions.length}</div>
          <div className="text-xs text-gray-500">Superseded</div>
        </div>
      </div>

      {/* Aspects Affected */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Aspects with Decisions</h3>
        <div className="flex flex-wrap gap-2">
          {Array.from(affectedAspects).map(aspectKey => {
            const [domainId, aspectId] = aspectKey.split('/')
            const count = decisions.filter(
              d => d.domain_id === domainId && d.aspect_id === aspectId
            ).length
            return (
              <div
                key={aspectKey}
                className="px-3 py-2 bg-gray-50 rounded border"
              >
                <div className="text-xs text-gray-400">{domainId}</div>
                <div className="text-sm text-indigo-600">{ASPECT_LABELS[aspectId]}</div>
                <div className="text-xs text-gray-500">
                  {aspectId}
                </div>
                <div className="text-xs text-gray-400 mt-1">
                  {count} decision{count !== 1 ? 's' : ''}
                </div>
              </div>
            )
          })}
          {affectedAspects.size === 0 && (
            <p className="text-gray-500 text-sm">No aspects have decisions yet</p>
          )}
        </div>
      </div>

      {/* Change Timeline */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Change Timeline</h3>
        <div className="space-y-6">
          {Object.entries(changesByDate).map(([date, dayDecisions]) => (
            <div key={date}>
              <div className="flex items-center gap-3 mb-3">
                <div className="w-2 h-2 bg-indigo-500 rounded-full" />
                <span className="text-gray-600 text-sm">{date}</span>
                <span className="text-xs text-gray-400">
                  ({dayDecisions.length} change{dayDecisions.length !== 1 ? 's' : ''})
                </span>
              </div>
              <div className="ml-4 space-y-2">
                {dayDecisions.map(decision => (
                  <div
                    key={decision.decision_id}
                    className="flex items-start gap-3 p-3 bg-gray-50 rounded"
                  >
                    <div className="flex-shrink-0">
                      {decision.supersedes ? (
                        <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">
                          REVISION
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs">
                          NEW
                        </span>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <Link
                        to={`/decisions/${decision.decision_id}`}
                        className="text-indigo-600 hover:text-indigo-500 font-mono text-xs font-medium"
                      >
                        {decision.decision_code || decision.decision_id.slice(0, 12) + '...'}
                      </Link>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-gray-500">{decision.domain_id}</span>
                        <span className="text-gray-400">→</span>
                        <span className="text-xs text-gray-600">{ASPECT_LABELS[decision.aspect_id]}</span>
                        <span className="text-xs text-gray-400">
                          ({decision.aspect_id})
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 mt-1 truncate">
                        {decision.statement}
                      </p>
                      {decision.supersedes && (() => {
                        const supersededDecision = decisions.find(d => d.decision_id === decision.supersedes)
                        return (
                          <div className="mt-2 text-xs">
                            <span className="text-gray-500">Supersedes: </span>
                            <Link
                              to={`/decisions/${decision.supersedes}`}
                              className="text-gray-600 hover:text-gray-700 font-mono"
                            >
                              {supersededDecision?.decision_code || decision.supersedes.slice(0, 8) + '...'}
                            </Link>
                          </div>
                        )
                      })()}
                    </div>
                    <div className="text-xs text-gray-400 font-mono">
                      v{decision.version}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}

          {Object.keys(changesByDate).length === 0 && (
            <p className="text-gray-500 text-sm text-center py-4">
              No changes recorded yet
            </p>
          )}
        </div>
      </div>

      {/* Superseded Decisions */}
      {supersededDecisions.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Superseded Decisions</h3>
          <div className="space-y-2">
            {supersededDecisions.map(decision => {
              const supersededBy = decisions.find(d => d.supersedes === decision.decision_id)
              return (
                <div
                  key={decision.decision_id}
                  className="flex items-center gap-3 p-3 bg-gray-50 rounded"
                >
                  <Link
                    to={`/decisions/${decision.decision_id}`}
                    className="text-gray-500 hover:text-gray-700 font-mono text-xs"
                  >
                    {decision.decision_code || decision.decision_id.slice(0, 12) + '...'}
                  </Link>
                  <span className="text-gray-400">→</span>
                  <span className="text-xs text-gray-500">superseded by</span>
                  <span className="text-gray-400">→</span>
                  {supersededBy && (
                    <Link
                      to={`/decisions/${supersededBy.decision_id}`}
                      className="text-indigo-600 hover:text-indigo-500 font-mono text-xs font-medium"
                    >
                      {supersededBy.decision_code || supersededBy.decision_id.slice(0, 12) + '...'}
                    </Link>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Projection Note */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <h4 className="text-sm font-medium text-amber-800 mb-1">Projection Note</h4>
        <p className="text-xs text-amber-700">
          This projection shows factual changes only.
          Labels "NEW" and "REVISION" are structural, not qualitative.
          It does NOT indicate improvement or breaking change status.
          Per MANTRA-L1-PROJECTION-CATALOG-001 §7.
        </p>
      </div>
    </div>
  )
}
