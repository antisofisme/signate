/**
 * IAM Domain - Custom Hooks
 */

import { useState, useCallback, useMemo } from 'react'
import type { UserFilters, UserRole } from '../types'

// ============================================
// User Filter Hook
// ============================================

export function useUserFilters(initialFilters?: Partial<UserFilters>) {
  const [filters, setFilters] = useState<UserFilters>(initialFilters || {})

  const updateFilter = useCallback(<K extends keyof UserFilters>(
    key: K,
    value: UserFilters[K]
  ) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
  }, [])

  const resetFilters = useCallback(() => {
    setFilters(initialFilters || {})
  }, [initialFilters])

  const hasActiveFilters = useMemo(() => {
    return Object.values(filters).some((v) => v !== undefined && v !== '')
  }, [filters])

  return {
    filters,
    setFilters,
    updateFilter,
    resetFilters,
    hasActiveFilters,
  }
}

// ============================================
// Role Badge Hook
// ============================================

export function useRoleBadge() {
  const getRoleLabel = useCallback((role: UserRole): string => {
    const labels: Record<UserRole, string> = {
      SUPER_ADMIN: 'Super Admin',
      ADMIN: 'Administrator',
      OPERATOR: 'Operator',
      VIEWER: 'Viewer',
    }
    return labels[role] || role
  }, [])

  const getRoleVariant = useCallback((role: UserRole): string => {
    const variants: Record<UserRole, string> = {
      SUPER_ADMIN: 'destructive',
      ADMIN: 'default',
      OPERATOR: 'secondary',
      VIEWER: 'outline',
    }
    return variants[role] || 'outline'
  }, [])

  return { getRoleLabel, getRoleVariant }
}

// ============================================
// Permission Matrix Hook
// ============================================

export function usePermissionMatrix() {
  const [expandedModules, setExpandedModules] = useState<string[]>([])

  const toggleModule = useCallback((module: string) => {
    setExpandedModules((prev) =>
      prev.includes(module)
        ? prev.filter((m) => m !== module)
        : [...prev, module]
    )
  }, [])

  const expandAll = useCallback((modules: string[]) => {
    setExpandedModules(modules)
  }, [])

  const collapseAll = useCallback(() => {
    setExpandedModules([])
  }, [])

  return {
    expandedModules,
    toggleModule,
    expandAll,
    collapseAll,
    isExpanded: (module: string) => expandedModules.includes(module),
  }
}
