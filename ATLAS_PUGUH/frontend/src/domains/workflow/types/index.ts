/**
 * Workflow Domain - TypeScript Types
 */

import type { WorkflowStatus, Priority } from '@/shared/types'

// Re-export from shared
export type { Workflow, WorkflowType, WorkflowStatus, WorkflowAction, Priority } from '@/shared/types'

// Domain-specific types
export interface WorkflowFilters {
  status?: WorkflowStatus
  priority?: Priority
  assignedTo?: string
  search?: string
}

export interface WorkflowStats {
  pending: number
  highPriority: number
  approvedToday: number
  rejectedToday: number
}

export const WORKFLOW_STATUS_LABELS: Record<WorkflowStatus, string> = {
  PENDING: 'Pending',
  APPROVED: 'Approved',
  REJECTED: 'Rejected',
  ESCALATED: 'Escalated',
  CANCELLED: 'Cancelled',
}

export const WORKFLOW_STATUS_COLORS: Record<WorkflowStatus, string> = {
  PENDING: 'warning',
  APPROVED: 'success',
  REJECTED: 'destructive',
  ESCALATED: 'info',
  CANCELLED: 'secondary',
}

// Badge variants compatible with DomainPage badge prop
export const WORKFLOW_STATUS_BADGE_VARIANTS: Record<WorkflowStatus, 'default' | 'success' | 'warning' | 'error' | 'info'> = {
  PENDING: 'warning',
  APPROVED: 'success',
  REJECTED: 'error',
  ESCALATED: 'info',
  CANCELLED: 'default',
}
