/**
 * Decision Domain - TypeScript Types
 */

// Re-export from shared
export type { Rule, RuleStatus, Decision, DecisionOutput, RuleCondition } from '@/shared/types'

// Import for local use
import type { RuleStatus, RuleCondition } from '@/shared/types'

// Domain-specific types
export interface RuleFilters {
  search?: string
  status?: RuleStatus
  type?: string
}

export interface RuleFormData {
  name: string
  type: string
  description?: string
  conditions: RuleCondition[]
}

// Simplified type for creating rule draft (conditions added later)
export interface CreateRuleDraftRequest {
  name: string
  type: string
  description?: string
}

export interface ActivationRequest {
  ruleId: string
  version: number
  reason: string
}

export interface UpdateRuleRequest {
  name?: string
  description?: string
  conditions?: Record<string, unknown>
  action?: Record<string, unknown>
}

export interface DecisionFilters {
  ruleId?: string
  type?: string
  approved?: boolean
  startDate?: string
  endDate?: string
}

// Constants
export const RULE_STATUS_LABELS: Record<RuleStatus, string> = {
  DRAFT: 'Draft',
  PENDING_ACTIVATION: 'Pending Activation',
  ACTIVE: 'Active',
  DEPRECATED: 'Deprecated',
}

export const RULE_STATUS_COLORS: Record<RuleStatus, string> = {
  DRAFT: 'secondary',
  PENDING_ACTIVATION: 'warning',
  ACTIVE: 'success',
  DEPRECATED: 'outline',
}
