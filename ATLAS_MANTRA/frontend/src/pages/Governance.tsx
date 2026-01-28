/**
 * Governance Page - Authority Model (A10)
 * Shows who can approve what and approval chains per domain
 * Per MANTRA-LAW-001 §5 (Sovereignty) and §6 (AI Authority)
 */

import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  Users,
  Clock,
  ClipboardList,
  AlertCircle,
  UserCheck,
  Bot,
  CheckCircle,
} from 'lucide-react'
import { decisionsApi } from '../shared/api'
import { DOMAINS, DOMAIN_LABELS } from '../shared/constants'

interface GovernanceDecision {
  decision_id: string
  decision_code: string
  statement: string
  domain_id: string
  aspect_id: string
  scope: string
  blast_radius: string
  created_by: string
  approved_by?: string
  approved_at?: string
  version: string
}

// Authority levels by domain
// NOTE: These are example roles - customize for your organization
const DOMAIN_AUTHORITY = {
  'INT': {
    approvers: ['Product Lead', 'Engineering Lead', 'Executive Sponsor'],
    description: 'Decisions about goals, priorities, and product direction. Typically approved by someone who can commit resources.',
    requiredLevel: 'Leadership',
    whyNeeded: 'These decisions set direction for the entire team, so leadership sign-off ensures alignment.',
  },
  'ARCH': {
    approvers: ['Senior Engineer', 'Tech Lead', 'Architect'],
    description: 'Decisions about system design, technology choices, and code structure. Approved by someone with technical expertise.',
    requiredLevel: 'Senior Technical',
    whyNeeded: 'Technical decisions have long-term impact, so experienced engineers should validate the approach.',
  },
  'CTL': {
    approvers: ['Security Engineer', 'Compliance Lead', 'Risk Owner'],
    description: 'Decisions about security, compliance, and risk management. Approved by someone responsible for risk.',
    requiredLevel: 'Security/Compliance',
    whyNeeded: 'Security and compliance decisions affect the entire organization and may have legal implications.',
  },
  'EVO': {
    approvers: ['DevOps Lead', 'Release Manager', 'On-call Engineer'],
    description: 'Decisions about deployments, migrations, and operational changes. Approved by someone who owns operations.',
    requiredLevel: 'Operations',
    whyNeeded: 'Deployment decisions can cause outages, so operational expertise is required.',
  },
}

// Approval requirements by scope
const SCOPE_REQUIREMENTS = {
  'APPLICATION': {
    level: 'Standard',
    approvers: 1,
    description: 'Affects a single app or service',
    example: 'e.g., "Use React Query in the dashboard app"',
    color: 'bg-green-100 text-green-800',
  },
  'DOMAIN': {
    level: 'Elevated',
    approvers: 2,
    description: 'Affects multiple apps in the same area',
    example: 'e.g., "All payment services must use idempotency keys"',
    color: 'bg-yellow-100 text-yellow-800',
  },
  'ORGANIZATION': {
    level: 'Critical',
    approvers: 3,
    description: 'Affects the entire organization',
    example: 'e.g., "All services must use PostgreSQL"',
    color: 'bg-red-100 text-red-800',
  },
}

// Blast radius approval requirements
const BLAST_RADIUS_REQUIREMENTS = {
  'LOW': { additionalReview: false, color: 'bg-green-100 text-green-800' },
  'MEDIUM': { additionalReview: false, color: 'bg-yellow-100 text-yellow-800' },
  'HIGH': { additionalReview: true, color: 'bg-orange-100 text-orange-800' },
  'CRITICAL': { additionalReview: true, color: 'bg-red-100 text-red-800' },
}

