/**
 * Audit Event Types - Phase A+
 * Types for audit trail events
 */

export interface AuditEvent {
  event_id: string
  event_type: string
  entity_type: string
  entity_id: string
  actor_type: string
  actor_id: string | null
  event_at: string
  event_data: Record<string, any>
}

export interface AuditEventListResponse {
  events: AuditEvent[]
  total: number
  note?: string
}
