/**
 * Relation Editor
 * Visual editor for managing decision relations and dependencies
 */

import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { clsx } from 'clsx'
import { decisionsApi, Decision, RelationType } from '../shared/api'
import { DOMAIN_COLORS, DOMAIN_LABELS } from '../shared/constants'

// =============================================================================
// Types
// =============================================================================

interface RelationEdge {
  source: string
  target: string
  type: RelationType
}


// =============================================================================
// Component
// =============================================================================

export default function RelationEditor() {
  const [selectedDecision, setSelectedDecision] = useState<Decision | null>(null)
  const [viewMode, setViewMode] = useState<'list' | 'graph'>('list')
  const [filterDomain, setFilterDomain] = useState('')

  // Fetch all decisions
  const { data: decisionsData, isLoading } = useQuery({
    queryKey: ['decisions-for-relations'],
    queryFn: () => decisionsApi.list({ limit: 1000 }),
  })

  const decisions = decisionsData?.decisions || []

  // Filter decisions
  const filteredDecisions = useMemo(() => {
    if (!filterDomain) return decisions
    return decisions.filter(d => (d.domain_id || (d as any).group_id) === filterDomain)
  }, [decisions, filterDomain])

  // Build relation edges for graph view
  const relationEdges = useMemo(() => {
    const edges: RelationEdge[] = []
    decisions.forEach(d => {
      d.relations?.forEach(rel => {
        edges.push({
          source: d.decision_id,
          target: rel.target_id,
          type: rel.type,
        })
      })
      // Also include supersedes as a relation
      if (d.supersedes) {
        edges.push({
          source: d.decision_id,
          target: d.supersedes,
          type: 'depends_on', // Supersedes implies dependency
        })
      }
    })
    return edges
  }, [decisions])

  // Count relations for a decision
  const getRelationCounts = (decision: Decision) => {
    const outgoing = decision.relations?.length || 0
    const incoming = relationEdges.filter(e => e.target === decision.decision_id).length
    return { outgoing, incoming, total: outgoing + incoming }
  }

  // Get related decisions for selected decision
  const relatedDecisions = useMemo(() => {
    if (!selectedDecision) return { outgoing: [], incoming: [] }

    const outgoing = selectedDecision.relations?.map(rel => ({
      decision: decisions.find(d => d.decision_id === rel.target_id),
      type: rel.type,
    })).filter(r => r.decision) || []

    const incoming = relationEdges
      .filter(e => e.target === selectedDecision.decision_id)
      .map(e => ({
        decision: decisions.find(d => d.decision_id === e.source),
        type: e.type,
      }))
      .filter(r => r.decision)

    return { outgoing, incoming }
  }, [selectedDecision, decisions, relationEdges])

  const uniqueDomains = [...new Set(decisions.map(d => (d.domain_id || (d as any).group_id)))]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Relation Editor</h1>
          <p className="mt-1 text-gray-600">
            Manage dependencies and relationships between decisions
          </p>
        </div>

        {/* View Toggle */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setViewMode('list')}
            className={clsx(
              'px-4 py-2 rounded-lg font-medium transition-colors',
              viewMode === 'list'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
          >
            List View
          </button>
          <button
            onClick={() => setViewMode('graph')}
            className={clsx(
              'px-4 py-2 rounded-lg font-medium transition-colors',
              viewMode === 'graph'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
          >
            Graph View
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total Decisions" value={decisions.length} icon="📄" />
        <StatCard label="Total Relations" value={relationEdges.length} icon="🔗" />
        <StatCard
          label="With Dependencies"
          value={decisions.filter(d => d.relations && d.relations.length > 0).length}
          icon="↗️"
        />
        <StatCard
          label="Supersedes Chains"
          value={decisions.filter(d => d.supersedes).length}
          icon="🔄"
        />
      </div>

      {/* Filter */}
      <div className="bg-white rounded-lg shadow-sm border p-4">
        <div className="flex flex-wrap items-center gap-4">
          <div>
            <label className="block text-sm text-gray-500 mb-1">Filter by Domain</label>
            <select
              value={filterDomain}
              onChange={(e) => setFilterDomain(e.target.value)}
              className="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">All Domains</option>
              {uniqueDomains.map(d => (
                <option key={d} value={d}>{d} - {DOMAIN_LABELS[d]}</option>
              ))}
            </select>
          </div>

          <div className="flex-1" />

          <Link
            to="/relationships"
            className="px-4 py-2 text-indigo-600 hover:text-indigo-800"
          >
            View Relationship Projection →
          </Link>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-12">
          <div className="animate-spin w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full mx-auto"></div>
          <p className="mt-2 text-gray-500">Loading decisions...</p>
        </div>
      )}

      {/* Main Content */}
      {!isLoading && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Decision List */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm border">
              <div className="p-4 border-b">
                <h3 className="font-semibold text-gray-900">
                  Decisions ({filteredDecisions.length})
                </h3>
              </div>
              <div className="divide-y max-h-[600px] overflow-y-auto">
                {filteredDecisions.map(decision => {
                  const counts = getRelationCounts(decision)
                  const isSelected = selectedDecision?.decision_id === decision.decision_id
                  return (
                    <button
                      key={decision.decision_id}
                      onClick={() => setSelectedDecision(decision)}
                      className={clsx(
                        'w-full p-3 text-left hover:bg-gray-50 transition-colors',
                        isSelected && 'bg-indigo-50 border-l-4 border-indigo-600'
                      )}
                    >
                      <div className="flex items-center gap-2">
                        <span
                          className="w-2 h-2 rounded-full"
                          style={{ backgroundColor: DOMAIN_COLORS[(decision.domain_id || (decision as any).group_id)] }}
                        />
                        <span className="font-mono text-sm text-gray-700">
                          {decision.decision_code || decision.decision_id.slice(0, 8)}
                        </span>
                        {counts.total > 0 && (
                          <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">
                            {counts.total}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mt-1 line-clamp-1">
                        {decision.statement}
                      </p>
                    </button>
                  )
                })}
              </div>
            </div>
          </div>

          {/* Detail Panel */}
          <div className="lg:col-span-2">
            {selectedDecision ? (
              <div className="space-y-4">
                {/* Selected Decision Card */}
                <div className="bg-white rounded-lg shadow-sm border p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <span
                          className="px-2 py-0.5 rounded text-xs text-white"
                          style={{ backgroundColor: DOMAIN_COLORS[selectedDecision.domain_id || (selectedDecision as any).group_id] }}
                        >
                          {selectedDecision.domain_id || (selectedDecision as any).group_id}
                        </span>
                        <span className="font-mono font-medium">
                          {selectedDecision.decision_code || selectedDecision.decision_id.slice(0, 8)}
                        </span>
                      </div>
                      <h3 className="mt-2 font-semibold text-gray-900">
                        {selectedDecision.statement}
                      </h3>
                    </div>
                    <Link
                      to={`/decisions/${selectedDecision.decision_id}`}
                      className="text-sm text-indigo-600 hover:text-indigo-800"
                    >
                      View Detail →
                    </Link>
                  </div>

                  {/* Supersedes */}
                  {selectedDecision.supersedes && (
                    <div className="mt-3 p-2 bg-amber-50 rounded border border-amber-200">
                      <span className="text-xs font-medium text-amber-700">SUPERSEDES:</span>
                      <span className="ml-2 font-mono text-sm text-amber-600">
                        {selectedDecision.supersedes.slice(0, 8)}...
                      </span>
                    </div>
                  )}
                </div>

                {/* Immutability Notice & Alternatives */}
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <span className="text-2xl">🔒</span>
                    <div>
                      <h4 className="font-medium text-amber-800">Immutability Constraint</h4>
                      <p className="text-sm text-amber-700 mt-1">
                        Per MANTRA-LAW-001, decisions are <strong>immutable</strong> once created.
                        Relations cannot be added or removed from existing decisions.
                      </p>
                      <div className="mt-3 space-y-2">
                        <p className="text-sm text-amber-700 font-medium">To add relations:</p>
                        <ul className="text-sm text-amber-600 list-disc list-inside space-y-1">
                          <li>Create a new decision that <strong>supersedes</strong> this one with the desired relations</li>
                          <li>Or specify relations when creating new decisions via the <Link to="/wizard" className="text-indigo-600 hover:underline">Decision Wizard</Link></li>
                        </ul>
                      </div>
                      <Link
                        to={`/wizard?supersedes=${selectedDecision.decision_id}`}
                        className="mt-3 inline-flex items-center gap-2 px-3 py-1.5 bg-amber-600 text-white text-sm rounded hover:bg-amber-700"
                      >
                        <span>Create Superseding Version</span>
                        <span>→</span>
                      </Link>
                    </div>
                  </div>
                </div>

                {/* Current Relations Summary */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-medium text-gray-700 mb-2">Current Relations</h4>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div className="text-center">
                      <div className="text-lg font-bold text-blue-600">
                        {selectedDecision.relations?.filter(r => r.type === 'depends_on').length || 0}
                      </div>
                      <div className="text-gray-500">depends_on</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-red-600">
                        {selectedDecision.relations?.filter(r => r.type === 'conflicts_with').length || 0}
                      </div>
                      <div className="text-gray-500">conflicts_with</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-green-600">
                        {selectedDecision.relations?.filter(r => r.type === 'informed_by').length || 0}
                      </div>
                      <div className="text-gray-500">informed_by</div>
                    </div>
                  </div>
                </div>

                {/* Outgoing Relations */}
                <div className="bg-white rounded-lg shadow-sm border p-4">
                  <h4 className="font-medium text-gray-900 mb-3">
                    Outgoing Relations ({relatedDecisions.outgoing.length})
                  </h4>
                  {relatedDecisions.outgoing.length > 0 ? (
                    <div className="space-y-2">
                      {relatedDecisions.outgoing.map(({ decision, type }) => (
                        <RelationCard
                          key={decision!.decision_id}
                          decision={decision!}
                          type={type}
                          direction="outgoing"
                          onClick={() => setSelectedDecision(decision!)}
                        />
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500 italic">No outgoing relations</p>
                  )}
                </div>

                {/* Incoming Relations */}
                <div className="bg-white rounded-lg shadow-sm border p-4">
                  <h4 className="font-medium text-gray-900 mb-3">
                    Incoming Relations ({relatedDecisions.incoming.length})
                  </h4>
                  {relatedDecisions.incoming.length > 0 ? (
                    <div className="space-y-2">
                      {relatedDecisions.incoming.map(({ decision, type }) => (
                        <RelationCard
                          key={decision!.decision_id}
                          decision={decision!}
                          type={type}
                          direction="incoming"
                          onClick={() => setSelectedDecision(decision!)}
                        />
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500 italic">No incoming relations</p>
                  )}
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm border p-12 text-center">
                <span className="text-4xl">🔗</span>
                <h3 className="mt-4 text-lg font-medium text-gray-900">Select a Decision</h3>
                <p className="mt-2 text-gray-500">
                  Click on a decision from the list to view and edit its relations
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Graph View (Simple visualization) */}
      {viewMode === 'graph' && !isLoading && (
        <div className="bg-white rounded-lg shadow-sm border p-4">
          <h3 className="font-semibold text-gray-900 mb-4">Relation Graph</h3>
          <div className="min-h-[400px] bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 flex items-center justify-center">
            <div className="text-center">
              <span className="text-4xl">🕸️</span>
              <p className="mt-2 text-gray-500">
                Interactive graph visualization coming soon
              </p>
              <p className="text-sm text-gray-400 mt-1">
                For now, use the Relationship Projection page for visual graph
              </p>
              <Link
                to="/relationships"
                className="mt-4 inline-block px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
              >
                View Relationship Graph →
              </Link>
            </div>
          </div>

          {/* Simple Stats about Graph */}
          <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {relationEdges.filter(e => e.type === 'depends_on').length}
              </div>
              <div className="text-blue-700">Dependencies</div>
            </div>
            <div className="text-center p-3 bg-red-50 rounded-lg">
              <div className="text-2xl font-bold text-red-600">
                {relationEdges.filter(e => e.type === 'conflicts_with').length}
              </div>
              <div className="text-red-700">Conflicts</div>
            </div>
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {relationEdges.filter(e => e.type === 'informed_by').length}
              </div>
              <div className="text-green-700">Informed By</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// =============================================================================
// Subcomponents
// =============================================================================

function StatCard({
  label,
  value,
  icon,
}: {
  label: string
  value: number
  icon: string
}) {
  return (
    <div className="bg-white rounded-lg shadow-sm border p-4">
      <div className="flex items-center justify-between">
        <span className="text-2xl">{icon}</span>
        <span className="text-2xl font-bold text-gray-900">{value}</span>
      </div>
      <p className="mt-1 text-sm text-gray-500">{label}</p>
    </div>
  )
}

function RelationCard({
  decision,
  type,
  direction,
  onClick,
}: {
  decision: Decision
  type: RelationType
  direction: 'incoming' | 'outgoing'
  onClick: () => void
}) {
  const typeColors = {
    depends_on: 'bg-blue-100 text-blue-700 border-blue-200',
    conflicts_with: 'bg-red-100 text-red-700 border-red-200',
    informed_by: 'bg-green-100 text-green-700 border-green-200',
  }

  const typeLabels = {
    depends_on: 'DEPENDS ON',
    conflicts_with: 'CONFLICTS WITH',
    informed_by: 'INFORMED BY',
  }

  const arrows = {
    incoming: '←',
    outgoing: '→',
  }

  return (
    <button
      onClick={onClick}
      className={clsx(
        'w-full p-3 rounded-lg border text-left transition-colors hover:shadow-sm',
        typeColors[type]
      )}
    >
      <div className="flex items-center gap-2">
        <span className="text-lg">{arrows[direction]}</span>
        <span className="text-xs font-bold uppercase">{typeLabels[type]}</span>
      </div>
      <div className="flex items-center gap-2 mt-1">
        <span
          className="w-2 h-2 rounded-full"
          style={{ backgroundColor: DOMAIN_COLORS[(decision.domain_id || (decision as any).group_id)] }}
        />
        <span className="font-mono text-sm">
          {decision.decision_code || decision.decision_id.slice(0, 8)}
        </span>
      </div>
      <p className="text-sm mt-1 line-clamp-1 opacity-75">
        {decision.statement}
      </p>
    </button>
  )
}
