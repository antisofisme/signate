/**
 * MCP Dashboard - ATLAS_MANTRA
 *
 * Admin interface for MCP (Model Context Protocol) features:
 * - List available agents and their configurations
 * - View task checklists by type
 * - Validate proposed actions
 * - Query task context
 */

import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { clsx } from 'clsx'

const API_BASE = import.meta.env.VITE_API_URL || 'http://31.97.111.175:8002'

// Types
interface Agent {
  id: string
  name: string
  description: string
  version: string
  category: string
  keywords: string[]
  groups: string[]
  features: string[]
}

interface AgentsResponse {
  agents: Agent[]
  total: number
  category_filter?: string
}

// Checklist item for MCP checklist API
interface ChecklistItem {
  id: string
  step: string
  command?: string | null
  blocking: boolean
}

interface ChecklistPhases {
  pre_deploy: ChecklistItem[]
  deploy: ChecklistItem[]
  post_deploy: ChecklistItem[]
}

interface ChecklistResponse {
  task_type: string
  agent: {
    id: string
    name: string
  }
  target: string | null
  phase: string
  checklist: ChecklistPhases
  critical_rules: string[]
  total_steps: number
  error?: string | null
}

interface ValidationResult {
  validation_result: 'APPROVED' | 'WARNING' | 'BLOCKED'
  violations: Array<{ action: string; rule: string; severity: string }>
  warnings: Array<{ action: string; suggestion: string }>
  approved_actions: string[]
  requires_review: boolean
}

// Checklist item for task context response (different format)
interface ContextChecklistItem {
  text: string
  priority: 'CRITICAL' | 'IMPORTANT' | 'SUPPLEMENTARY' | 'REFERENCE'
  category?: string
  required?: boolean
}

interface TaskContextResponse {
  decisions: Array<{
    id: string
    code: string
    statement: string
    relevance_score: number
  }>
  checklist: ContextChecklistItem[]
  constraints: Array<{
    text: string
    type: string
    source_decision: string
  }>
  total_decisions: number
  execution_time_ms: number
}

