import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../shared/api'
import { GROUP_LABELS, FEATURE_LABELS } from '../shared/constants'

export default function DecisionDetail() {
  const { id } = useParams<{ id: string }>()

  const { data: decision, isLoading, error } = useQuery({
    queryKey: ['decision', id],
    queryFn: () => api.get(`/api/v1/decisions/${id}`).then(r => r.data),
    enabled: !!id,
  })

  if (isLoading) {
    return <div className="text-gray-500">Loading decision...</div>
  }

  if (error || !decision) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl text-red-600">Decision not found</h2>
        <Link to="/decisions" className="text-indigo-600 mt-4 inline-block">
          Back to decisions
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-4">
        <Link to="/decisions" className="text-gray-500 hover:text-gray-700">
          &larr; Back
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">Decision Detail</h1>
      </div>

      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="grid grid-cols-2 gap-6">
          <div>
            <label className="text-sm text-gray-500">Decision ID</label>
            <p className="text-gray-900 font-mono">{decision.decision_id}</p>
          </div>
          <div>
            <label className="text-sm text-gray-500">Version</label>
            <p className="text-gray-900 font-mono">{decision.version}</p>
          </div>
          <div>
            <label className="text-sm text-gray-500">Group</label>
            <p className="text-indigo-600">{GROUP_LABELS[decision.group_id]}</p>
            <p className="text-xs text-gray-400">Group {decision.group_id.split('-')[1]}</p>
          </div>
          <div>
            <label className="text-sm text-gray-500">Feature</label>
            <p className="text-indigo-600">{decision.feature_id}</p>
            <p className="text-xs text-gray-500">{FEATURE_LABELS[decision.feature_id]}</p>
          </div>
          <div>
            <label className="text-sm text-gray-500">Scope</label>
            <p className="text-gray-900">{decision.scope}</p>
          </div>
          <div>
            <label className="text-sm text-gray-500">Blast Radius</label>
            <p className="text-gray-900">{decision.blast_radius}</p>
          </div>
          <div>
            <label className="text-sm text-gray-500">Created By</label>
            <p className="text-gray-900">{decision.created_by || 'Unknown'}</p>
          </div>
          <div>
            <label className="text-sm text-gray-500">Created At</label>
            <p className="text-gray-900">
              {decision.created_at ? new Date(decision.created_at).toLocaleString() : 'Unknown'}
            </p>
          </div>
        </div>
      </div>

      {/* Version Chain */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="font-semibold text-gray-900 mb-3">Version Chain</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-gray-500">Supersedes</label>
            {decision.supersedes ? (
              <Link
                to={`/decisions/${decision.supersedes}`}
                className="text-indigo-600 hover:text-indigo-500 font-mono block"
              >
                {decision.supersedes.slice(0, 8)}...
              </Link>
            ) : (
              <p className="text-gray-400">None (original decision)</p>
            )}
          </div>
          <div>
            <label className="text-sm text-gray-500">Related Decisions</label>
            {decision.related_decisions?.length > 0 ? (
              <div className="space-y-1">
                {decision.related_decisions.map((rel: string) => (
                  <Link
                    key={rel}
                    to={`/decisions/${rel}`}
                    className="text-indigo-600 hover:text-indigo-500 font-mono block text-sm"
                  >
                    {rel.slice(0, 8)}...
                  </Link>
                ))}
              </div>
            ) : (
              <p className="text-gray-400">None</p>
            )}
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="font-semibold text-gray-900 mb-3">Statement</h3>
        <p className="text-gray-700">{decision.statement}</p>
      </div>

      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="font-semibold text-gray-900 mb-3">Rationale</h3>
        <p className="text-gray-700">{decision.rationale}</p>
      </div>

      {decision.constraints?.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="font-semibold text-gray-900 mb-3">Constraints</h3>
          <div className="space-y-3">
            {decision.constraints.map((c: any, i: number) => (
              <div key={i} className="p-3 bg-gray-50 rounded">
                <div className="flex items-center space-x-2 mb-1">
                  <span className="text-sm text-indigo-600">{c.constraint_id}</span>
                  <span className="text-xs text-gray-500">{c.type}</span>
                </div>
                <p className="text-sm text-gray-700">{c.statement}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {decision.invariants?.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="font-semibold text-gray-900 mb-3">Invariants</h3>
          <ul className="list-disc list-inside space-y-1">
            {decision.invariants.map((inv: string, i: number) => (
              <li key={i} className="text-gray-700">{inv}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
