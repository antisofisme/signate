import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../shared/api'
import { SkeletonPage } from '../components/ui/skeleton'
import { getCurrentDecisions, buildSupersededSet, getDecisionCounts } from '../shared/decisionUtils'

/**
 * Scope Projection
 * Per MANTRA-L1-PROJECTION-CATALOG-001 §5
 *
 * Displays:
 * - FE / BE / Infra / CI-CD scope
 * - Cross-group reference
 *
 * Does NOT display:
 * - Prioritas
 * - Tingkat kepentingan
 */

interface Decision {
  decision_id: string
  decision_code: string | null  // Human-readable code: INT-F01-001-v1.0.0
  version: string
  statement: string
  scope: string
  blast_radius: string
  group_id: string
  feature_id: string
  related_decisions: string[]
  tags: string[]
  tech_stack: string[]
}

// Technical Area Categories (12 total)
const SCOPE_CATEGORIES = ['FE', 'BE', 'DB', 'API', 'INFRA', 'SECURITY', 'DEVOPS', 'TESTING', 'PERF', 'DATA', 'ARCH', 'OTHER'] as const

const SCOPE_COLORS: Record<string, string> = {
  // Core Development
  'FE': 'bg-blue-100 text-blue-700',
  'BE': 'bg-green-100 text-green-700',
  'DB': 'bg-cyan-100 text-cyan-700',
  'API': 'bg-teal-100 text-teal-700',
  // Infrastructure & Operations
  'INFRA': 'bg-purple-100 text-purple-700',
  'CICD': 'bg-orange-100 text-orange-700',
  'DEVOPS': 'bg-amber-100 text-amber-700',
  // Quality & Security
  'SECURITY': 'bg-red-100 text-red-700',
  'TESTING': 'bg-pink-100 text-pink-700',
  'PERF': 'bg-yellow-100 text-yellow-700',
  // Architecture & Data (NEW)
  'DATA': 'bg-indigo-100 text-indigo-700',
  'ARCH': 'bg-violet-100 text-violet-700',
  // Fallback
  'OTHER': 'bg-gray-100 text-gray-500',
}

function categorizeByTags(tags: string[]): string[] {
  if (!tags || tags.length === 0) return ['OTHER']

  const categories: string[] = []
  const tagSet = new Set(tags.map(t => t.toUpperCase()))

  // Direct mapping - each tag maps to its category
  const directMappings = ['FE', 'BE', 'DB', 'API', 'INFRA', 'SECURITY', 'DEVOPS', 'CICD', 'TESTING', 'PERF', 'DATA', 'ARCH']

  for (const tag of directMappings) {
    if (tagSet.has(tag)) {
      categories.push(tag)
    }
  }

  return categories.length > 0 ? [...new Set(categories)] : ['OTHER']
}

