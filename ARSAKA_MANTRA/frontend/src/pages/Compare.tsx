import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { clsx } from 'clsx'
import { Link } from 'react-router-dom'
import { decisionsApi, Decision, FieldDifference } from '../shared/api'
import { ASPECT_LABELS, DOMAIN_COLORS } from '../shared/constants'

export default function Compare() {
  const [decisionA, setDecisionA] = useState('')
  const [decisionB, setDecisionB] = useState('')
  const [actor, setActor] = useState('')

  // Fetch all decisions for selection
  const { data: decisions } = useQuery({
    queryKey: ['decisions'],
    queryFn: () => decisionsApi.list({ limit: 1000 }),
  })

  // Compare query - only run when we have both IDs
  const { data: comparison, isLoading, error, refetch } = useQuery({
    queryKey: ['compare', decisionA, decisionB, actor],
    queryFn: () => decisionsApi.compare(decisionA, decisionB, actor || 'compare-user'),
    enabled: false, // Manual trigger
  })

  const handleCompare = () => {
    if (!decisionA || !decisionB) {
      alert('Please select two decisions to compare')
      return
    }
    if (decisionA === decisionB) {
      alert('Please select two different decisions')
      return
    }
    refetch()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Decision Comparison</h1>
        <p className="mt-2 text-gray-600">
          Compare two decisions side-by-side to identify differences and evolution
        </p>
      </div>

      {/* Selection Panel */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Select Decisions</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Decision A */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Decision A
            </label>
            <select
              value={decisionA}
              onChange={(e) => setDecisionA(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">Select decision...</option>
              {decisions?.decisions.map(d => (
                <option key={d.decision_id} value={d.decision_id}>
                  {d.decision_code || d.decision_id.slice(0, 8)} - {d.statement.slice(0, 50)}...
                </option>
              ))}
            </select>
          </div>

          {/* Decision B */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Decision B
            </label>
            <select
              value={decisionB}
              onChange={(e) => setDecisionB(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">Select decision...</option>
              {decisions?.decisions.map(d => (
                <option key={d.decision_id} value={d.decision_id}>
                  {d.decision_code || d.decision_id.slice(0, 8)} - {d.statement.slice(0, 50)}...
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Actor Input */}
        <div className="mt-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Your Name (for audit)
          </label>
          <input
            type="text"
            value={actor}
            onChange={(e) => setActor(e.target.value)}
            placeholder="Enter your name"
            className="w-full md:w-1/2 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <button
          onClick={handleCompare}
          disabled={!decisionA || !decisionB || isLoading}
          className="mt-4 btn btn-primary"
        >
          {isLoading ? 'Comparing...' : '🔍 Compare Decisions'}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700">Error: {(error as Error).message}</p>
        </div>
      )}

      {/* Comparison Results */}
      {comparison && (
        <div className="space-y-6">
          {/* Status Banner */}
          {comparison.is_supersedes_chain && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
              <div className="flex items-center gap-2">
                <span className="text-lg">🔗</span>
                <span className="font-medium text-amber-800">Evolution Chain Detected</span>
              </div>
              <p className="text-sm text-amber-700 mt-1">
                These decisions are in a supersedes chain.
                Direction: {comparison.supersedes_direction}
              </p>
            </div>
          )}

          {/* Side-by-side Comparison */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Decision A Card */}
            {comparison.decision_a && (
              <DecisionCard
                decision={comparison.decision_a}
                label="Decision A"
                color="blue"
              />
            )}

            {/* Decision B Card */}
            {comparison.decision_b && (
              <DecisionCard
                decision={comparison.decision_b}
                label="Decision B"
                color="purple"
              />
            )}
          </div>

          {/* Differences Table */}
          {comparison.differences.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="font-semibold text-gray-900 mb-4">
                📋 Differences ({comparison.differences.length})
              </h3>

              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2 px-3 font-medium text-gray-700">Field</th>
                      <th className="text-left py-2 px-3 font-medium text-blue-700">Decision A</th>
                      <th className="text-left py-2 px-3 font-medium text-purple-700">Decision B</th>
                      <th className="text-left py-2 px-3 font-medium text-gray-700">Change</th>
                    </tr>
                  </thead>
                  <tbody>
                    {comparison.differences.map((diff, idx) => (
                      <DifferenceRow key={idx} diff={diff} />
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* No Differences */}
          {comparison.differences.length === 0 && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
              <span className="text-2xl">✅</span>
              <p className="text-green-700 font-medium mt-2">No differences found</p>
              <p className="text-sm text-green-600">These decisions are identical</p>
            </div>
          )}

          {/* Common Info */}
          <div className="bg-gray-50 rounded-lg p-4 flex gap-6 text-sm">
            <div className="flex items-center gap-2">
              <span className={comparison.common_group ? 'text-green-500' : 'text-gray-400'}>
                {comparison.common_group ? '✓' : '✗'}
              </span>
              <span className="text-gray-700">Same Domain</span>
            </div>
            <div className="flex items-center gap-2">
              <span className={comparison.common_feature ? 'text-green-500' : 'text-gray-400'}>
                {comparison.common_feature ? '✓' : '✗'}
              </span>
              <span className="text-gray-700">Same Aspect</span>
            </div>
            <div className="flex items-center gap-2">
              <span className={comparison.is_supersedes_chain ? 'text-green-500' : 'text-gray-400'}>
                {comparison.is_supersedes_chain ? '✓' : '✗'}
              </span>
              <span className="text-gray-700">Supersedes Chain</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// =============================================================================
// Component: Decision Card
// =============================================================================
function DecisionCard({
  decision,
  label,
  color,
}: {
  decision: Decision
  label: string
  color: 'blue' | 'purple'
}) {
  const borderColor = color === 'blue' ? 'border-blue-500' : 'border-purple-500'
  const textColor = color === 'blue' ? 'text-blue-700' : 'text-purple-700'

  return (
    <div className={clsx('bg-white rounded-lg shadow-sm border-l-4 p-4', borderColor)}>
      <div className={clsx('text-xs font-medium mb-2', textColor)}>{label}</div>

      {/* Code & Domain */}
      <div className="flex items-center gap-2 mb-2">
        <span
          className="px-2 py-0.5 rounded text-xs text-white"
          style={{ backgroundColor: DOMAIN_COLORS[decision.domain_id || (decision as any).group_id] || '#6B7280' }}
        >
          {decision.domain_id || (decision as any).group_id}
        </span>
        <span className="font-mono text-sm text-gray-700">
          {decision.decision_code || decision.decision_id.slice(0, 8)}
        </span>
      </div>

      {/* Statement */}
      <p className="text-sm text-gray-900 font-medium mb-2">
        {decision.statement}
      </p>

      {/* Metadata Grid */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <span className="text-gray-500">Aspect:</span>
          <span className="ml-1 text-gray-700">{ASPECT_LABELS[decision.aspect_id || (decision as any).feature_id] || decision.aspect_id || (decision as any).feature_id}</span>
        </div>
        <div>
          <span className="text-gray-500">Version:</span>
          <span className="ml-1 text-gray-700">{decision.version}</span>
        </div>
        <div>
          <span className="text-gray-500">Scope:</span>
          <span className="ml-1 text-gray-700">{decision.scope}</span>
        </div>
        <div>
          <span className="text-gray-500">Blast Radius:</span>
          <span className="ml-1 text-gray-700">{decision.blast_radius}</span>
        </div>
      </div>

      {/* Supersedes */}
      {decision.supersedes && (
        <div className="mt-2 pt-2 border-t text-xs">
          <span className="text-gray-500">Supersedes:</span>
          <span className="ml-1 font-mono text-amber-600">{decision.supersedes.slice(0, 8)}...</span>
        </div>
      )}

      {/* Link to Detail */}
      <Link
        to={`/decisions/${decision.decision_id}`}
        className="mt-3 block text-xs text-indigo-600 hover:text-indigo-500"
      >
        View Full Details →
      </Link>
    </div>
  )
}

// =============================================================================
// Component: Difference Row
// =============================================================================
function DifferenceRow({ diff }: { diff: FieldDifference }) {
  const changeColors = {
    modified: 'bg-amber-100 text-amber-700',
    added: 'bg-green-100 text-green-700',
    removed: 'bg-red-100 text-red-700',
  }

  const formatValue = (value: any): string => {
    if (value === null || value === undefined) return '—'
    if (typeof value === 'object') return JSON.stringify(value, null, 2)
    return String(value)
  }

  return (
    <tr className="border-b hover:bg-gray-50">
      <td className="py-2 px-3 font-medium text-gray-900">{diff.field_name}</td>
      <td className="py-2 px-3 text-gray-600 font-mono text-xs max-w-xs truncate">
        {formatValue(diff.value_a)}
      </td>
      <td className="py-2 px-3 text-gray-600 font-mono text-xs max-w-xs truncate">
        {formatValue(diff.value_b)}
      </td>
      <td className="py-2 px-3">
        <span className={clsx('px-2 py-0.5 rounded text-xs', changeColors[diff.change_type])}>
          {diff.change_type}
        </span>
      </td>
    </tr>
  )
}
