/**
 * Rule Types - Phase A+
 */

export interface Rule {
  rule_id: string
  tenant_id: string
  decision_type: string
  rule_name: string
  description?: string
  conditions: Record<string, any>
  action: {
    outcome: 'ALLOWED' | 'DENIED' | 'REQUIRE_APPROVAL'
    approver_role?: string
    reason?: string
  }
  version: string
  status: 'DRAFT' | 'ACTIVE' | 'DEPRECATED' | 'DELETED'
  evaluation_sequence: number
  functional_area_id?: string  // NEW: Governance metadata (UI grouping only, NOT used in decision logic)
  created_at: string
  activated_at?: string
  deactivated_at?: string
}

export interface RuleListResponse {
  rules: Rule[]
  total: number
}

export interface CreateRuleRequest {
  decision_type: string
  rule_name: string
  description?: string
  conditions: Record<string, any>
  action: {
    outcome: 'ALLOWED' | 'DENIED' | 'REQUIRE_APPROVAL'
    approver_role?: string
    reason?: string
  }
  evaluation_sequence?: number
  functional_area_id?: string  // NEW: Optional governance metadata
}
