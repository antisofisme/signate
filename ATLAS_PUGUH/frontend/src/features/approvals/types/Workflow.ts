/**
 * Workflow Types - Phase A+
 * Types for approval workflow entities
 */

export interface WorkflowListItem {
  workflow_id: string
  decision_id: string
  tenant_id: string
  current_state: string
  current_state_label: string
  approver_role: string
  delegated_to_user_id: string | null
  escalated_to_user_id: string | null
  created_at: string
  completed_at: string | null
  // Nested decision object from API
  decision?: {
    decision_type: string
    context: Record<string, any>
    outcome: string
  }
}

export interface WorkflowListResponse {
  workflows: WorkflowListItem[]
  total: number
}
