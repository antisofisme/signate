import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../shared/api'
import { ASPECT_LABELS, DOMAIN_LABELS } from '../shared/constants'
import { SkeletonPage } from '../components/ui/skeleton'

/**
 * Evolution Timeline Projection
 * Per MANTRA-L1-PROJECTION-CATALOG-001 §4
 *
 * Displays:
 * - Version
 * - created_at
 * - Ringkasan rationale perubahan
 *
 * Does NOT display:
 * - Latest = correct
 * - Validity claim
 */

interface Decision {
  decision_id: string
  decision_code: string | null  // Human-readable code: INT-A01-001-v1.0.0
  version: string
  created_at: string
  supersedes: string | null
  statement: string
  rationale: string
  domain_id: string
  aspect_id: string
}

export default function EvolutionTimeline() {
  const [searchParams] = useSearchParams()
  const decisionId = searchParams.get('decision')

  const { data, isLoading } = useQuery({
    queryKey: ['decisions'],
    queryFn: () => api.get('/api/v1/decisions').then(r => r.data),
  })

  if (isLoading) {
    return <SkeletonPage />
  }

  const decisions: Decision[] = data?.decisions || []

  // Build version chains
  const buildChain = (startId: string): Decision[] => {
    const chain: Decision[] = []
    let currentId: string | null = startId

    while (currentId) {
      const decision = decisions.find(d => d.decision_id === currentId)
      if (decision) {
        chain.push(decision)
        // Find what this decision supersedes
        currentId = decision.supersedes
      } else {
        break
      }
    }

    return chain.reverse() // Oldest first
  }

  // Find all chain heads (decisions that are not superseded by anything)
  const supersededIds = new Set(decisions.map(d => d.supersedes).filter(Boolean))
  const chainHeads = decisions.filter(d => !supersededIds.has(d.decision_id))

  // If specific decision requested, show its chain
  const selectedChain = decisionId ? buildChain(decisionId) : null

  // Group chains by aspect
  const chainsByAspect: Record<string, Decision[][]> = {}
  chainHeads.forEach(head => {
    const chain = buildChain(head.decision_id)
    if (chain.length > 0) {
      const aspectKey = `${chain[0].domain_id}/${chain[0].aspect_id}`
      if (!chainsByAspect[aspectKey]) {
        chainsByAspect[aspectKey] = []
      }
      chainsByAspect[aspectKey].push(chain)
    }
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Evolution Timeline</h1>
        <p className="mt-2 text-gray-600">
          Version chains showing decision evolution (no validity judgment)
        </p>
      </div>

      {/* Selected Chain Detail */}
      {selectedChain && selectedChain.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6 border-indigo-200">
          <h3 className="text-indigo-600 font-medium mb-4">
            Chain for: {selectedChain[selectedChain.length - 1].decision_code || selectedChain[selectedChain.length - 1].decision_id.slice(0, 8) + '...'}
          </h3>
          <div className="relative">
            {/* Timeline line */}
            <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />

            <div className="space-y-6">
              {selectedChain.map((decision, index) => (
                <div key={decision.decision_id} className="relative pl-10">
                  {/* Timeline dot */}
                  <div className={`absolute left-2.5 w-3 h-3 rounded-full ${
                    index === selectedChain.length - 1
                      ? 'bg-indigo-500'
                      : 'bg-gray-400'
                  }`} />

                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-gray-500">
                        {new Date(decision.created_at).toLocaleString()}
                      </span>
                      <span className="px-2 py-0.5 bg-gray-200 rounded text-xs text-gray-700 font-mono">
                        {decision.version}
                      </span>
                    </div>
                    <Link
                      to={`/decisions/${decision.decision_id}`}
                      className="text-indigo-600 hover:text-indigo-500 font-mono text-sm"
                    >
                      {decision.decision_code || decision.decision_id.slice(0, 12) + '...'}
                    </Link>
                    <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                      {decision.rationale}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* All Chains by Aspect */}
      {!selectedChain && (
        <div className="space-y-6">
          {Object.entries(chainsByAspect).map(([aspectKey, chains]) => {
            const [domainId, aspectId] = aspectKey.split('/')
            return (
              <div key={aspectKey} className="bg-white rounded-lg shadow-sm border p-6">
                <div className="flex items-center gap-3 mb-4">
                  <span className="text-indigo-600 font-medium">{DOMAIN_LABELS[domainId]}</span>
                  <span className="text-gray-400">→</span>
                  <span className="text-gray-700">{ASPECT_LABELS[aspectId]}</span>
                  <span className="text-xs text-gray-400">
                    ({domainId}/{aspectId})
                  </span>
                </div>

                <div className="space-y-4">
                  {chains.map((chain, chainIndex) => (
                    <div key={chainIndex} className="flex items-center gap-2 overflow-x-auto pb-2">
                      {chain.map((decision, index) => (
                        <div key={decision.decision_id} className="flex items-center">
                          <Link
                            to={`/decisions/${decision.decision_id}`}
                            className="flex-shrink-0 p-2 bg-gray-50 rounded hover:bg-gray-100 transition-colors"
                          >
                            <div className="text-xs text-gray-600 font-mono">
                              {decision.version}
                            </div>
                            <div className="text-xs text-gray-500">
                              {new Date(decision.created_at).toLocaleDateString()}
                            </div>
                          </Link>
                          {index < chain.length - 1 && (
                            <span className="text-gray-400 mx-1">→</span>
                          )}
                        </div>
                      ))}
                      <Link
                        to={`/timeline?decision=${chain[chain.length - 1].decision_id}`}
                        className="text-xs text-indigo-600 hover:text-indigo-500 ml-2"
                      >
                        View chain
                      </Link>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}

          {Object.keys(chainsByAspect).length === 0 && (
            <div className="bg-white rounded-lg shadow-sm border p-6 text-center text-gray-500">
              No version chains found. Decisions without supersedes links appear as single nodes.
            </div>
          )}
        </div>
      )}

      {/* Structural Note */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <h4 className="text-sm font-medium text-amber-800 mb-1">Projection Note</h4>
        <p className="text-xs text-amber-700">
          This projection shows factual version relationships only.
          It does NOT indicate which version is "correct" or "current".
          All versions are displayed equally per MANTRA-L1-PROJECTION-CATALOG-001 §4.
        </p>
      </div>
    </div>
  )
}
