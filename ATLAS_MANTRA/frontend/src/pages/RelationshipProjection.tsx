/**
 * Relationship Projection - Force-Directed Graph
 *
 * Primary view: Force-directed graph showing typed relations
 * - depends_on (blue solid line)
 * - conflicts_with (red dashed line)
 * - informed_by (green dotted line)
 * - supersedes (amber line)
 *
 * Per user requirement: Graph is the truth model, filters provide cognitive safety.
 */

import { useQuery } from '@tanstack/react-query'
import { useState, useEffect, useRef, useMemo, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { api, Decision, Relation } from '../shared/api'
import {
  GROUPS,
  GROUP_LABELS,
  GROUP_COLORS,
  RELATION_LABELS,
  RELATION_EDGE_STYLES,
} from '../shared/constants'

// =============================================================================
// Types for Graph
// =============================================================================

interface GraphNode {
  id: string
  code: string
  group: string
  feature: string
  statement: string
  x: number
  y: number
  vx: number
  vy: number
  fx?: number | null
  fy?: number | null
}

interface GraphEdge {
  source: string
  target: string
  type: 'depends_on' | 'conflicts_with' | 'informed_by' | 'supersedes'
}

// =============================================================================
// Force Simulation Hook
// =============================================================================

function useForceSimulation(
  nodes: GraphNode[],
  edges: GraphEdge[],
  width: number,
  height: number
) {
  const [positions, setPositions] = useState<Map<string, { x: number; y: number }>>(new Map())
  const animationRef = useRef<number>()
  const nodesRef = useRef<GraphNode[]>([])

  useEffect(() => {
    if (nodes.length === 0) return

    const groupPositions: Record<string, { cx: number; cy: number }> = {
      'INT': { cx: width * 0.25, cy: height * 0.25 },
      'ARCH': { cx: width * 0.75, cy: height * 0.25 },
      'CTL': { cx: width * 0.25, cy: height * 0.75 },
      'EVO': { cx: width * 0.75, cy: height * 0.75 },
    }

    const initializedNodes = nodes.map(node => {
      const groupPos = groupPositions[node.group] || { cx: width / 2, cy: height / 2 }
      const angle = Math.random() * Math.PI * 2
      const radius = 50 + Math.random() * 80
      return {
        ...node,
        x: groupPos.cx + Math.cos(angle) * radius,
        y: groupPos.cy + Math.sin(angle) * radius,
        vx: 0,
        vy: 0,
      }
    })

    nodesRef.current = initializedNodes
    updatePositions()
  }, [nodes, width, height])

  const tick = useCallback(() => {
    const nodeMap = new Map(nodesRef.current.map(n => [n.id, n]))
    const alpha = 0.1
    const repelForce = 500
    const linkDistance = 120

    nodesRef.current.forEach(node => {
      if (node.fx !== undefined && node.fx !== null) {
        node.x = node.fx
        node.y = node.fy!
        node.vx = 0
        node.vy = 0
        return
      }

      // Center gravity
      node.vx += (width / 2 - node.x) * 0.005
      node.vy += (height / 2 - node.y) * 0.005

      // Group center gravity
      const groupCenters: Record<string, { cx: number; cy: number }> = {
        'INT': { cx: width * 0.25, cy: height * 0.25 },
        'ARCH': { cx: width * 0.75, cy: height * 0.25 },
        'CTL': { cx: width * 0.25, cy: height * 0.75 },
        'EVO': { cx: width * 0.75, cy: height * 0.75 },
      }
      const gc = groupCenters[node.group]
      if (gc) {
        node.vx += (gc.cx - node.x) * 0.015
        node.vy += (gc.cy - node.y) * 0.015
      }

      // Repulsion
      nodesRef.current.forEach(other => {
        if (other.id === node.id) return
        const dx = node.x - other.x
        const dy = node.y - other.y
        const dist = Math.sqrt(dx * dx + dy * dy) || 1
        const force = repelForce / (dist * dist)
        node.vx += (dx / dist) * force * alpha
        node.vy += (dy / dist) * force * alpha
      })
    })

    // Link forces
    edges.forEach(edge => {
      const source = nodeMap.get(edge.source)
      const target = nodeMap.get(edge.target)
      if (!source || !target) return

      const dx = target.x - source.x
      const dy = target.y - source.y
      const dist = Math.sqrt(dx * dx + dy * dy) || 1
      const force = (dist - linkDistance) * 0.05 * alpha

      if (source.fx === undefined || source.fx === null) {
        source.vx += (dx / dist) * force
        source.vy += (dy / dist) * force
      }
      if (target.fx === undefined || target.fx === null) {
        target.vx -= (dx / dist) * force
        target.vy -= (dy / dist) * force
      }
    })

    // Apply velocity
    nodesRef.current.forEach(node => {
      if (node.fx !== undefined && node.fx !== null) return
      node.vx *= 0.9
      node.vy *= 0.9
      node.x += node.vx
      node.y += node.vy
      node.x = Math.max(40, Math.min(width - 40, node.x))
      node.y = Math.max(50, Math.min(height - 40, node.y))
    })

    updatePositions()
  }, [edges, width, height])

  const updatePositions = useCallback(() => {
    const newPositions = new Map<string, { x: number; y: number }>()
    nodesRef.current.forEach(node => {
      newPositions.set(node.id, { x: node.x, y: node.y })
    })
    setPositions(newPositions)
  }, [])

  useEffect(() => {
    let frameCount = 0
    const maxFrames = 300

    const animate = () => {
      if (frameCount < maxFrames) {
        tick()
        frameCount++
        animationRef.current = requestAnimationFrame(animate)
      }
    }

    animate()

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [tick])

  const startDrag = useCallback((id: string, x: number, y: number) => {
    const node = nodesRef.current.find(n => n.id === id)
    if (node) {
      node.fx = x
      node.fy = y
    }
  }, [])

  const drag = useCallback((id: string, x: number, y: number) => {
    const node = nodesRef.current.find(n => n.id === id)
    if (node) {
      node.fx = x
      node.fy = y
      node.x = x
      node.y = y
      updatePositions()
    }
  }, [updatePositions])

  const endDrag = useCallback((id: string) => {
    const node = nodesRef.current.find(n => n.id === id)
    if (node) {
      node.fx = null
      node.fy = null
    }
  }, [])

  return { positions, startDrag, drag, endDrag }
}

// =============================================================================
// Main Component
// =============================================================================

export default function RelationshipProjection() {
  const [filterGroup, setFilterGroup] = useState<string>('')
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [hoveredNode, setHoveredNode] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'graph' | 'matrix' | 'list'>('graph')
  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 })

  const { data, isLoading } = useQuery({
    queryKey: ['decisions'],
    queryFn: () => api.get('/api/v1/decisions?limit=100').then(r => r.data),
  })

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect()
        setDimensions({ width: rect.width || 800, height: 550 })
      }
    }

    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [])

  const { nodes, edges, decisionMap, stats } = useMemo(() => {
    if (!data?.decisions) return { nodes: [], edges: [], decisionMap: new Map(), stats: { total: 0, relations: 0, crossGroup: 0 } }

    const decisions: Decision[] = data.decisions
    const decisionMap = new Map<string, Decision>(decisions.map(d => [d.decision_id, d]))

    const filteredDecisions = filterGroup
      ? decisions.filter(d => d.group_id === filterGroup)
      : decisions

    const nodes: GraphNode[] = filteredDecisions.map(d => ({
      id: d.decision_id,
      code: d.decision_code || d.decision_id.slice(0, 8),
      group: d.group_id,
      feature: d.feature_id,
      statement: d.statement,
      x: 0, y: 0, vx: 0, vy: 0,
    }))

    const nodeIds = new Set(nodes.map(n => n.id))
    const edges: GraphEdge[] = []
    let crossGroupCount = 0

    filteredDecisions.forEach(d => {
      // Typed relations
      if (d.relations && Array.isArray(d.relations)) {
        d.relations.forEach((rel: Relation) => {
          if (nodeIds.has(rel.target_id)) {
            edges.push({
              source: d.decision_id,
              target: rel.target_id,
              type: rel.type as GraphEdge['type'],
            })
            const target = decisionMap.get(rel.target_id)
            if (target && target.group_id !== d.group_id) crossGroupCount++
          }
        })
      }

      // Legacy related_decisions
      if (d.related_decisions && d.related_decisions.length > 0) {
        d.related_decisions.forEach(targetId => {
          if (nodeIds.has(targetId) && !edges.some(e => e.source === d.decision_id && e.target === targetId)) {
            edges.push({ source: d.decision_id, target: targetId, type: 'depends_on' })
            const target = decisionMap.get(targetId)
            if (target && target.group_id !== d.group_id) crossGroupCount++
          }
        })
      }

      // Supersedes
      if (d.supersedes && nodeIds.has(d.supersedes)) {
        edges.push({ source: d.decision_id, target: d.supersedes, type: 'supersedes' })
      }
    })

    return {
      nodes,
      edges,
      decisionMap,
      stats: { total: nodes.length, relations: edges.length, crossGroup: crossGroupCount }
    }
  }, [data?.decisions, filterGroup])

  const { positions, startDrag, drag, endDrag } = useForceSimulation(nodes, edges, dimensions.width, dimensions.height)

  const [isDragging, setIsDragging] = useState(false)
  const [dragNode, setDragNode] = useState<string | null>(null)

  const handleMouseDown = (nodeId: string, e: React.MouseEvent) => {
    e.preventDefault()
    setIsDragging(true)
    setDragNode(nodeId)
    const rect = svgRef.current?.getBoundingClientRect()
    if (rect) startDrag(nodeId, e.clientX - rect.left, e.clientY - rect.top)
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging && dragNode) {
      const rect = svgRef.current?.getBoundingClientRect()
      if (rect) drag(dragNode, e.clientX - rect.left, e.clientY - rect.top)
    }
  }

  const handleMouseUp = () => {
    if (dragNode) endDrag(dragNode)
    setIsDragging(false)
    setDragNode(null)
  }

  // Matrix data
  const matrixData = useMemo(() => {
    const matrix: Record<string, Record<string, { count: number; types: Set<string> }>> = {}
    GROUPS.forEach(g1 => {
      matrix[g1] = {}
      GROUPS.forEach(g2 => { matrix[g1][g2] = { count: 0, types: new Set() } })
    })

    edges.forEach(edge => {
      const s = nodes.find(n => n.id === edge.source)
      const t = nodes.find(n => n.id === edge.target)
      if (s && t) {
        matrix[s.group][t.group].count++
        matrix[s.group][t.group].types.add(edge.type)
      }
    })

    return matrix
  }, [edges, nodes])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Relationship Graph</h1>
          <p className="mt-1 text-gray-600">
            {stats.total} decisions · {stats.relations} relations · {stats.crossGroup} cross-group
          </p>
        </div>
        <div className="flex gap-2">
          {(['graph', 'matrix', 'list'] as const).map(mode => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                viewMode === mode ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {mode.charAt(0).toUpperCase() + mode.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Filters & Legend */}
      <div className="bg-white rounded-lg shadow-sm border p-4">
        <div className="flex flex-wrap gap-4 items-center">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Filter Group</label>
            <select
              value={filterGroup}
              onChange={e => setFilterGroup(e.target.value)}
              className="px-3 py-1.5 border rounded text-sm focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">All Groups</option>
              {GROUPS.map(g => (
                <option key={g} value={g}>{g}: {GROUP_LABELS[g]}</option>
              ))}
            </select>
          </div>

          <div className="flex-1 flex flex-wrap gap-4 justify-end text-xs">
            {Object.entries(RELATION_LABELS).map(([type, label]) => (
              <div key={type} className="flex items-center gap-1.5">
                <svg width="20" height="8">
                  <line x1="0" y1="4" x2="20" y2="4"
                    stroke={RELATION_EDGE_STYLES[type]?.stroke || '#666'}
                    strokeWidth="2"
                    strokeDasharray={RELATION_EDGE_STYLES[type]?.strokeDasharray}
                  />
                </svg>
                <span className="text-gray-600">{label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Graph View */}
      {viewMode === 'graph' && (
        <div ref={containerRef} className="bg-white rounded-lg shadow-sm border overflow-hidden">
          <svg
            ref={svgRef}
            width={dimensions.width}
            height={dimensions.height}
            className="cursor-move"
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
          >
            {/* Group Labels */}
            {!filterGroup && GROUPS.map((g, i) => {
              const pos = [
                { x: dimensions.width * 0.25, y: 24 },
                { x: dimensions.width * 0.75, y: 24 },
                { x: dimensions.width * 0.25, y: dimensions.height - 16 },
                { x: dimensions.width * 0.75, y: dimensions.height - 16 },
              ][i]
              return (
                <text key={g} x={pos.x} y={pos.y} textAnchor="middle"
                  fill={GROUP_COLORS[g]} className="text-xs font-semibold">
                  {g}: {GROUP_LABELS[g]}
                </text>
              )
            })}

            {/* Edges */}
            {edges.map((edge, i) => {
              const sp = positions.get(edge.source)
              const tp = positions.get(edge.target)
              if (!sp || !tp) return null

              const style = RELATION_EDGE_STYLES[edge.type] || { stroke: '#666' }
              const isHighlighted = hoveredNode === edge.source || hoveredNode === edge.target ||
                                   selectedNode === edge.source || selectedNode === edge.target

              // Calculate arrow position
              const dx = tp.x - sp.x
              const dy = tp.y - sp.y
              const len = Math.sqrt(dx * dx + dy * dy)
              const nodeRadius = 18
              const endX = tp.x - (dx / len) * nodeRadius
              const endY = tp.y - (dy / len) * nodeRadius

              return (
                <g key={i}>
                  <line x1={sp.x} y1={sp.y} x2={endX} y2={endY}
                    stroke={style.stroke}
                    strokeWidth={isHighlighted ? 2.5 : 1.5}
                    strokeDasharray={style.strokeDasharray}
                    opacity={isHighlighted ? 1 : 0.5}
                    markerEnd={`url(#arrow-${edge.type})`}
                  />
                </g>
              )
            })}

            {/* Arrow markers */}
            <defs>
              {Object.entries(RELATION_EDGE_STYLES).map(([type, style]) => (
                <marker key={type} id={`arrow-${type}`}
                  markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                  <polygon points="0 0, 8 3, 0 6" fill={style.stroke} />
                </marker>
              ))}
            </defs>

            {/* Nodes */}
            {nodes.map(node => {
              const pos = positions.get(node.id)
              if (!pos) return null

              const isSelected = selectedNode === node.id
              const isHovered = hoveredNode === node.id
              const nodeColor = GROUP_COLORS[node.group] || '#666'

              return (
                <g key={node.id}
                  transform={`translate(${pos.x}, ${pos.y})`}
                  onMouseDown={e => handleMouseDown(node.id, e)}
                  onMouseEnter={() => setHoveredNode(node.id)}
                  onMouseLeave={() => setHoveredNode(null)}
                  onClick={() => setSelectedNode(isSelected ? null : node.id)}
                  className="cursor-pointer"
                >
                  <circle r={isSelected || isHovered ? 22 : 18}
                    fill={nodeColor}
                    opacity={isSelected || isHovered ? 1 : 0.85}
                    stroke={isSelected ? '#1F2937' : isHovered ? '#4B5563' : 'none'}
                    strokeWidth={2}
                  />
                  <text y={1} textAnchor="middle" dominantBaseline="middle"
                    fill="white" className="text-[10px] font-bold pointer-events-none">
                    {node.feature}
                  </text>
                </g>
              )
            })}
          </svg>

          {/* Selected Node Detail */}
          {selectedNode && decisionMap.get(selectedNode) && (
            <div className="border-t p-4 bg-gray-50">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <Link to={`/decisions/${selectedNode}`}
                    className="text-lg font-semibold text-indigo-600 hover:text-indigo-500">
                    {decisionMap.get(selectedNode)!.decision_code || selectedNode.slice(0, 12)}
                  </Link>
                  <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                    {decisionMap.get(selectedNode)!.statement}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-2 text-xs">
                    <span className="px-2 py-0.5 rounded" style={{ backgroundColor: GROUP_COLORS[decisionMap.get(selectedNode)!.group_id] + '20', color: GROUP_COLORS[decisionMap.get(selectedNode)!.group_id] }}>
                      {decisionMap.get(selectedNode)!.group_id}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-gray-100 text-gray-700">
                      {decisionMap.get(selectedNode)!.feature_id}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-gray-100 text-gray-700">
                      {decisionMap.get(selectedNode)!.blast_radius}
                    </span>
                  </div>
                </div>
                <button onClick={() => setSelectedNode(null)} className="text-gray-400 hover:text-gray-600 ml-4">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Matrix View */}
      {viewMode === 'matrix' && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Group × Group Relationship Matrix</h3>
          <table className="w-full text-sm">
            <thead>
              <tr>
                <th className="text-left p-2 text-gray-500 font-medium">From ↓ / To →</th>
                {GROUPS.map(g => (
                  <th key={g} className="p-2 text-center font-medium" style={{ color: GROUP_COLORS[g] }}>{g}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {GROUPS.map(from => (
                <tr key={from}>
                  <td className="p-2 font-medium" style={{ color: GROUP_COLORS[from] }}>{from}</td>
                  {GROUPS.map(to => {
                    const cell = matrixData[from][to]
                    const isCross = from !== to
                    return (
                      <td key={to} className={`p-2 text-center ${cell.count > 0 ? (isCross ? 'bg-amber-50' : 'bg-blue-50') : ''}`}>
                        {cell.count > 0 ? (
                          <div>
                            <span className="font-semibold">{cell.count}</span>
                            <div className="text-[10px] text-gray-400">
                              {Array.from(cell.types).map(t => t.slice(0, 1).toUpperCase()).join(',')}
                            </div>
                          </div>
                        ) : <span className="text-gray-300">-</span>}
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* List View */}
      {viewMode === 'list' && (
        <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Source</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Relation</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Target</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Cross-Group</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {edges.map((edge, i) => {
                const s = nodes.find(n => n.id === edge.source)
                const t = nodes.find(n => n.id === edge.target)
                if (!s || !t) return null
                const isCross = s.group !== t.group

                return (
                  <tr key={i} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <Link to={`/decisions/${edge.source}`} className="text-indigo-600 hover:text-indigo-500 font-mono text-xs">
                        {s.code}
                      </Link>
                      <span className="ml-2 text-[10px]" style={{ color: GROUP_COLORS[s.group] }}>[{s.group}]</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded text-xs font-medium"
                        style={{ backgroundColor: RELATION_EDGE_STYLES[edge.type]?.stroke + '20', color: RELATION_EDGE_STYLES[edge.type]?.stroke }}>
                        {RELATION_LABELS[edge.type]}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <Link to={`/decisions/${edge.target}`} className="text-indigo-600 hover:text-indigo-500 font-mono text-xs">
                        {t.code}
                      </Link>
                      <span className="ml-2 text-[10px]" style={{ color: GROUP_COLORS[t.group] }}>[{t.group}]</span>
                    </td>
                    <td className="px-4 py-3">
                      {isCross ? <span className="px-2 py-0.5 rounded text-xs bg-amber-100 text-amber-800">Yes</span> : <span className="text-gray-400">-</span>}
                    </td>
                  </tr>
                )
              })}
              {edges.length === 0 && (
                <tr><td colSpan={4} className="px-4 py-8 text-center text-gray-500">No relations found</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Note */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs">
        <p className="text-amber-800">
          <span className="font-medium">Graph = Truth Model.</span>{' '}
          Filters provide cognitive safety. Tree/Matrix/List are projections, not the model itself.
        </p>
      </div>
    </div>
  )
}
