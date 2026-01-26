/**
 * Workflow Domain - Custom Hooks
 */

import { useState, useCallback } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import type { WorkflowFilters, Priority } from '../types'

// ============================================
// Filter Hook
// ============================================

export function useWorkflowFilters(initialFilters?: Partial<WorkflowFilters>) {
  const [filters, setFilters] = useState<WorkflowFilters>(initialFilters || {})

  const updateFilter = useCallback(<K extends keyof WorkflowFilters>(
    key: K,
    value: WorkflowFilters[K]
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
// Approve Form Hook
// ============================================

const approveSchema = z.object({
  comment: z.string().optional(),
})

export type ApproveFormData = z.infer<typeof approveSchema>

export function useApproveForm() {
  return useForm<ApproveFormData>({
    resolver: zodResolver(approveSchema),
    defaultValues: {
      comment: '',
    },
  })
}

// ============================================
// Reject Form Hook
// ============================================

const rejectSchema = z.object({
  reason: z.string().min(10, 'Reason must be at least 10 characters'),
})

export type RejectFormData = z.infer<typeof rejectSchema>

export function useRejectForm() {
  return useForm<RejectFormData>({
    resolver: zodResolver(rejectSchema),
    defaultValues: {
      reason: '',
    },
  })
}

// ============================================
// Priority Badge Hook
// ============================================

export function usePriorityBadge() {
  const getBadgeVariant = useCallback((priority: Priority) => {
    switch (priority) {
      case 'high':
        return 'destructive'
      case 'medium':
        return 'warning'
      case 'low':
        return 'secondary'
      default:
        return 'outline'
    }
  }, [])

  return { getBadgeVariant }
}
