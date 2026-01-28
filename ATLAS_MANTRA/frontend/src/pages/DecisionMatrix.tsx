import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useMemo } from 'react'
import { api } from '../shared/api'
import { DOMAINS, ASPECTS, DOMAIN_LABELS, ASPECT_LABELS, ASPECT_ICONS } from '../shared/constants'
import { SkeletonMatrix } from '../components/ui/skeleton'
import { buildSupersededSet } from '../shared/decisionUtils'

/**
 * Matrix Overview Projection
 * Per MANTRA-L1-PROJECTION-CATALOG-001 §1
 *
 * Displays:
 * - Domain name
 * - Aspect name
 * - Jumlah decision (count)
 * - Jumlah version chain (optional)
 *
 * Does NOT display:
 * - Status
 * - Selected/active decision
 * - Value-judgment colors
 */

export default function DecisionMatrix() {
  // Fetch all decisions grouped by domain/aspect
  const { data: grouped, isLoading } = useQuery({
    queryKey: ['grouped'],
    queryFn: () => api.get('/api/v1/grouped').then(r => r.data),
  })

  // Build superseded set for filtering
  const supersededSet = useMemo(() => {
    if (!grouped?.grouped) return new Set<string>()
    const allDecisions = Object.values(grouped.grouped)
      .flatMap((domain: any) => Object.values(domain).flat())
    return buildSupersededSet(allDecisions as any[])
  }, [grouped])

  if (isLoading) {
    return <SkeletonMatrix />
  }

  // Count CURRENT decisions per domain/aspect
  const getCurrentCount = (domain: string, aspect: string): number => {
    const decisions = grouped?.grouped?.[domain]?.[aspect] ?? []
    return decisions.filter((d: any) => !supersededSet.has(d.decision_id)).length
  }

  // Count TOTAL decisions per domain/aspect (for tooltip)
  const getTotalCount = (domain: string, aspect: string): number => {
    return grouped?.grouped?.[domain]?.[aspect]?.length ?? 0
  }

  // Count historical decisions per domain/aspect
  const getHistoricalCount = (domain: string, aspect: string): number => {
    return getTotalCount(domain, aspect) - getCurrentCount(domain, aspect)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Decision Matrix</h1>
        <p className="mt-2 text-gray-600">
          4 Domains x 4 Aspects = 16 Decision Categories per MANTRA-DEC-002
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="px-4 py-3 text-left text-gray-500 font-medium">Domain</th>
              <th className="px-4 py-3 text-center text-gray-500 font-medium">Aspect 1</th>
              <th className="px-4 py-3 text-center text-gray-500 font-medium">Aspect 2</th>
              <th className="px-4 py-3 text-center text-gray-500 font-medium">Aspect 3</th>
              <th className="px-4 py-3 text-center text-gray-500 font-medium">Aspect 4</th>
            </tr>
          </thead>
          <tbody>
            {DOMAINS.map((domain) => (
              <tr key={domain} className="border-b border-gray-100">
                <td className="px-4 py-4">
                  <div>
                    <span className="font-medium text-indigo-600">{DOMAIN_LABELS[domain]}</span>
                    <div className="text-xs text-gray-400 mt-1">
                      Domain {domain}
                    </div>
                  </div>
                </td>
                {ASPECTS[domain].map((aspect) => {
                  const currentCount = getCurrentCount(domain, aspect)
                  const historicalCount = getHistoricalCount(domain, aspect)
                  const totalCount = getTotalCount(domain, aspect)
                  return (
                    <td key={aspect} className="px-4 py-4">
                      <Link
                        to={`/decisions?domain=${domain}&aspect=${aspect}`}
                        className="block p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors text-center border"
                        title={`${currentCount} current, ${historicalCount} historical`}
                      >
                        <div className="flex items-center justify-center gap-1 text-xs text-gray-500 mb-1">
                          <span>{ASPECT_ICONS[aspect]}</span>
                          <span>{aspect}</span>
                        </div>
                        <div className="text-sm font-medium text-gray-700 mb-2">
                          {ASPECT_LABELS[aspect]}
                        </div>
                        <div className="text-2xl font-bold text-gray-900">
                          {currentCount}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          current {currentCount === 1 ? 'decision' : 'decisions'}
                        </div>
                        {historicalCount > 0 && (
                          <div className="text-xs text-gray-400 mt-1">
                            ({totalCount} total)
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

      {/* Aspect Quick Navigation */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Quick Navigation by Aspect</h3>
        <div className="grid grid-cols-4 gap-4">
          {DOMAINS.map((domain) => {
            const domainColors: Record<string, string> = {
              'INT': 'bg-blue-50 hover:bg-blue-100 border-blue-200',
              'ARCH': 'bg-green-50 hover:bg-green-100 border-green-200',
              'CTL': 'bg-orange-50 hover:bg-orange-100 border-orange-200',
              'EVO': 'bg-purple-50 hover:bg-purple-100 border-purple-200',
            }
            return (
              <div key={domain} className="space-y-2">
                <Link
                  to={`/domain/${domain.toLowerCase()}`}
                  className="block font-semibold text-sm text-gray-700 hover:text-indigo-600"
                >
                  {domain}: {DOMAIN_LABELS[domain]}
                </Link>
                {ASPECTS[domain].map((aspect) => (
                  <Link
                    key={aspect}
                    to={`/decisions?domain=${domain}&aspect=${aspect}`}
                    className={`block px-3 py-2 text-sm rounded border transition-colors ${domainColors[domain]}`}
                  >
                    <span className="mr-1">{ASPECT_ICONS[aspect]}</span>
                    <span className="font-mono text-xs text-gray-400">{aspect}</span>
                    <span className="ml-1 text-gray-700">{ASPECT_LABELS[aspect]}</span>
                    <span className="ml-2 text-xs text-gray-400">({getCurrentCount(domain, aspect)})</span>
                  </Link>
                ))}
              </div>
            )
          })}
        </div>
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
            <span className="text-gray-500">Domains:</span>
            <span className="text-gray-900 ml-2">4</span>
          </div>
          <div>
            <span className="text-gray-500">Aspects per Domain:</span>
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
