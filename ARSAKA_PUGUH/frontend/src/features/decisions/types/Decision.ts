/**
 * Decision Types - Phase A+
 * Minimal types for decision visibility
 */

export interface Decision {
  decision_id: string
  tenant_id: string
  decision_type: string
  outcome: 'ALLOWED' | 'DENIED' | 'REQUIRE_APPROVAL'
  outcome_label: string
  rule_matched_id: string | null
  approval_workflow_id: string | null
  created_at: string
  context: Record<string, any>
  latency_ms: number | null
}

export interface DecisionListResponse {
  decisions: Decision[]
  total: number
}

export interface DecisionDetail {
  decision: {
    decision_id: string
    tenant_id: string
    decision_type: string
    context: Record<string, any>
    outcome: string
    outcome_label: string
    outcome_description: string
    rule_matched_id: string | null
    rule_version: string | null
    approval_workflow_id: string | null
    latency_ms: number | null
    created_at: string
    metadata_json: Record<string, any> | null
  }
  workflow: {
    workflow_id: string
    current_state: string
    current_state_label: string
    approver_role: string
    delegated_to_user_id: string | null
    escalated_to_user_id: string | null
    created_at: string
    completed_at: string | null
  } | null
  workflow_actions: Array<{
    action_id: string
    action_type: string
    action_type_label: string
    old_state: string | null
    new_state: string
    acted_by_role: string
    acted_by_user_id: string | null
    action_at: string
    comment: string | null
    metadata_json: Record<string, any> | null
  }>
}

export interface CreateDecisionRequest {
  tenant_id: string
  decision_type: string
  context: Record<string, any>
  idempotency_key?: string
  trace_id?: string
  requester_user_id?: string
}

export interface CreateDecisionResponse {
  decision_id: string
  outcome: string
  rule_matched_id: string | null
  rule_version: string | null
  workflow_id: string | null
  created_at: string
}
