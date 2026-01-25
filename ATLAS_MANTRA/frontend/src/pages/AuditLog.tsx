import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { auditApi, decisionsApi, AuditEntry, AuditMetadata } from '../shared/api'
import { useState } from 'react'
import { GROUP_LABELS, FEATURE_LABELS } from '../shared/constants'

// Helper to render typed metadata
function MetadataDisplay({ metadata }: { metadata: AuditMetadata }) {
  if (!metadata || typeof metadata !== 'object') return null

  const metaType = '_metadata_type' in metadata ? metadata._metadata_type : null

  if (metaType === 'ProposedMetadata') {
    const m = metadata as any
    return (
      <div className="flex gap-4 text-xs">
        <span className="text-gray-500">Proposal: <span className="font-mono">{m.proposal_id?.slice(0, 8)}...</span></span>
        <span className={m.validation_status === 'VALID' ? 'text-green-600' : 'text-red-600'}>
          {m.validation_status}
        </span>
        {m.violations_count > 0 && <span className="text-red-500">{m.violations_count} violations</span>}
      </div>
    )
  }

  if (metaType === 'StoredMetadata') {
    const m = metadata as any
    return (
      <div className="flex gap-4 text-xs">
        <span className="text-gray-500">v{m.version}</span>
        {m.supersedes && <span className="text-orange-600">supersedes {m.supersedes.slice(0, 8)}...</span>}
      </div>
    )
  }

  if (metaType === 'ChallengeMetadata') {
    const m = metadata as any
    return (
      <div className="flex gap-4 text-xs">
        <span className="text-orange-600">Challenged: {m.challenged_decision_id?.slice(0, 8)}...</span>
        <span className="text-gray-500 truncate max-w-xs">{m.challenge_rationale}</span>
      </div>
    )
  }

  if (metaType === 'CompareMetadata') {
    const m = metadata as any
    return (
      <div className="flex gap-4 text-xs">
        <span className="text-purple-600">vs {m.compared_with?.slice(0, 8)}...</span>
        <span className="text-gray-500">{m.differences_count} differences</span>
        {m.is_supersedes_chain && <span className="text-blue-500">in chain</span>}
      </div>
    )
  }

  if (metaType === 'ReadMetadata') {
    const m = metadata as any
    return (
      <div className="flex gap-4 text-xs">
        <span className="text-gray-500">{m.operation}</span>
        {m.chain_length && <span className="text-gray-400">{m.chain_length} versions</span>}
      </div>
    )
  }

  // Fallback for untyped metadata
  return (
    <div className="text-xs text-gray-400">
      {JSON.stringify(metadata).slice(0, 50)}...
    </div>
  )
}

const EVENT_TYPE_COLORS: Record<string, string> = {
  DECISION_STORED: 'bg-green-100 text-green-800',
  DECISION_PROPOSED: 'bg-blue-100 text-blue-800',
  DECISION_READ: 'bg-gray-100 text-gray-800',
  DECISION_COMPARED: 'bg-purple-100 text-purple-800',
  CHALLENGE_CREATED: 'bg-orange-100 text-orange-800',
  DECISION_VALIDATED: 'bg-cyan-100 text-cyan-800',
}

const EVENT_TYPE_LABELS: Record<string, string> = {
  DECISION_STORED: 'Stored',
  DECISION_PROPOSED: 'Proposed',
  DECISION_READ: 'Read',
  DECISION_COMPARED: 'Compared',
  CHALLENGE_CREATED: 'Challenged',
  DECISION_VALIDATED: 'Validated',
}

function formatTimestamp(timestamp: string) {
  const date = new Date(timestamp)
  return date.toLocaleString()
}

function formatRelativeTime(timestamp: string) {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (days > 0) return `${days}d ago`
  if (hours > 0) return `${hours}h ago`
  if (minutes > 0) return `${minutes}m ago`
  return 'just now'
}

