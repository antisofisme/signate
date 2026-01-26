/**
 * ATLAS_PUGUH - Global TypeScript Types
 * Following ATLAS_PANDAWA standards
 */

// ============================================
// Base Types
// ============================================

export type UUID = string
export type ISO8601 = string

// ============================================
// Domain Types
// ============================================

export type DomainType = 'iam' | 'tenant' | 'decision' | 'workflow' | 'control'

export const DOMAIN_COLORS: Record<DomainType, { primary: string; light: string }> = {
  iam: { primary: '#3B82F6', light: '#DBEAFE' },
  tenant: { primary: '#8B5CF6', light: '#EDE9FE' },
  decision: { primary: '#F59E0B', light: '#FEF3C7' },
  workflow: { primary: '#10B981', light: '#D1FAE5' },
  control: { primary: '#64748B', light: '#F1F5F9' },
}

// ============================================
// User & Auth Types
// ============================================

export interface User {
  id: UUID
  email: string
  name: string
  role: UserRole
  tenants: TenantMembership[]
  permissions: string[]
  createdAt: ISO8601
  updatedAt?: ISO8601
}

export type UserRole = 'SUPER_ADMIN' | 'ADMIN' | 'OPERATOR' | 'VIEWER'

export interface TenantMembership {
  tenantId: UUID
  tenantName: string
  role: UserRole
  permissions: string[]
}

export interface AuthState {
  user: User | null
  accessToken: string | null
  activeTenantId: UUID | null
  isAuthenticated: boolean
}

// ============================================
// Tenant Types
// ============================================

export interface Tenant {
  id: UUID
  name: string
  slug: string
  status: TenantStatus
  memberCount: number
  createdAt: ISO8601
}

export type TenantStatus = 'active' | 'suspended' | 'pending'

// ============================================
// Decision Types
// ============================================

export interface Rule {
  id: UUID
  name: string
  type: string
  description?: string
  status: RuleStatus
  version: number
  conditions: RuleCondition[]
  logic?: Record<string, unknown>
  createdBy?: string
  createdAt: ISO8601
  updatedAt: ISO8601
}

export type RuleStatus = 'DRAFT' | 'PENDING_ACTIVATION' | 'ACTIVE' | 'DEPRECATED'

export interface RuleCondition {
  field: string
  operator: 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'in' | 'nin'
  value: unknown
}

export interface Decision {
  id: UUID
  name: string
  type: string
  description?: string
  ruleId: UUID
  input: Record<string, unknown>
  output: DecisionOutput
  outcome: 'APPROVED' | 'REJECTED' | 'PENDING'
  createdAt: ISO8601
  processedAt?: ISO8601
}

export interface DecisionOutput {
  approved: boolean
  reason?: string
  score?: number
}

// ============================================
// Workflow Types
// ============================================

export interface Workflow {
  id: UUID
  type: WorkflowType
  status: WorkflowStatus
  subject: string
  description?: string
  context?: Record<string, unknown>
  requestedBy: UUID
  requestedByName: string
  assignedTo?: UUID
  assignedToName?: string
  priority: Priority
  dueAt?: ISO8601
  createdAt: ISO8601
  processedAt?: ISO8601
  completedAt?: ISO8601
}

export type WorkflowType = 'RULE_ACTIVATION' | 'USER_APPROVAL' | 'CONTENT_REVIEW'
export type WorkflowStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'ESCALATED' | 'CANCELLED'
export type Priority = 'high' | 'medium' | 'low'

export interface WorkflowAction {
  workflowId: UUID
  action: 'approve' | 'reject' | 'escalate'
  comment?: string
}

// ============================================
// Audit & Control Types
// ============================================

export interface AuditRecord {
  id: UUID
  action: string
  resource: string
  resourceId?: UUID
  actor: string
  actorId?: UUID
  changes?: Record<string, { old: unknown; new: unknown }>
  metadata?: Record<string, unknown>
  traceId?: string
  ipAddress?: string
  userAgent?: string
  timestamp: ISO8601
}

export interface SystemEvent {
  id: UUID
  type: string
  source: string
  payload?: Record<string, unknown>
  status: EventStatus
  error?: string
  retryCount?: number
  processedAt?: ISO8601
  timestamp: ISO8601
}

export type EventStatus = 'PENDING' | 'PROCESSED' | 'FAILED' | 'DLQ'

export interface DLQEvent {
  id: UUID
  eventType: string
  originalEventId: UUID
  error: string
  retryCount: number
  failedAt: ISO8601
}

// ============================================
// API Types
// ============================================

export interface PaginationParams {
  page?: number
  limit?: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

export interface PaginatedResponse<T> {
  items: T[]
  meta: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
}

export interface FilterParams {
  search?: string
  status?: string
  startDate?: ISO8601
  endDate?: ISO8601
  [key: string]: unknown
}