// API functions
const mcpApi = {
  listAgents: async (): Promise<AgentsResponse> => {
    const res = await fetch(`${API_BASE}/api/v1/mcp/list-agents`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    })
    if (!res.ok) throw new Error('Failed to fetch agents')
    return res.json()
  },

  getChecklist: async (taskType: string): Promise<ChecklistResponse> => {
    const res = await fetch(`${API_BASE}/api/v1/mcp/checklist`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_type: taskType })
    })
    if (!res.ok) throw new Error('Failed to fetch checklist')
    return res.json()
  },

  validateActions: async (params: { task_type: string; proposed_actions: string[] }): Promise<ValidationResult> => {
    const res = await fetch(`${API_BASE}/api/v1/mcp/validate-actions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    })
    if (!res.ok) throw new Error('Failed to validate actions')
    return res.json()
  },

  getTaskContext: async (params: { intent: string; project?: string; target?: string }): Promise<TaskContextResponse> => {
    const res = await fetch(`${API_BASE}/api/v1/mcp/task-context`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    })
    if (!res.ok) throw new Error('Failed to fetch task context')
    return res.json()
  }
}

// Icons
const Icons = {
  Robot: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
    </svg>
  ),
  Checklist: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
    </svg>
  ),
  Shield: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    </svg>
  ),
  Search: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
    </svg>
  ),
  Check: () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
    </svg>
  ),
  X: () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  ),
  Warning: () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
  ),
}

// Priority colors
const PRIORITY_COLORS = {
  CRITICAL: 'bg-red-100 text-red-800 border-red-200',
  IMPORTANT: 'bg-amber-100 text-amber-800 border-amber-200',
  SUPPLEMENTARY: 'bg-blue-100 text-blue-800 border-blue-200',
  REFERENCE: 'bg-gray-100 text-gray-800 border-gray-200',
}

// Task types for checklist (matches available agents)
const TASK_TYPES = [
  'deployment',
  'backend',
  'frontend',
  'database',
  'security',
]

// Tabs
type TabType = 'agents' | 'checklist' | 'validate' | 'context'

export default function MCPDashboard() {
  const [activeTab, setActiveTab] = useState<TabType>('agents')

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">MCP Dashboard</h1>
          <p className="text-gray-600 mt-1">Model Context Protocol management and testing</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <span className="px-2 py-1 bg-green-100 text-green-700 rounded">MICS Active</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-4">
          {[
            { id: 'agents' as TabType, label: 'Agents', icon: Icons.Robot },
            { id: 'checklist' as TabType, label: 'Checklists', icon: Icons.Checklist },
            { id: 'validate' as TabType, label: 'Validate Actions', icon: Icons.Shield },
            { id: 'context' as TabType, label: 'Task Context', icon: Icons.Search },
          ].map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={clsx(
                'flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors',
                activeTab === id
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              )}
            >
              <Icon />
              {label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'agents' && <AgentsTab />}
      {activeTab === 'checklist' && <ChecklistTab />}
      {activeTab === 'validate' && <ValidateTab />}
      {activeTab === 'context' && <ContextTab />}
    </div>
  )
}

// Agents Tab
function AgentsTab() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['mcp-agents'],
    queryFn: mcpApi.listAgents
  })

  if (isLoading) return <LoadingState />
  if (error) return <ErrorState message="Failed to load agents" />

  // Safe calculations with null checks
  const agents = data?.agents || []
  const totalAgents = data?.total || agents.length
  const uniqueCategories = new Set(agents.map(a => a.category).filter(Boolean))
  const uniqueGroups = new Set(agents.flatMap(a => a.groups || []))
  const uniqueFeatures = new Set(agents.flatMap(a => a.features || []))

  return (
    <div className="space-y-4">
      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard label="Total Agents" value={totalAgents} color="indigo" />
        <StatCard label="Categories" value={uniqueCategories.size} color="green" />
        <StatCard label="Groups" value={uniqueGroups.size} color="purple" />
        <StatCard label="Features" value={uniqueFeatures.size} color="gray" />
      </div>

      {/* Agent Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {agents.map(agent => (
          <AgentCard key={agent.id} agent={agent} />
        ))}
      </div>

      {agents.length === 0 && (
        <EmptyState message="No agents configured" />
      )}
    </div>
  )
}

function AgentCard({ agent }: { agent: Agent }) {
  const [expanded, setExpanded] = useState(false)

  // Category colors
  const categoryColors: Record<string, string> = {
    deployment: 'bg-green-100 text-green-600',
    backend: 'bg-blue-100 text-blue-600',
    frontend: 'bg-purple-100 text-purple-600',
    database: 'bg-amber-100 text-amber-600',
    security: 'bg-red-100 text-red-600',
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className={clsx(
              'w-10 h-10 rounded-lg flex items-center justify-center',
              categoryColors[agent.category] || 'bg-gray-100 text-gray-600'
            )}>
              <Icons.Robot />
            </div>
            <div>
              <h3 className="font-medium text-gray-900">{agent.name}</h3>
              <p className="text-xs text-gray-500">v{agent.version}</p>
            </div>
          </div>
          <span className="px-2 py-0.5 text-xs rounded-full bg-indigo-100 text-indigo-700 capitalize">
            {agent.category}
          </span>
        </div>

        <p className="mt-3 text-sm text-gray-600 line-clamp-2">{agent.description}</p>

        {/* Keywords */}
        <div className="mt-3 flex flex-wrap gap-1">
          {agent.keywords?.slice(0, 4).map(kw => (
            <span key={kw} className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
              {kw}
            </span>
          ))}
          {agent.keywords?.length > 4 && (
            <span className="px-2 py-0.5 bg-gray-100 text-gray-500 text-xs rounded">
              +{agent.keywords.length - 4}
            </span>
          )}
        </div>

        {/* Groups & Features */}
        <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
          <span>Groups: <span className="font-mono bg-gray-100 px-1.5 py-0.5 rounded">{agent.groups?.join(', ') || '-'}</span></span>
        </div>
      </div>

      {/* Expand/Collapse */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-2 text-xs text-gray-500 hover:bg-gray-50 border-t border-gray-100 text-left"
      >
        {expanded ? '▲ Less details' : '▼ More details'}
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-3 border-t border-gray-100 bg-gray-50">
          {/* Features */}
          <div>
            <div className="text-xs font-medium text-gray-500 mb-1">Features ({agent.features?.length || 0})</div>
            <div className="flex flex-wrap gap-1">
              {agent.features?.map(f => (
                <span key={f} className="px-1.5 py-0.5 bg-white border text-xs rounded font-mono">
                  {f}
                </span>
              ))}
            </div>
          </div>

          {/* All Keywords */}
          {agent.keywords?.length > 4 && (
            <div>
              <div className="text-xs font-medium text-gray-500 mb-1">All Keywords</div>
              <div className="flex flex-wrap gap-1">
                {agent.keywords.map(kw => (
                  <span key={kw} className="px-1.5 py-0.5 bg-white border text-xs rounded">
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// Checklist Tab
function ChecklistTab() {
  const [selectedTaskType, setSelectedTaskType] = useState('deployment')

  const { data, isLoading, error } = useQuery({
    queryKey: ['mcp-checklist', selectedTaskType],
    queryFn: () => mcpApi.getChecklist(selectedTaskType)
  })

  // Helper to render a phase section
  const renderPhase = (title: string, items: ChecklistItem[], colorClass: string) => {
    if (!items || items.length === 0) return null
    return (
      <div className="space-y-2">
        <h4 className={clsx('text-sm font-medium px-4 py-2', colorClass)}>{title}</h4>
        {items.map((item, idx) => (
          <div key={item.id || idx} className="px-4 py-3 flex items-start gap-3 border-b border-gray-100 last:border-0">
            <div className={clsx(
              'mt-0.5 w-5 h-5 rounded flex items-center justify-center flex-shrink-0',
              item.blocking ? 'bg-red-100 text-red-600' : 'bg-gray-100 text-gray-400'
            )}>
              {item.blocking ? <Icons.Warning /> : <Icons.Check />}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-900">{item.step}</p>
              {item.command && (
                <code className="mt-1 block text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded font-mono">
                  {item.command}
                </code>
              )}
              <div className="mt-1 flex items-center gap-2">
                {item.blocking && (
                  <span className="px-2 py-0.5 text-xs rounded bg-red-100 text-red-700 border border-red-200">
                    BLOCKING
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Task Type Selector */}
      <div className="flex flex-wrap gap-2">
        {TASK_TYPES.map(type => (
          <button
            key={type}
            onClick={() => setSelectedTaskType(type)}
            className={clsx(
              'px-3 py-1.5 text-sm rounded-lg transition-colors capitalize',
              selectedTaskType === type
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            )}
          >
            {type}
          </button>
        ))}
      </div>

      {isLoading && <LoadingState />}
      {error && <ErrorState message="Failed to load checklist" />}

      {data && (
        <div className="space-y-4">
          {/* Agent Info */}
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-indigo-100 text-indigo-600 flex items-center justify-center">
                  <Icons.Robot />
                </div>
                <div>
                  <h3 className="font-medium text-gray-900">{data.agent?.name || 'Unknown Agent'}</h3>
                  <p className="text-xs text-gray-500">{data.agent?.id}</p>
                </div>
              </div>
              <span className="text-sm text-gray-500">{data.total_steps} steps</span>
            </div>
          </div>

          {/* Critical Rules */}
          {data.critical_rules && data.critical_rules.length > 0 && (
            <div className="bg-red-50 rounded-lg border border-red-200 p-4">
              <h4 className="text-sm font-medium text-red-800 mb-2">Critical Rules</h4>
              <ul className="space-y-1">
                {data.critical_rules.map((rule, idx) => (
                  <li key={idx} className="text-sm text-red-700 flex items-start gap-2">
                    <span className="text-red-500 mt-0.5">•</span>
                    {rule}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Checklist Phases */}
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            {renderPhase('Pre-Deploy', data.checklist?.pre_deploy || [], 'bg-amber-50 text-amber-800')}
            {renderPhase('Deploy', data.checklist?.deploy || [], 'bg-blue-50 text-blue-800')}
            {renderPhase('Post-Deploy', data.checklist?.post_deploy || [], 'bg-green-50 text-green-800')}

            {(!data.checklist?.pre_deploy?.length &&
              !data.checklist?.deploy?.length &&
              !data.checklist?.post_deploy?.length) && (
              <div className="p-8 text-center text-gray-500">
                No checklist items for this task type
              </div>
            )}
          </div>

          {/* Error */}
          {data.error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
              {data.error}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// Validate Actions Tab
function ValidateTab() {
  const [taskType, setTaskType] = useState('deployment')
  const [actions, setActions] = useState('')
  const [result, setResult] = useState<ValidationResult | null>(null)

  const mutation = useMutation({
    mutationFn: mcpApi.validateActions,
    onSuccess: (data) => setResult(data)
  })

  const handleValidate = () => {
    const actionList = actions.split('\n').filter(a => a.trim())
    if (actionList.length === 0) return

    mutation.mutate({
      task_type: taskType,
      proposed_actions: actionList
    })
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Input */}
      <div className="space-y-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-4">
          <h3 className="font-medium text-gray-900">Validate Proposed Actions</h3>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Task Type</label>
            <select
              value={taskType}
              onChange={(e) => setTaskType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              {TASK_TYPES.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Proposed Actions (one per line)
            </label>
            <textarea
              value={actions}
              onChange={(e) => setActions(e.target.value)}
              placeholder="git pull origin main&#10;docker build -t app:latest .&#10;docker push registry/app:latest"
              rows={8}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 font-mono text-sm"
            />
          </div>

          <button
            onClick={handleValidate}
            disabled={mutation.isPending || !actions.trim()}
            className={clsx(
              'w-full px-4 py-2 rounded-lg font-medium transition-colors flex items-center justify-center gap-2',
              mutation.isPending || !actions.trim()
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-indigo-600 text-white hover:bg-indigo-700'
            )}
          >
            {mutation.isPending ? (
              <>
                <span className="animate-spin">⏳</span>
                Validating...
              </>
            ) : (
              <>
                <Icons.Shield />
                Validate Actions
              </>
            )}
          </button>
        </div>
      </div>

      {/* Result */}
      <div className="space-y-4">
        {mutation.error && <ErrorState message="Validation failed" />}

        {result && (
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            {/* Result Header */}
            <div className={clsx(
              'p-4',
              result.validation_result === 'APPROVED' && 'bg-green-50 border-b border-green-100',
              result.validation_result === 'WARNING' && 'bg-amber-50 border-b border-amber-100',
              result.validation_result === 'BLOCKED' && 'bg-red-50 border-b border-red-100'
            )}>
              <div className="flex items-center gap-2">
                {result.validation_result === 'APPROVED' && <Icons.Check />}
                {result.validation_result === 'WARNING' && <Icons.Warning />}
                {result.validation_result === 'BLOCKED' && <Icons.X />}
                <span className={clsx(
                  'font-medium',
                  result.validation_result === 'APPROVED' && 'text-green-700',
                  result.validation_result === 'WARNING' && 'text-amber-700',
                  result.validation_result === 'BLOCKED' && 'text-red-700'
                )}>
                  {result.validation_result}
                </span>
              </div>
            </div>

            <div className="p-4 space-y-4">
              {/* Approved Actions */}
              {result.approved_actions.length > 0 && (
                <div>
                  <div className="text-sm font-medium text-green-700 mb-2">
                    Approved ({result.approved_actions.length})
                  </div>
                  <ul className="space-y-1">
                    {result.approved_actions.map((action, idx) => (
                      <li key={idx} className="flex items-center gap-2 text-sm text-gray-700">
                        <span className="text-green-500"><Icons.Check /></span>
                        <code className="bg-gray-100 px-1 py-0.5 rounded">{action}</code>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Violations */}
              {result.violations.length > 0 && (
                <div>
                  <div className="text-sm font-medium text-red-700 mb-2">
                    Violations ({result.violations.length})
                  </div>
                  <ul className="space-y-2">
                    {result.violations.map((v, idx) => (
                      <li key={idx} className="text-sm bg-red-50 p-2 rounded border border-red-100">
                        <div className="flex items-center gap-2 text-red-700">
                          <Icons.X />
                          <code className="bg-white px-1 py-0.5 rounded">{v.action}</code>
                        </div>
                        <p className="mt-1 text-red-600 text-xs">Rule: {v.rule}</p>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Warnings */}
              {result.warnings.length > 0 && (
                <div>
                  <div className="text-sm font-medium text-amber-700 mb-2">
                    Warnings ({result.warnings.length})
                  </div>
                  <ul className="space-y-2">
                    {result.warnings.map((w, idx) => (
                      <li key={idx} className="text-sm bg-amber-50 p-2 rounded border border-amber-100">
                        <div className="flex items-center gap-2 text-amber-700">
                          <Icons.Warning />
                          <code className="bg-white px-1 py-0.5 rounded">{w.action}</code>
                        </div>
                        <p className="mt-1 text-amber-600 text-xs">{w.suggestion}</p>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Review Required */}
              {result.requires_review && (
                <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
                  ⚠️ Human review required before proceeding
                </div>
              )}
            </div>
          </div>
        )}

        {!result && !mutation.isPending && (
          <div className="bg-gray-50 rounded-lg border-2 border-dashed border-gray-200 p-8 text-center text-gray-500">
            <Icons.Shield />
            <p className="mt-2">Enter actions and click validate to see results</p>
          </div>
        )}
      </div>
    </div>
  )
}

// Context Tab
function ContextTab() {
  const [intent, setIntent] = useState('')
  const [project, setProject] = useState('')
  const [target, setTarget] = useState('')
  const [result, setResult] = useState<TaskContextResponse | null>(null)

  const mutation = useMutation({
    mutationFn: mcpApi.getTaskContext,
    onSuccess: (data) => setResult(data)
  })

  const handleQuery = () => {
    if (!intent.trim()) return
    mutation.mutate({ intent, project: project || undefined, target: target || undefined })
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Input */}
      <div className="space-y-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-4">
          <h3 className="font-medium text-gray-900">Query Task Context</h3>
          <p className="text-sm text-gray-600">
            Retrieve relevant decisions and constraints for a specific task intent.
          </p>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Intent <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={intent}
              onChange={(e) => setIntent(e.target.value)}
              placeholder="e.g., deploy backend service"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Project</label>
              <input
                type="text"
                value={project}
                onChange={(e) => setProject(e.target.value)}
                placeholder="atlas-mantra"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Target</label>
              <input
                type="text"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                placeholder="production"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
          </div>

          <button
            onClick={handleQuery}
            disabled={mutation.isPending || !intent.trim()}
            className={clsx(
              'w-full px-4 py-2 rounded-lg font-medium transition-colors flex items-center justify-center gap-2',
              mutation.isPending || !intent.trim()
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-indigo-600 text-white hover:bg-indigo-700'
            )}
          >
            {mutation.isPending ? (
              <>
                <span className="animate-spin">⏳</span>
                Querying...
              </>
            ) : (
              <>
                <Icons.Search />
                Get Context
              </>
            )}
          </button>
        </div>
      </div>

      {/* Result */}
      <div className="space-y-4">
        {mutation.error && <ErrorState message="Context query failed" />}

        {result && (
          <div className="space-y-4">
            {/* Stats */}
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Found {result.total_decisions} relevant decisions</span>
                <span className="text-gray-400">{result.execution_time_ms}ms</span>
              </div>
            </div>

            {/* Decisions */}
            {result.decisions.length > 0 && (
              <div className="bg-white rounded-lg border border-gray-200 divide-y">
                <div className="p-3 bg-gray-50 text-sm font-medium text-gray-700">
                  Relevant Decisions
                </div>
                {result.decisions.map(d => (
                  <div key={d.id} className="p-3">
                    <div className="flex items-center justify-between">
                      <code className="text-xs font-mono bg-indigo-100 text-indigo-700 px-1.5 py-0.5 rounded">
                        {d.code}
                      </code>
                      <span className="text-xs text-gray-400">
                        {(d.relevance_score * 100).toFixed(0)}% match
                      </span>
                    </div>
                    <p className="mt-1 text-sm text-gray-700 line-clamp-2">{d.statement}</p>
                  </div>
                ))}
              </div>
            )}

            {/* Constraints */}
            {result.constraints.length > 0 && (
              <div className="bg-white rounded-lg border border-gray-200 divide-y">
                <div className="p-3 bg-gray-50 text-sm font-medium text-gray-700">
                  Applicable Constraints
                </div>
                {result.constraints.map((c, idx) => (
                  <div key={idx} className="p-3">
                    <div className="flex items-center gap-2">
                      <span className={clsx(
                        'px-2 py-0.5 text-xs rounded',
                        c.type === 'PROHIBITION' && 'bg-red-100 text-red-700',
                        c.type === 'REQUIREMENT' && 'bg-green-100 text-green-700',
                        c.type === 'LIMITATION' && 'bg-amber-100 text-amber-700'
                      )}>
                        {c.type}
                      </span>
                      <span className="text-xs text-gray-400">from {c.source_decision}</span>
                    </div>
                    <p className="mt-1 text-sm text-gray-700">{c.text}</p>
                  </div>
                ))}
              </div>
            )}

            {/* Checklist */}
            {result.checklist.length > 0 && (
              <div className="bg-white rounded-lg border border-gray-200 divide-y">
                <div className="p-3 bg-gray-50 text-sm font-medium text-gray-700">
                  Task Checklist
                </div>
                {result.checklist.slice(0, 5).map((item, idx) => (
                  <div key={idx} className="p-3 flex items-start gap-2">
                    <input type="checkbox" className="mt-1" />
                    <div>
                      <p className="text-sm text-gray-700">{item.text}</p>
                      <span className={clsx(
                        'text-xs px-1.5 py-0.5 rounded',
                        PRIORITY_COLORS[item.priority]
                      )}>
                        {item.priority}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {!result && !mutation.isPending && (
          <div className="bg-gray-50 rounded-lg border-2 border-dashed border-gray-200 p-8 text-center text-gray-500">
            <Icons.Search />
            <p className="mt-2">Enter an intent and query to see relevant context</p>
          </div>
        )}
      </div>
    </div>
  )
}

// Helper Components
function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  const colors: Record<string, string> = {
    indigo: 'bg-indigo-50 text-indigo-600 border-indigo-100',
    green: 'bg-green-50 text-green-600 border-green-100',
    gray: 'bg-gray-50 text-gray-600 border-gray-100',
    purple: 'bg-purple-50 text-purple-600 border-purple-100',
  }

  return (
    <div className={clsx('p-4 rounded-lg border', colors[color])}>
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-sm opacity-80">{label}</div>
    </div>
  )
}

function LoadingState() {
  return (
    <div className="flex items-center justify-center p-12">
      <div className="animate-spin text-2xl">⏳</div>
    </div>
  )
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
      {message}
    </div>
  )
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="bg-gray-50 rounded-lg border-2 border-dashed border-gray-200 p-8 text-center text-gray-500">
      {message}
    </div>
  )
}
