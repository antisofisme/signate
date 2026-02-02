/**
 * Tenant Domain - Custom Hooks
 */

import { useState, useCallback } from 'react'
import type { TenantFilters, TenantStatus } from '../types'

// ============================================
// Tenant Filter Hook
// ============================================

export function useTenantFilters(initialFilters?: Partial<TenantFilters>) {
  const [filters, setFilters] = useState<TenantFilters>(initialFilters || {})

  const updateFilter = useCallback(<K extends keyof TenantFilters>(
    key: K,
    value: TenantFilters[K]
  ) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
  }, [])

  const resetFilters = useCallback(() => {
    setFilters(initialFilters || {})
  }, [initialFilters])

  return {
    filters,
    setFilters,
    updateFilter,
    resetFilters,
  }
}

// ============================================
// Tenant Status Badge Hook
// ============================================

export function useTenantStatusBadge() {
  const getStatusLabel = useCallback((status: TenantStatus): string => {
    const labels: Record<TenantStatus, string> = {
      active: 'Active',
      suspended: 'Suspended',
      pending: 'Pending',
    }
    return labels[status] || status
  }, [])

  const getStatusVariant = useCallback((status: TenantStatus): string => {
    const variants: Record<TenantStatus, string> = {
      active: 'success',
      suspended: 'destructive',
      pending: 'warning',
    }
    return variants[status] || 'outline'
  }, [])

  return { getStatusLabel, getStatusVariant }
}
