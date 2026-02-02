/**
 * Control Domain - Custom Hooks
 */

import { useState, useCallback } from 'react'
import type { AuditFilters, EventFilters, EventStatus } from '../types'

// ============================================
// Audit Filter Hook
// ============================================

export function useAuditFilters(initialFilters?: Partial<AuditFilters>) {
  const [filters, setFilters] = useState<AuditFilters>(initialFilters || {})

  const updateFilter = useCallback(<K extends keyof AuditFilters>(
    key: K,
    value: AuditFilters[K]
  ) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
  }, [])

  const resetFilters = useCallback(() => {
    setFilters(initialFilters || {})
  }, [initialFilters])

  return { filters, setFilters, updateFilter, resetFilters }
}

// ============================================
// Event Filter Hook
// ============================================

export function useEventFilters(initialFilters?: Partial<EventFilters>) {
  const [filters, setFilters] = useState<EventFilters>(initialFilters || {})

  const updateFilter = useCallback(<K extends keyof EventFilters>(
    key: K,
    value: EventFilters[K]
  ) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
  }, [])

  const resetFilters = useCallback(() => {
    setFilters(initialFilters || {})
  }, [initialFilters])

  return { filters, setFilters, updateFilter, resetFilters }
}

// ============================================
// Event Status Badge Hook
// ============================================

export function useEventStatusBadge() {
  const getStatusLabel = useCallback((status: EventStatus): string => {
    const labels: Record<EventStatus, string> = {
      PENDING: 'Pending',
      PROCESSED: 'Processed',
      FAILED: 'Failed',
      DLQ: 'Dead Letter Queue',
    }
    return labels[status] || status
  }, [])

  const getStatusVariant = useCallback((status: EventStatus): string => {
    const variants: Record<EventStatus, string> = {
      PENDING: 'warning',
      PROCESSED: 'success',
      FAILED: 'destructive',
      DLQ: 'destructive',
    }
    return variants[status] || 'outline'
  }, [])

  return { getStatusLabel, getStatusVariant }
}
