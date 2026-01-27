/**
 * Approval Dashboard
 * Track and manage pending decision approvals
 */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { clsx } from 'clsx'
import { approvalsApi, decisionsApi, PendingApproval, Decision } from '../shared/api'
import { FEATURE_LABELS, GROUP_COLORS } from '../shared/constants'

// =============================================================================
// Component
// =============================================================================

export default function ApprovalDashboard() {
  const queryClient = useQueryClient()
  const [actorName, setActorName] = useState('')
  const [selectedApproval, setSelectedApproval] = useState<PendingApproval | null>(null)
  const [rejectReason, setRejectReason] = useState('')
  const [approvalComment, setApprovalComment] = useState('')

  // Fetch pending approvals
  const { data: pendingData, isLoading, error } = useQuery({
    queryKey: ['pending-approvals'],
    queryFn: () => approvalsApi.listPending({ limit: 100 }),
    // Simulate with decisions list if endpoint not available
    retry: false,
  })

  // Fetch recent decisions as fallback/additional context
  const { data: recentDecisions } = useQuery({
    queryKey: ['recent-decisions'],
    queryFn: () => decisionsApi.list({ limit: 20 }),
  })

  // Approve mutation
  const approveMutation = useMutation({
    mutationFn: (proposalId: string) =>
      approvalsApi.approve(proposalId, actorName || 'approval-user', approvalComment),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-approvals'] })
      setSelectedApproval(null)
      setApprovalComment('')
    },
  })

  // Reject mutation
  const rejectMutation = useMutation({
    mutationFn: (proposalId: string) =>
      approvalsApi.reject(proposalId, actorName || 'approval-user', rejectReason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-approvals'] })
      setSelectedApproval(null)
      setRejectReason('')
    },
  })

  // Simulated pending approvals if API not available
  const pendingApprovals = pendingData?.pending || []
  const hasPendingApi = !error

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Approval Dashboard</h1>
          <p className="mt-1 text-gray-600">
            Review and approve pending decisions
          </p>
        </div>

        {/* Actor Name Input */}
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-500">Your Name:</label>
          <input
            type="text"
            value={actorName}
            onChange={(e) => setActorName(e.target.value)}
            placeholder="Enter your name"
            className="px-3 py-1.5 border rounded-lg focus:ring-2 focus:ring-indigo-500 text-sm"
          />
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          label="Pending Approvals"
          value={pendingApprovals.length}
          color="amber"
          icon="⏳"
        />
        <StatCard
          label="High Impact"
          value={pendingApprovals.filter(p => p.impact_level === 'HIGH' || p.impact_level === 'CRITICAL').length}
          color="red"
          icon="🔴"
        />
        <StatCard
          label="With Conflicts"
          value={pendingApprovals.filter(p => p.has_conflicts).length}
          color="orange"
          icon="⚠️"
        />
        <StatCard
          label="Ready to Approve"
          value={pendingApprovals.filter(p => !p.has_conflicts && p.quality_score >= 80).length}
          color="green"
          icon="✅"
        />
      </div>

      {/* API Status Warning */}
      {!hasPendingApi && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <span className="text-lg">⚠️</span>
            <div>
              <p className="font-medium text-amber-800">Pending Approvals API not available</p>
              <p className="text-sm text-amber-700">
                Showing recent decisions as reference. Use the Validator page to create proposals.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-12">
          <div className="animate-spin w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full mx-auto"></div>
          <p className="mt-2 text-gray-500">Loading pending approvals...</p>
        </div>
      )}

      {/* Pending Approvals List */}
      {hasPendingApi && pendingApprovals.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="p-4 border-b">
            <h3 className="font-semibold text-gray-900">
              Pending Decisions ({pendingApprovals.length})
            </h3>
          </div>
          <div className="divide-y">
            {pendingApprovals.map((approval) => (
              <ApprovalCard
                key={approval.proposal_id}
                approval={approval}
                isSelected={selectedApproval?.proposal_id === approval.proposal_id}
                onApprove={() => approveMutation.mutate(approval.proposal_id)}
                onReject={() => {
                  setSelectedApproval(approval)
                }}
                isApproving={approveMutation.isPending}
              />
            ))}
          </div>
        </div>
      )}

      {/* No Pending Approvals */}
      {hasPendingApi && pendingApprovals.length === 0 && !isLoading && (
        <div className="bg-white rounded-lg shadow-sm border p-12 text-center">
          <span className="text-4xl">✅</span>
          <h3 className="mt-4 text-lg font-medium text-gray-900">All caught up!</h3>
          <p className="mt-2 text-gray-500">No pending approvals at this time.</p>
          <Link
            to="/wizard"
            className="mt-4 inline-block px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            Create New Decision
          </Link>
        </div>
      )}

      {/* Recent Decisions (fallback view) */}
      {!hasPendingApi && recentDecisions && (
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="p-4 border-b">
            <h3 className="font-semibold text-gray-900">
              Recent Decisions ({recentDecisions.decisions.length})
            </h3>
            <p className="text-sm text-gray-500">
              Reference view of recent decisions
            </p>
          </div>
          <div className="divide-y">
            {recentDecisions.decisions.slice(0, 10).map((decision) => (
              <RecentDecisionCard key={decision.decision_id} decision={decision} />
            ))}
          </div>
        </div>
      )}

      {/* Reject Modal */}
      {selectedApproval && (
        <RejectModal
          approval={selectedApproval}
          reason={rejectReason}
          onReasonChange={setRejectReason}
          onConfirm={() => rejectMutation.mutate(selectedApproval.proposal_id)}
          onCancel={() => {
            setSelectedApproval(null)
            setRejectReason('')
          }}
          isRejecting={rejectMutation.isPending}
        />
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
  color,
  icon,
}: {
  label: string
  value: number
  color: 'amber' | 'red' | 'orange' | 'green'
  icon: string
}) {
  const colorClasses = {
    amber: 'bg-amber-50 border-amber-200 text-amber-700',
    red: 'bg-red-50 border-red-200 text-red-700',
    orange: 'bg-orange-50 border-orange-200 text-orange-700',
    green: 'bg-green-50 border-green-200 text-green-700',
  }

  return (
    <div className={clsx('rounded-lg border p-4', colorClasses[color])}>
      <div className="flex items-center justify-between">
        <span className="text-2xl">{icon}</span>
        <span className="text-3xl font-bold">{value}</span>
      </div>
      <p className="mt-2 text-sm font-medium">{label}</p>
    </div>
  )
}