export default function Governance() {
  const [pendingApprovals, setPendingApprovals] = useState<GovernanceDecision[]>([])
  const [recentApprovals, setRecentApprovals] = useState<GovernanceDecision[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'overview' | 'pending' | 'history'>('overview')

  useEffect(() => {
    async function fetchData() {
      try {
        // Get decisions without approval (pending)
        const result = await decisionsApi.list({ limit: 1000 })
        const allDecisions = (result.decisions || []) as GovernanceDecision[]
        const pending = allDecisions.filter((d) => !d.approved_by)
        const approved = allDecisions
          .filter((d) => d.approved_by)
          .sort((a, b) =>
            new Date(b.approved_at || 0).getTime() - new Date(a.approved_at || 0).getTime()
          )
          .slice(0, 10)

        setPendingApprovals(pending)
        setRecentApprovals(approved)
      } catch (error) {
        console.error('Failed to fetch governance data:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <Users className="w-6 h-6 text-purple-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Governance & Authority</h1>
            <p className="text-gray-500">
              Manage who can approve decisions and track approval workflows
            </p>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white border rounded-lg p-4">
          <div className="text-2xl font-bold text-orange-600">{pendingApprovals.length}</div>
          <div className="text-sm text-gray-500">Pending Approvals</div>
        </div>
        <div className="bg-white border rounded-lg p-4">
          <div className="text-2xl font-bold text-green-600">{recentApprovals.length}</div>
          <div className="text-sm text-gray-500">Recently Approved</div>
        </div>
        <div className="bg-white border rounded-lg p-4">
          <div className="text-2xl font-bold text-purple-600">{DOMAINS.length}</div>
          <div className="text-sm text-gray-500">Domain Authorities</div>
        </div>
        <div className="bg-white border rounded-lg p-4">
          <div className="flex items-center gap-2">
            <Bot className="w-6 h-6 text-gray-400" />
            <span className="text-2xl font-bold text-gray-600">Human Only</span>
          </div>
          <div className="text-sm text-gray-500">AI cannot approve decisions</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b">
        <nav className="flex gap-4">
          {[
            { id: 'overview', label: 'Authority Overview', icon: Users },
            { id: 'pending', label: `Pending (${pendingApprovals.length})`, icon: Clock },
            { id: 'history', label: 'Approval History', icon: ClipboardList },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as typeof activeTab)}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
                activeTab === tab.id
                  ? 'border-purple-600 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Human Authority Reminder */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center gap-3">
                <UserCheck className="w-8 h-8 text-green-600" />
                <div>
                  <h3 className="font-semibold text-green-800">All Decisions Require Human Approval</h3>
                  <p className="text-sm text-green-700">
                    <strong>What AI can do:</strong> Analyze decisions, suggest improvements, detect conflicts.
                    <br />
                    <strong>What AI cannot do:</strong> Approve, reject, or finalize any decision.
                  </p>
                </div>
              </div>
            </div>

            {/* Customization Notice */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center gap-3">
                <AlertCircle className="w-8 h-8 text-blue-600" />
                <div>
                  <h3 className="font-semibold text-blue-800">Customize for Your Team</h3>
                  <p className="text-sm text-blue-700">
                    The approver roles below are <strong>examples</strong> based on typical team structures.
                    You can configure different roles (e.g., "Engineering Manager" instead of "Technical Lead")
                    to match your organization. The only requirement is that approvers must be real people.
                  </p>
                </div>
              </div>
            </div>

            {/* Domain Authority Cards */}
            <h3 className="font-semibold text-gray-900">Authority by Domain</h3>
            <div className="grid gap-4 md:grid-cols-2">
              {DOMAINS.map((domain) => {
                const authority = DOMAIN_AUTHORITY[domain as keyof typeof DOMAIN_AUTHORITY]
                // Per DOMAIN_COLORS in constants.ts: INT=Blue, ARCH=Purple, CTL=Red, EVO=Green
                const colors: Record<string, string> = {
                  'INT': 'border-blue-200 bg-blue-50',
                  'ARCH': 'border-purple-200 bg-purple-50',
                  'CTL': 'border-red-200 bg-red-50',
                  'EVO': 'border-green-200 bg-green-50',
                }
                return (
                  <div key={domain} className={`border rounded-lg overflow-hidden ${colors[domain]}`}>
                    <div className="px-4 py-3 border-b border-white/50">
                      <Link
                        to={`/domain/${domain.toLowerCase()}`}
                        className="font-bold hover:underline"
                      >
                        {domain}: {DOMAIN_LABELS[domain]}
                      </Link>
                      <p className="text-sm opacity-80 mt-1">{authority.description}</p>
                    </div>
                    <div className="p-4 bg-white/50">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-semibold text-gray-500 uppercase">Required Level</span>
                        <span className="text-sm font-medium">{authority.requiredLevel}</span>
                      </div>
                      <div className="text-xs font-semibold text-gray-500 uppercase mb-2">Example Approvers</div>
                      <div className="flex flex-wrap gap-2 mb-3">
                        {authority.approvers.map((approver) => (
                          <span key={approver} className="px-2 py-1 bg-white rounded text-sm border">
                            {approver}
                          </span>
                        ))}
                      </div>
                      <div className="text-xs text-gray-600 bg-white/70 rounded p-2">
                        <strong>Why?</strong> {authority.whyNeeded}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Scope Requirements */}
            <h3 className="font-semibold text-gray-900 mt-8">How Many Approvers Are Needed?</h3>
            <p className="text-sm text-gray-500 mb-4">
              Wider-impact decisions need more approvers to ensure proper review.
            </p>
            <div className="grid gap-4 md:grid-cols-3">
              {Object.entries(SCOPE_REQUIREMENTS).map(([scope, req]) => (
                <div key={scope} className="border rounded-lg p-4">
                  <div className={`inline-block px-2 py-1 rounded text-sm font-medium mb-2 ${req.color}`}>
                    {scope}
                  </div>
                  <div className="text-sm text-gray-600 mb-2">{req.description}</div>
                  <div className="text-xs text-gray-400 italic mb-3">{req.example}</div>
                  <div className="flex items-center justify-between text-sm border-t pt-2">
                    <span className="text-gray-500">Approvers needed:</span>
                    <span className="font-bold text-lg">{req.approvers}</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Blast Radius Impact */}
            <h3 className="font-semibold text-gray-900 mt-8">When Is Extra Review Needed?</h3>
            <p className="text-sm text-gray-500 mb-4">
              "Blast radius" measures how much damage could occur if this decision turns out to be wrong.
            </p>
            <div className="grid grid-cols-4 gap-4">
              {Object.entries(BLAST_RADIUS_REQUIREMENTS).map(([radius, req]) => (
                <div key={radius} className="border rounded-lg p-3 text-center">
                  <div className={`inline-block px-2 py-1 rounded text-xs font-medium mb-2 ${req.color}`}>
                    {radius}
                  </div>
                  <div className="text-sm">
                    {req.additionalReview ? (
                      <span className="text-orange-600 font-medium">Needs security review</span>
                    ) : (
                      <span className="text-gray-500">Standard approval</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Pending Tab */}
        {activeTab === 'pending' && (
          <div className="space-y-4">
            {loading ? (
              <div className="text-center py-8 text-gray-500">Loading...</div>
            ) : pendingApprovals.length === 0 ? (
              <div className="text-center py-8">
                <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-2" />
                <div className="text-gray-500">All caught up! No decisions waiting for approval.</div>
              </div>
            ) : (
              <>
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                  <p className="text-sm text-amber-800">
                    <strong>{pendingApprovals.length} decision{pendingApprovals.length > 1 ? 's' : ''}</strong> waiting for human approval.
                    Decisions cannot be enforced until approved by an authorized person.
                  </p>
                </div>
                <div className="space-y-3">
                  {pendingApprovals.map((decision) => {
                    const authority = DOMAIN_AUTHORITY[decision.domain_id as keyof typeof DOMAIN_AUTHORITY]
                    const scopeReq = SCOPE_REQUIREMENTS[decision.scope as keyof typeof SCOPE_REQUIREMENTS]
                    return (
                      <div key={decision.decision_id} className="border rounded-lg p-4 hover:bg-gray-50">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <Link
                                to={`/decisions/${decision.decision_id}`}
                                className="font-mono text-sm text-indigo-600 hover:underline"
                              >
                                {decision.decision_code}
                              </Link>
                              <span className="text-xs text-gray-400">
                                {DOMAIN_LABELS[decision.domain_id] || decision.domain_id}
                              </span>
                            </div>
                            <p className="text-sm text-gray-700 mt-1">{decision.statement}</p>
                            <div className="flex gap-2 mt-2">
                              <span className={`px-2 py-0.5 text-xs rounded ${scopeReq?.color || 'bg-gray-100'}`}>
                                {decision.scope}
                              </span>
                              <span className={`px-2 py-0.5 text-xs rounded ${
                                BLAST_RADIUS_REQUIREMENTS[decision.blast_radius as keyof typeof BLAST_RADIUS_REQUIREMENTS]?.color || 'bg-gray-100'
                              }`}>
                                {decision.blast_radius} impact
                              </span>
                            </div>
                            {/* Why approval is needed */}
                            <div className="mt-2 text-xs text-gray-500 bg-gray-50 rounded p-2">
                              <strong>Needs approval from:</strong> {authority?.approvers.join(', ') || 'Authorized approver'}
                              {scopeReq && scopeReq.approvers > 1 && (
                                <span className="ml-1 text-amber-600">({scopeReq.approvers} approvers required)</span>
                              )}
                            </div>
                          </div>
                          <Link
                            to={`/decisions/${decision.decision_id}`}
                            className="px-3 py-1 bg-emerald-600 text-white text-sm rounded hover:bg-emerald-700 ml-4"
                          >
                            Review
                          </Link>
                        </div>
                      </div>
                    )
                  })}
                </div>
                <div className="text-center pt-4">
                  <Link
                    to="/approvals"
                    className="text-indigo-600 hover:underline text-sm"
                  >
                    Open Approval Dashboard for bulk actions
                  </Link>
                </div>
              </>
            )}
          </div>
        )}

        {/* History Tab */}
        {activeTab === 'history' && (
          <div className="space-y-4">
            {loading ? (
              <div className="text-center py-8 text-gray-500">Loading...</div>
            ) : recentApprovals.length === 0 ? (
              <div className="text-center py-8">
                <ClipboardList className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                <div className="text-gray-500">No approvals yet. Decisions will appear here once approved.</div>
              </div>
            ) : (
              <>
                <div className="bg-gray-50 border rounded-lg p-3">
                  <p className="text-sm text-gray-600">
                    Showing the <strong>10 most recent</strong> approved decisions.
                    Each approval is permanent and creates an audit trail.
                  </p>
                </div>
                <table className="w-full">
                  <thead>
                    <tr className="border-b text-left text-sm text-gray-500">
                      <th className="pb-2">Decision</th>
                      <th className="pb-2">Statement</th>
                      <th className="pb-2">Approved By</th>
                      <th className="pb-2">Date</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {recentApprovals.map((decision) => (
                      <tr key={decision.decision_id} className="hover:bg-gray-50">
                        <td className="py-3">
                          <Link
                            to={`/decisions/${decision.decision_id}`}
                            className="font-mono text-sm text-indigo-600 hover:underline"
                          >
                            {decision.decision_code}
                          </Link>
                          <div className="text-xs text-gray-400">
                            {DOMAIN_LABELS[decision.domain_id] || decision.domain_id}
                          </div>
                        </td>
                        <td className="py-3 text-sm text-gray-700 max-w-xs truncate">
                          {decision.statement}
                        </td>
                        <td className="py-3 text-sm">
                          <span className="px-2 py-1 bg-green-100 text-green-800 rounded inline-flex items-center gap-1">
                            <UserCheck className="w-3 h-3" />
                            {decision.approved_by}
                          </span>
                        </td>
                        <td className="py-3 text-sm text-gray-500">
                          {decision.approved_at
                            ? new Date(decision.approved_at).toLocaleDateString('en-US', {
                                month: 'short',
                                day: 'numeric',
                                year: 'numeric',
                              })
                            : '-'
                          }
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div className="text-center pt-4">
                  <Link
                    to="/audit"
                    className="text-indigo-600 hover:underline text-sm"
                  >
                    View complete Audit Log with all actions
                  </Link>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