export default function ScopeProjection() {
  const { data, isLoading } = useQuery({
    queryKey: ['decisions'],
    queryFn: () => api.get('/api/v1/decisions').then(r => r.data),
  })

  if (isLoading) {
    return <SkeletonPage />
  }

  const allDecisions: Decision[] = data?.decisions || []
  // Cast to any[] for utility functions (local Decision interface is compatible subset)
  const currentDecisions = getCurrentDecisions(allDecisions as any[]) as Decision[]
  const supersededSet = buildSupersededSet(allDecisions as any[])
  const counts = getDecisionCounts(allDecisions as any[])

  // Group CURRENT decisions by tags category (a decision can appear in multiple categories)
  const byScope: Record<string, Decision[]> = {}
  SCOPE_CATEGORIES.forEach(cat => {
    byScope[cat] = []
  })

  currentDecisions.forEach(decision => {
    const categories = categorizeByTags(decision.tags || [])
    categories.forEach(category => {
      if (byScope[category]) {
        byScope[category].push(decision)
      }
    })
  })

  // Track historical counts per category for indicators
  const historicalByScope: Record<string, number> = {}
  SCOPE_CATEGORIES.forEach(cat => {
    const historicalInCategory = allDecisions.filter(d =>
      supersededSet.has(d.decision_id) &&
      categorizeByTags(d.tags || []).includes(cat)
    )
    historicalByScope[cat] = historicalInCategory.length
  })

  // Cross-group references (only from current decisions)
  const crossGroupRefs: { from: Decision; to: string }[] = []
  currentDecisions.forEach(decision => {
    decision.related_decisions?.forEach(relId => {
      const related = allDecisions.find(d => d.decision_id === relId)
      if (related && related.group_id !== decision.group_id) {
        crossGroupRefs.push({ from: decision, to: relId })
      }
    })
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Technical Areas</h1>
        <p className="mt-2 text-gray-600">
          {counts.current} current decisions across 12 technical areas
          {counts.superseded > 0 && (
            <span className="text-gray-400 ml-1">
              ({counts.total} total incl. {counts.superseded} historical)
            </span>
          )}
        </p>
      </div>

      {/* Scope Distribution */}
      <div className="grid grid-cols-3 gap-4">
        {SCOPE_CATEGORIES.map(category => (
          <div key={category} className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center justify-between mb-3">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${SCOPE_COLORS[category]}`}>
                {category}
              </span>
              <div className="text-right">
                <span className="text-2xl font-bold text-gray-900">
                  {byScope[category].length}
                </span>
                {historicalByScope[category] > 0 && (
                  <span className="text-xs text-gray-400 block">
                    +{historicalByScope[category]} historical
                  </span>
                )}
              </div>
            </div>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {byScope[category].slice(0, 5).map(decision => (
                <Link
                  key={decision.decision_id}
                  to={`/decisions/${decision.decision_id}`}
                  className="block p-2 bg-gray-50 rounded hover:bg-gray-100 transition-colors"
                >
                  <div className="text-xs text-indigo-600 font-mono font-medium">
                    {decision.decision_code || decision.decision_id.slice(0, 8) + '...'}
                  </div>
                  <div className="text-xs text-gray-600 truncate">
                    {decision.statement.slice(0, 50)}...
                  </div>
                </Link>
              ))}
              {byScope[category].length > 5 && (
                <div className="text-xs text-gray-500 text-center">
                  +{byScope[category].length - 5} more
                </div>
              )}
              {byScope[category].length === 0 && (
                <div className="text-xs text-gray-400 text-center py-2">
                  No decisions
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Blast Radius Overview */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Blast Radius Distribution</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="px-3 py-2 text-left text-gray-500 font-medium">Decision</th>
                <th className="px-3 py-2 text-left text-gray-500 font-medium">Technical Areas</th>
                <th className="px-3 py-2 text-left text-gray-500 font-medium">Impact Level</th>
                <th className="px-3 py-2 text-left text-gray-500 font-medium">Group/Feature</th>
              </tr>
            </thead>
            <tbody>
              {currentDecisions.slice(0, 10).map(decision => (
                <tr key={decision.decision_id} className="border-b border-gray-100">
                  <td className="px-3 py-2">
                    <Link
                      to={`/decisions/${decision.decision_id}`}
                      className="text-indigo-600 hover:text-indigo-500 font-mono text-xs font-medium"
                    >
                      {decision.decision_code || decision.decision_id.slice(0, 8) + '...'}
                    </Link>
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex flex-wrap gap-1">
                      {(decision.tags || []).length > 0 ? (
                        decision.tags.slice(0, 3).map(tag => (
                          <span key={tag} className={`px-2 py-0.5 rounded text-xs ${SCOPE_COLORS[tag] || SCOPE_COLORS['OTHER']}`}>
                            {tag}
                          </span>
                        ))
                      ) : (
                        <span className="px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-500">-</span>
                      )}
                    </div>
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex flex-col gap-1">
                      <span className={`px-2 py-0.5 rounded text-xs inline-block w-fit ${
                        decision.scope === 'ORGANIZATION' ? 'bg-red-100 text-red-700' :
                        decision.scope === 'DOMAIN' ? 'bg-orange-100 text-orange-700' :
                        'bg-green-100 text-green-700'
                      }`}>
                        {decision.scope || 'APP'}
                      </span>
                      <span className="text-gray-400 text-xs">
                        Risk: {decision.blast_radius || 'LOW'}
                      </span>
                    </div>
                  </td>
                  <td className="px-3 py-2 text-gray-500 text-xs">
                    G{decision.group_id.split('-')[1]}/{decision.feature_id}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Cross-Group References */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Cross-Group References</h3>
        {crossGroupRefs.length > 0 ? (
          <div className="space-y-2">
            {crossGroupRefs.map((ref, index) => {
              const toDecision = allDecisions.find(d => d.decision_id === ref.to)
              return (
                <div key={index} className="flex items-center gap-2 text-sm">
                  <Link
                    to={`/decisions/${ref.from.decision_id}`}
                    className="text-indigo-600 hover:text-indigo-500 font-mono text-xs font-medium"
                  >
                    {ref.from.decision_code || ref.from.decision_id.slice(0, 8)}
                  </Link>
                  <span className="text-gray-500">(G{ref.from.group_id.split('-')[1]})</span>
                  <span className="text-gray-400">→</span>
                  <Link
                    to={`/decisions/${ref.to}`}
                    className="text-indigo-600 hover:text-indigo-500 font-mono text-xs font-medium"
                  >
                    {toDecision?.decision_code || ref.to.slice(0, 8)}
                  </Link>
                </div>
              )
            })}
          </div>
        ) : (
          <p className="text-gray-500 text-sm">No cross-group references found</p>
        )}
      </div>

      {/* Projection Note */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <h4 className="text-sm font-medium text-amber-800 mb-1">Projection Note</h4>
        <p className="text-xs text-amber-700">
          This projection shows scope categorization and blast radius factually.
          It does NOT indicate priority or importance level.
          Per MANTRA-L1-PROJECTION-CATALOG-001 §5.
        </p>
      </div>
    </div>
  )
}
