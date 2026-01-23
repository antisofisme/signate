/**
 * SDK Type Definitions
 *
 * Data transfer objects matching Core Service API contracts.
 * Source: INFRA-LAY3-002 (Core Service Implementation Standards)
 */

export interface CreateDecisionRequest {
  tenant_id: string;
  decision_type: string;
  context: Record<string, any>;
  idempotency_key?: string;
  trace_id?: string;
  requester_user_id?: string;
}

export interface CreateDecisionResponse {
  decision_id: string;
  outcome: "ALLOWED" | "DENIED" | "REQUIRE_APPROVAL";
  rule_matched_id?: string;
  rule_version?: string;
  workflow_id?: string;
  created_at: string;
}

export interface ApproveWorkflowRequest {
  tenant_id: string;
  approver_role: string;
  acted_by_user_id?: string;
  comment?: string;
}

export interface ApproveWorkflowResponse {
  workflow_id: string;
  current_state: string;
  completed_at: string;
}

export interface RejectWorkflowRequest {
  tenant_id: string;
  approver_role: string;
  acted_by_user_id?: string;
  reason?: string;
}

export interface RejectWorkflowResponse {
  workflow_id: string;
  current_state: string;
  completed_at: string;
}

export interface DelegateWorkflowRequest {
  tenant_id: string;
  approver_role: string;
  delegated_to_user_id: string;
  acted_by_user_id?: string;
  reason?: string;
}

export interface DelegateWorkflowResponse {
  workflow_id: string;
  current_state: string;
  delegated_to_user_id: string;
}

export interface EscalateWorkflowRequest {
  tenant_id: string;
  escalated_to_role: string;
  escalation_reason: string;
}

export interface EscalateWorkflowResponse {
  workflow_id: string;
  current_state: string;
  escalated_to_role: string;
}

export interface ErrorResponse {
  error_code: string;
  message: string;
  details?: Record<string, any>;
}
