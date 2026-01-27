import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../shared/api'
import { GROUPS, FEATURES, GROUP_LABELS, FEATURE_LABELS } from '../shared/constants'
import { SkeletonMatrix } from '../components/ui/skeleton'

/**
 * Matrix Overview Projection
 * Per MANTRA-L1-PROJECTION-CATALOG-001 §1
 *
 * Displays:
 * - Group name
 * - Feature name
 * - Jumlah decision (count)
 * - Jumlah version chain (optional)
 *
 * Does NOT display:
 * - Status
 * - Selected/active decision
 * - Value-judgment colors
 */

export default function DecisionMatrix() {
  // Fetch all decisions grouped by group/feature
  const { data: grouped, isLoading } = useQuery({
    queryKey: ['grouped'],
    queryFn: () => api.get('/api/v1/grouped').then(r => r.data),
  })

  if (isLoading) {
    return <SkeletonMatrix />
  }

  // Count decisions per group/feature
  const getCount = (group: string, feature: string): number => {
    return grouped?.grouped?.[group]?.[feature]?.length ?? 0
  }

  // Count version chains (decisions with supersedes)
  const getChainCount = (group: string, feature: string): number => {
    const decisions = grouped?.grouped?.[group]?.[feature] ?? []
    return decisions.filter((d: any) => d.supersedes).length
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Decision Matrix</h1>
        <p className="mt-2 text-gray-600">
          4 Groups x 4 Features = 16 Decision Categories per MANTRA-DEC-002
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="px-4 py-3 text-left text-gray-500 font-medium">Group</th>
              <th className="px-4 py-3 text-center text-gray-500 font-medium">Feature 1</th>
              <th className="px-4 py-3 text-center text-gray-500 font-medium">Feature 2</th>
              <th className="px-4 py-3 text-center text-gray-500 font-medium">Feature 3</th>
              <th className="px-4 py-3 text-center text-gray-500 font-medium">Feature 4</th>
            </tr>
          </thead>
          <tbody>
            {GROUPS.map((group) => (
              <tr key={group} className="border-b border-gray-100">
                <td className="px-4 py-4">
                  <div>
                    <span className="font-medium text-indigo-600">{GROUP_LABELS[group]}</span>
                    <div className="text-xs text-gray-400 mt-1">
                      Group {group.split('-')[1]}
                    </div>
                  </div>
                </td>
                {FEATURES[group].map((feature) => {
                  const count = getCount(group, feature)
                  const chainCount = getChainCount(group, feature)
                  return (
                    <td key={feature} className="px-4 py-4">
                      <Link
                        to={`/decisions?group=${group}&feature=${feature}`}
                        className="block p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors text-center border"
                      >
                        <div className="text-xs text-gray-500 mb-1">
                          {feature}
                        </div>
                        <div className="text-sm font-medium text-gray-700 mb-2">
                          {FEATURE_LABELS[feature]}
                        </div>
                        <div className="text-2xl font-bold text-gray-900">
                          {count}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          {count === 1 ? 'decision' : 'decisions'}
                        </div>
                        {chainCount > 0 && (
                          <div className="text-xs text-gray-400 mt-1">
                            {chainCount} version {chainCount === 1 ? 'chain' : 'chains'}
                          </div>
                        )}
                      </Link>
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Structural Information - No value judgments */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="font-semibold text-gray-900 mb-3">Matrix Structure</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Total Cells:</span>
            <span className="text-gray-900 ml-2">16</span>
          </div>
          <div>
            <span className="text-gray-500">Groups:</span>
            <span className="text-gray-900 ml-2">4</span>
          </div>
          <div>
            <span className="text-gray-500">Features per Group:</span>
            <span className="text-gray-900 ml-2">4</span>
          </div>
          <div>
            <span className="text-gray-500">Per:</span>
            <span className="text-gray-900 ml-2">MANTRA-LAW-001 §3</span>
          </div>
        </div>
      </div>
    </div>
  )
}
