import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../shared/api'
import { GROUP_LABELS, FEATURE_LABELS } from '../shared/constants'

export default function DecisionList() {
  const { data, isLoading } = useQuery({
    queryKey: ['decisions'],
    queryFn: () => api.get('/api/v1/decisions').then(r => r.data),
  })

  if (isLoading) {
    return <div className="text-gray-500">Loading decisions...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Decisions</h1>
          <p className="mt-1 text-gray-600">
            Total: {data?.total_count ?? 0} decisions
          </p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Decision ID</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Group</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Feature</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Statement</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Version</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Supersedes</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data?.decisions?.map((decision: any) => (
              <tr key={decision.decision_id} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3">
                  <Link
                    to={`/decisions/${decision.decision_id}`}
                    className="text-indigo-600 hover:text-indigo-500 font-mono text-sm"
                  >
                    {decision.decision_id.slice(0, 8)}...
                  </Link>
                </td>
                <td className="px-4 py-3 text-sm">
                  <span className="text-gray-700">{GROUP_LABELS[decision.group_id]}</span>
                  <span className="text-xs text-gray-400 block">Group {decision.group_id.split('-')[1]}</span>
                </td>
                <td className="px-4 py-3 text-sm">
                  <span className="text-gray-700">{decision.feature_id}</span>
                  <span className="text-xs text-gray-500 block">{FEATURE_LABELS[decision.feature_id]}</span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-600 max-w-md truncate">
                  {decision.statement}
                </td>
                <td className="px-4 py-3">
                  <span className="px-2 py-1 bg-gray-100 rounded text-xs text-gray-700 font-mono">
                    {decision.version}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-500 font-mono">
                  {decision.supersedes ? decision.supersedes.slice(0, 8) + '...' : '-'}
                </td>
              </tr>
            ))}
            {(!data?.decisions || data.decisions.length === 0) && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                  No decisions found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
