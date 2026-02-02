/**
 * Decision Detail Component - Phase A+
 * Shows full decision details + workflow status
 */

import { useParams, useNavigate } from 'react-router-dom'
import { useDecisionDetail } from '../hooks/useDecisionDetail'

export function DecisionDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data, isLoading, error } = useDecisionDetail(id)

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading decision details...</div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded p-4">
          <div className="text-red-800 font-semibold">Error loading decision</div>
          <div className="text-red-600 text-sm mt-1">
            {error instanceof Error ? error.message : 'Unknown error'}
          </div>
        </div>
        <button
          onClick={() => navigate('/decisions')}
          className="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded font-semibold"
        >
          Back to Decisions
        </button>
      </div>
    )
  }

  if (!data) {
    return null
  }

  const { decision, workflow, workflow_actions } = data

  // Outcome color mapping
  const outcomeColors = {
    ALLOWED: 'bg-green-100 text-green-800',
    DENIED: 'bg-red-100 text-red-800',
    REQUIRE_APPROVAL: 'bg-yellow-100 text-yellow-800',
  } as const

  const outcomeColor =
    outcomeColors[decision.outcome as keyof typeof outcomeColors] ||
    'bg-gray-100 text-gray-800'

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Decision Detail</h1>
          <p className="text-sm text-gray-600 mt-1 font-mono">{decision.decision_id}</p>
        </div>
        <button
          onClick={() => navigate('/decisions')}
          className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded font-semibold"
        >
          Back to List
        </button>
      </div>

      {/* Decision Card */}
      <div className="bg-white border rounded-lg p-6">
        <h2 className="text-lg font-bold text-gray-900 mb-4">Decision Information</h2>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <span className="text-sm font-semibold text-gray-700">Decision Type</span>
            <p className="mt-1 text-gray-900 font-medium">{decision.decision_type}</p>
          </div>

          <div>
            <span className="text-sm font-semibold text-gray-700">Outcome</span>
            <div className="mt-1">
              <span className={`px-2 py-1 rounded text-xs font-semibold ${outcomeColor}`}>
                {decision.outcome_label}
              </span>
            </div>
          </div>

          <div>
            <span className="text-sm font-semibold text-gray-700">Created At</span>
            <p className="mt-1 text-gray-900">
              {new Date(decision.created_at).toLocaleString()}
            </p>
          </div>

          {decision.latency_ms !== null && (
            <div>
              <span className="text-sm font-semibold text-gray-700">Processing Time</span>
              <p className="mt-1 text-gray-900">{decision.latency_ms} ms</p>
            </div>
          )}

          {decision.rule_matched_id && (
            <div className="col-span-2">
              <span className="text-sm font-semibold text-gray-700">Rule Matched</span>
              <p className="mt-1 text-gray-900 font-mono text-sm">
                {decision.rule_matched_id}
                {decision.rule_version && (
                  <span className="text-gray-600 ml-2">(version {decision.rule_version})</span>
                )}
              </p>
            </div>
          )}
        </div>

        {/* Outcome Description */}
        <div className="mt-4 pt-4 border-t">
          <span className="text-sm font-semibold text-gray-700">Description</span>
          <p className="mt-1 text-gray-900">{decision.outcome_description}</p>
        </div>

        {/* Context Data */}
        {decision.context && Object.keys(decision.context).length > 0 && (
          <div className="mt-4 pt-4 border-t">
            <span className="text-sm font-semibold text-gray-700">Context Data</span>
            <div className="mt-2 bg-gray-50 rounded p-3 font-mono text-sm">
              <pre className="whitespace-pre-wrap">
                {JSON.stringify(decision.context, null, 2)}
              </pre>
            </div>
          </div>
        )}

        {/* Metadata */}
        {decision.metadata_json && Object.keys(decision.metadata_json).length > 0 && (
          <div className="mt-4 pt-4 border-t">
            <span className="text-sm font-semibold text-gray-700">Metadata</span>
            <div className="mt-2 bg-gray-50 rounded p-3 font-mono text-sm">
              <pre className="whitespace-pre-wrap">
                {JSON.stringify(decision.metadata_json, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>

      {/* Workflow Card (if approval required) */}
      {workflow && (
        <div className="bg-white border rounded-lg p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Approval Workflow</h2>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="text-sm font-semibold text-gray-700">Workflow ID</span>
              <p className="mt-1 text-gray-900 font-mono text-sm">{workflow.workflow_id}</p>
            </div>

            <div>
              <span className="text-sm font-semibold text-gray-700">Current State</span>
              <p className="mt-1 text-gray-900 font-medium">
                {workflow.current_state_label}
              </p>
            </div>

            <div>
              <span className="text-sm font-semibold text-gray-700">Approver Role</span>
              <p className="mt-1 text-gray-900">{workflow.approver_role}</p>
            </div>

            <div>
              <span className="text-sm font-semibold text-gray-700">Created At</span>
              <p className="mt-1 text-gray-900">
                {new Date(workflow.created_at).toLocaleString()}
              </p>
            </div>

            {workflow.delegated_to_user_id && (
              <div>
                <span className="text-sm font-semibold text-gray-700">Delegated To</span>
                <p className="mt-1 text-gray-900 font-mono text-sm">
                  {workflow.delegated_to_user_id}
                </p>
              </div>
            )}

            {workflow.escalated_to_user_id && (
              <div>
                <span className="text-sm font-semibold text-gray-700">Escalated To</span>
                <p className="mt-1 text-gray-900 font-mono text-sm">
                  {workflow.escalated_to_user_id}
                </p>
              </div>
            )}

            {workflow.completed_at && (
              <div className="col-span-2">
                <span className="text-sm font-semibold text-gray-700">Completed At</span>
                <p className="mt-1 text-gray-900">
                  {new Date(workflow.completed_at).toLocaleString()}
                </p>
              </div>
            )}
          </div>

          {/* Workflow Actions History */}
          {workflow_actions && workflow_actions.length > 0 && (
            <div className="mt-6 pt-4 border-t">
              <h3 className="text-sm font-bold text-gray-900 mb-3">Action History</h3>

              <div className="space-y-3">
                {workflow_actions.map((action) => (
                  <div
                    key={action.action_id}
                    className="bg-gray-50 rounded p-4 border-l-4 border-blue-500"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-gray-900">
                            {action.action_type_label}
                          </span>
                          {action.old_state && (
                            <span className="text-xs text-gray-600">
                              ({action.old_state} → {action.new_state})
                            </span>
                          )}
                        </div>

                        <div className="mt-1 text-sm text-gray-700">
                          <span className="font-medium">By:</span> {action.acted_by_role}
                          {action.acted_by_user_id && (
                            <span className="ml-2 font-mono text-xs">
                              {action.acted_by_user_id}
                            </span>
                          )}
                        </div>

                        {action.comment && (
                          <div className="mt-2 text-sm text-gray-600 italic">
                            "{action.comment}"
                          </div>
                        )}

                        {action.metadata_json &&
                          Object.keys(action.metadata_json).length > 0 && (
                            <div className="mt-2 bg-white rounded p-2 text-xs font-mono">
                              <pre>{JSON.stringify(action.metadata_json, null, 2)}</pre>
                            </div>
                          )}
                      </div>

                      <div className="text-right text-xs text-gray-600">
                        {new Date(action.action_at).toLocaleString()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Empty state for actions */}
          {(!workflow_actions || workflow_actions.length === 0) && (
            <div className="mt-6 pt-4 border-t text-center text-gray-500 text-sm">
              No workflow actions recorded yet
            </div>
          )}
        </div>
      )}

      {/* No Workflow Message */}
      {!workflow && decision.outcome !== 'REQUIRE_APPROVAL' && (
        <div className="bg-blue-50 border border-blue-200 rounded p-4 text-sm text-blue-800">
          <strong>No Approval Required:</strong> This decision was processed automatically
          without needing approval workflow.
        </div>
      )}

      {/* Phase A+ Note */}
      <div className="bg-yellow-50 border border-yellow-200 rounded p-3 text-sm text-yellow-800">
        <strong>Phase A+ Visibility Mode:</strong> This view shows decision and workflow data
        from the existing engine. No new features added.
      </div>
    </div>
  )
}