function ApprovalCard({
  approval,
  isSelected,
  onApprove,
  onReject,
  isApproving,
}: {
  approval: PendingApproval
  isSelected: boolean
  onApprove: () => void
  onReject: () => void
  isApproving: boolean
}) {
  const decision = approval.decision

  return (
    <div
      className={clsx(
        'p-4 hover:bg-gray-50 transition-colors',
        isSelected && 'bg-indigo-50'
      )}
    >
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
        {/* Decision Info */}
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span
              className="px-2 py-0.5 rounded text-xs font-medium text-white"
              style={{ backgroundColor: GROUP_COLORS[decision.group_id] || '#6B7280' }}
            >
              {decision.group_id}
            </span>
            <span className="text-xs text-gray-500">{FEATURE_LABELS[decision.feature_id]}</span>
            <span className="font-mono text-sm text-gray-700">
              {decision.decision_code || decision.decision_id.slice(0, 8)}
            </span>
          </div>

          <p className="text-gray-900 font-medium">{decision.statement}</p>

          <div className="mt-2 flex flex-wrap gap-2 text-xs">
            <span className="text-gray-500">
              Proposed by <span className="font-medium">{approval.proposed_by}</span>
            </span>
            <span className="text-gray-400">|</span>
            <span className="text-gray-500">
              {new Date(approval.proposed_at).toLocaleDateString()}
            </span>
          </div>

          {/* Quality & Impact Badges */}
          <div className="mt-3 flex flex-wrap gap-2">
            <span
              className={clsx(
                'px-2 py-0.5 rounded text-xs font-medium',
                approval.quality_score >= 80 && 'bg-green-100 text-green-700',
                approval.quality_score >= 60 && approval.quality_score < 80 && 'bg-amber-100 text-amber-700',
                approval.quality_score < 60 && 'bg-red-100 text-red-700'
              )}
            >
              Quality: {approval.quality_score}%
            </span>
            <span
              className={clsx(
                'px-2 py-0.5 rounded text-xs font-medium',
                approval.impact_level === 'LOW' && 'bg-green-100 text-green-700',
                approval.impact_level === 'MODERATE' && 'bg-amber-100 text-amber-700',
                (approval.impact_level === 'HIGH' || approval.impact_level === 'CRITICAL') && 'bg-red-100 text-red-700'
              )}
            >
              Impact: {approval.impact_level}
            </span>
            {approval.has_conflicts && (
              <span className="px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-700">
                Has Conflicts
              </span>
            )}
            {approval.has_duplicates && (
              <span className="px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-700">
                Near Duplicates
              </span>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <Link
            to={`/decisions/${decision.decision_id}`}
            className="px-3 py-1.5 text-sm text-gray-600 border rounded-lg hover:bg-gray-100"
          >
            View
          </Link>
          <button
            onClick={onReject}
            className="px-3 py-1.5 text-sm text-red-600 border border-red-200 rounded-lg hover:bg-red-50"
          >
            Reject
          </button>
          <button
            onClick={onApprove}
            disabled={isApproving}
            className="px-3 py-1.5 text-sm text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:bg-gray-300"
          >
            {isApproving ? '...' : 'Approve'}
          </button>
        </div>
      </div>
    </div>
  )
}

function RecentDecisionCard({ decision }: { decision: Decision }) {
  return (
    <div className="p-4 hover:bg-gray-50 transition-colors">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span
              className="px-2 py-0.5 rounded text-xs font-medium text-white"
              style={{ backgroundColor: GROUP_COLORS[decision.group_id] || '#6B7280' }}
            >
              {decision.group_id}
            </span>
            <span className="font-mono text-sm text-gray-700">
              {decision.decision_code || decision.decision_id.slice(0, 8)}
            </span>
            {decision.approved_by && (
              <span className="px-2 py-0.5 rounded text-xs bg-green-100 text-green-700">
                Approved
              </span>
            )}
          </div>
          <p className="text-gray-900 text-sm">{decision.statement}</p>
          <p className="text-xs text-gray-500 mt-1">
            {decision.created_by} | {new Date(decision.created_at).toLocaleDateString()}
          </p>
        </div>
        <Link
          to={`/decisions/${decision.decision_id}`}
          className="px-3 py-1.5 text-sm text-indigo-600 hover:text-indigo-800"
        >
          View
        </Link>
      </div>
    </div>
  )
}

function RejectModal({
  approval,
  reason,
  onReasonChange,
  onConfirm,
  onCancel,
  isRejecting,
}: {
  approval: PendingApproval
  reason: string
  onReasonChange: (reason: string) => void
  onConfirm: () => void
  onCancel: () => void
  isRejecting: boolean
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Reject Decision</h3>

        <p className="text-sm text-gray-600 mb-4">
          You are rejecting:{' '}
          <span className="font-mono font-medium">
            {approval.decision.decision_code || approval.decision_id.slice(0, 8)}
          </span>
        </p>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Rejection Reason <span className="text-red-500">*</span>
          </label>
          <textarea
            value={reason}
            onChange={(e) => onReasonChange(e.target.value)}
            placeholder="Explain why this decision is being rejected..."
            rows={4}
            className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-red-500"
          />
        </div>

        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={!reason.trim() || isRejecting}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-300"
          >
            {isRejecting ? 'Rejecting...' : 'Confirm Rejection'}
          </button>
        </div>
      </div>
    </div>
  )
}