// Component untuk menampilkan detail decision saat expand
function DecisionDetail({ decisionId }: { decisionId: string }) {
  const { data: decision, isLoading, error } = useQuery({
    queryKey: ['decision', decisionId],
    queryFn: () => decisionsApi.get(decisionId),
    staleTime: 60000, // Cache for 1 minute
  })

  if (isLoading) {
    return <div className="text-gray-500 text-sm py-2">Loading decision...</div>
  }

  if (error || !decision) {
    return <div className="text-red-500 text-sm py-2">Failed to load decision</div>
  }

  return (
    <div className="space-y-3">
      {/* Header with Decision Code */}
      <div className="flex items-center gap-3">
        {decision.decision_code && (
          <span className="font-mono text-sm text-indigo-600 font-semibold">{decision.decision_code}</span>
        )}
        <span className="text-sm font-medium text-gray-900">{GROUP_LABELS[decision.group_id]}</span>
        <span className="text-gray-300">›</span>
        <span className="text-sm text-gray-600">{FEATURE_LABELS[decision.feature_id] || decision.feature_id}</span>
        <span className={`ml-auto px-2 py-0.5 rounded text-xs ${
          decision.blast_radius === 'CRITICAL' ? 'bg-red-100 text-red-800' :
          decision.blast_radius === 'HIGH' ? 'bg-orange-100 text-orange-800' :
          decision.blast_radius === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
          'bg-green-100 text-green-800'
        }`}>
          {decision.blast_radius}
        </span>
      </div>

      {/* Statement */}
      <div>
        <div className="text-xs text-gray-500 uppercase mb-1">Statement</div>
        <div className="text-sm text-gray-900 bg-white border rounded p-2">
          {decision.statement}
        </div>
      </div>

      {/* Rationale */}
      <div>
        <div className="text-xs text-gray-500 uppercase mb-1">Rationale</div>
        <div className="text-sm text-gray-700 bg-white border rounded p-2 max-h-32 overflow-y-auto">
          {decision.rationale}
        </div>
      </div>

      {/* Constraints (if any) */}
      {decision.constraints && decision.constraints.length > 0 && (
        <div>
          <div className="text-xs text-gray-500 uppercase mb-1">Constraints ({decision.constraints.length})</div>
          <div className="space-y-1">
            {decision.constraints.slice(0, 3).map((c: any) => (
              <div key={c.constraint_id} className="text-xs bg-white border rounded px-2 py-1 flex items-center gap-2">
                <span className={`px-1.5 py-0.5 rounded ${
                  c.type === 'PROHIBITION' ? 'bg-red-50 text-red-700' :
                  c.type === 'REQUIREMENT' ? 'bg-blue-50 text-blue-700' :
                  'bg-yellow-50 text-yellow-700'
                }`}>{c.type}</span>
                <span className="text-gray-600 truncate">{c.statement}</span>
              </div>
            ))}
            {decision.constraints.length > 3 && (
              <div className="text-xs text-gray-400">+{decision.constraints.length - 3} more</div>
            )}
          </div>
        </div>
      )}

      {/* Footer with link */}
      <div className="flex items-center justify-between pt-2 border-t">
        <div className="text-xs text-gray-500">
          <span className="font-mono">{decision.decision_code || decision.decision_id.slice(0, 12) + '...'}</span>
          <span className="mx-2">•</span>
          <span>v{decision.version}</span>
          {decision.supersedes && (
            <>
              <span className="mx-2">•</span>
              <span className="text-orange-600">supersedes {decision.supersedes.slice(0, 8)}...</span>
            </>
          )}
        </div>
        <Link
          to={`/decisions/${decision.decision_id}`}
          className="text-xs text-indigo-600 hover:text-indigo-500"
        >
          View Full Detail →
        </Link>
      </div>
    </div>
  )
}

export default function AuditLog() {
  const [limit, setLimit] = useState(50)
  const [filterType, setFilterType] = useState<string>('')
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set())

  const toggleRow = (eventId: string) => {
    setExpandedRows(prev => {
      const next = new Set(prev)
      if (next.has(eventId)) {
        next.delete(eventId)
      } else {
        next.add(eventId)
      }
      return next
    })
  }

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['audit', limit, filterType],
    queryFn: () => auditApi.list({
      limit,
      ...(filterType && { event_type: filterType })
    }),
    refetchInterval: 10000,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading audit log...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Audit Log</h1>
          <p className="mt-1 text-gray-600">
            Complete audit trail of all operations • {data?.total_count ?? 0} entries
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border p-4">
        <div className="flex items-center gap-4">
          <div>
            <label className="text-sm text-gray-600 block mb-1">Event Type</label>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-3 py-2 border rounded-lg text-sm"
            >
              <option value="">All Events</option>
              <option value="DECISION_STORED">Stored</option>
              <option value="DECISION_PROPOSED">Proposed</option>
              <option value="DECISION_COMPARED">Compared</option>
              <option value="CHALLENGE_CREATED">Challenged</option>
              <option value="DECISION_READ">Read</option>
            </select>
          </div>
          <div>
            <label className="text-sm text-gray-600 block mb-1">Show</label>
            <select
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="px-3 py-2 border rounded-lg text-sm"
            >
              <option value={20}>20 entries</option>
              <option value={50}>50 entries</option>
              <option value={100}>100 entries</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-10"></th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Event</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actor</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Decision</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Metadata</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data?.entries?.map((entry: AuditEntry) => {
                const isExpanded = expandedRows.has(entry.event_id)
                return (
                  <>
                    <tr key={entry.event_id} className={`hover:bg-gray-50 ${isExpanded ? 'bg-indigo-50' : ''}`}>
                      <td className="px-4 py-2 whitespace-nowrap">
                        {entry.decision_id && (
                          <button
                            onClick={() => toggleRow(entry.event_id)}
                            className="text-gray-400 hover:text-gray-600 p-1"
                            title={isExpanded ? 'Collapse' : 'Expand'}
                          >
                            <svg className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-90' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                          </button>
                        )}
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500" title={formatTimestamp(entry.timestamp)}>
                        {formatRelativeTime(entry.timestamp)}
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${EVENT_TYPE_COLORS[entry.event_type] || 'bg-gray-100 text-gray-800'}`}>
                          {EVENT_TYPE_LABELS[entry.event_type] || entry.event_type}
                        </span>
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                        {entry.actor}
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap">
                        <span className={`px-1.5 py-0.5 rounded text-xs ${entry.actor_type === 'human' ? 'bg-green-50 text-green-700' : 'bg-yellow-50 text-yellow-700'}`}>
                          {entry.actor_type}
                        </span>
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap">
                        {entry.decision_id ? (
                          <Link
                            to={`/decisions/${entry.decision_id}`}
                            className="text-indigo-600 hover:text-indigo-500 font-mono text-xs"
                          >
                            {entry.decision_id.slice(0, 8)}...
                          </Link>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap">
                        <MetadataDisplay metadata={entry.metadata} />
                      </td>
                    </tr>
                    {isExpanded && entry.decision_id && (
                      <tr key={`${entry.event_id}-detail`} className="bg-gray-50">
                        <td colSpan={7} className="px-4 py-4">
                          <div className="ml-8 mr-4">
                            <DecisionDetail decisionId={entry.decision_id} />
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                )
              })}
            </tbody>
          </table>

          {(!data?.entries || data.entries.length === 0) && (
            <div className="p-8 text-center text-gray-500">
              No audit entries found
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
