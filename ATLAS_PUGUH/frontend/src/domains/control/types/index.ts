/**
 * Control Domain - TypeScript Types
 */

// Re-export from shared for external use
export type { AuditRecord, SystemEvent, EventStatus, DLQEvent } from '@/shared/types'

// Import for local use
import type { EventStatus } from '@/shared/types'

// Domain-specific types
export interface AuditFilters {
  action?: string
  actor?: string
  resource?: string
  startDate?: string
  endDate?: string
}

export interface EventFilters {
  type?: string
  source?: string
  status?: EventStatus
  startDate?: string
  endDate?: string
}

export interface MetricsSummary {
  decisionsToday: number
  decisionsChange: number
  approvalRate: number
  avgResponseTime: number
  dlqSize: number
}

export interface MetricsTrend {
  date: string
  decisions: number
  approvals: number
  rejections: number
}

// Constants
export const EVENT_STATUS_LABELS: Record<EventStatus, string> = {
  PENDING: 'Pending',
  PROCESSED: 'Processed',
  FAILED: 'Failed',
  DLQ: 'Dead Letter Queue',
}

export const EVENT_STATUS_COLORS: Record<EventStatus, string> = {
  PENDING: 'warning',
  PROCESSED: 'success',
  FAILED: 'destructive',
  DLQ: 'destructive',
}

// Badge variants compatible with DomainPage badge prop
export const EVENT_STATUS_BADGE_VARIANTS: Record<EventStatus, 'default' | 'success' | 'warning' | 'error' | 'info'> = {
  PENDING: 'warning',
  PROCESSED: 'success',
  FAILED: 'error',
  DLQ: 'error',
}
