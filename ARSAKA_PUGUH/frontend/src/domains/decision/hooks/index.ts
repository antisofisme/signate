/**
 * Decision Domain - Custom Hooks
 */

import { useState, useCallback } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import type { RuleFilters, RuleStatus } from '../types'

// ============================================
// Rule Filter Hook
// ============================================

export function useRuleFilters(initialFilters?: Partial<RuleFilters>) {
  const [filters, setFilters] = useState<RuleFilters>(initialFilters || {})

  const updateFilter = useCallback(<K extends keyof RuleFilters>(
    key: K,
    value: RuleFilters[K]
  ) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
  }, [])

  const resetFilters = useCallback(() => {
    setFilters(initialFilters || {})
  }, [initialFilters])

  return { filters, setFilters, updateFilter, resetFilters }
}

// ============================================
// Rule Status Badge Hook
// ============================================

export function useRuleStatusBadge() {
  const getStatusLabel = useCallback((status: RuleStatus): string => {
    const labels: Record<RuleStatus, string> = {
      DRAFT: 'Draft',
      PENDING_ACTIVATION: 'Pending',
      ACTIVE: 'Active',
      DEPRECATED: 'Deprecated',
    }
    return labels[status] || status
  }, [])

  const getStatusVariant = useCallback((status: RuleStatus): string => {
    const variants: Record<RuleStatus, string> = {
      DRAFT: 'secondary',
      PENDING_ACTIVATION: 'warning',
      ACTIVE: 'success',
      DEPRECATED: 'outline',
    }
    return variants[status] || 'outline'
  }, [])

  return { getStatusLabel, getStatusVariant }
}

// ============================================
// Create Rule Form Hook
// ============================================

const ruleFormSchema = z.object({
  name: z.string().min(3, 'Name must be at least 3 characters'),
  type: z.string().min(1, 'Type is required'),
  description: z.string().optional(),
})

export type RuleFormSchemaData = z.infer<typeof ruleFormSchema>

export function useRuleForm() {
  return useForm<RuleFormSchemaData>({
    resolver: zodResolver(ruleFormSchema),
    defaultValues: {
      name: '',
      type: '',
      description: '',
    },
  })
}

// ============================================
// Edit Rule Form Hook
// ============================================

const editRuleFormSchema = z.object({
  name: z.string().min(3, 'Name must be at least 3 characters'),
  description: z.string().optional(),
  conditions: z.string().refine(
    (val) => {
      if (!val || val.trim() === '') return true
      try {
        JSON.parse(val)
        return true
      } catch {
        return false
      }
    },
    { message: 'Conditions must be valid JSON' }
  ),
  action: z.string().refine(
    (val) => {
      if (!val || val.trim() === '') return true
      try {
        JSON.parse(val)
        return true
      } catch {
        return false
      }
    },
    { message: 'Action must be valid JSON' }
  ),
})

export type EditRuleFormData = z.infer<typeof editRuleFormSchema>

export function useEditRuleForm(defaultValues?: Partial<EditRuleFormData>) {
  return useForm<EditRuleFormData>({
    resolver: zodResolver(editRuleFormSchema),
    defaultValues: {
      name: defaultValues?.name || '',
      description: defaultValues?.description || '',
      conditions: defaultValues?.conditions || '{}',
      action: defaultValues?.action || '{}',
    },
  })
}

// ============================================
// Activation Request Form Hook
// ============================================

const activationSchema = z.object({
  reason: z.string().min(10, 'Please provide a reason for activation (min 10 characters)'),
})

export type ActivationFormData = z.infer<typeof activationSchema>

export function useActivationForm() {
  return useForm<ActivationFormData>({
    resolver: zodResolver(activationSchema),
    defaultValues: {
      reason: '',
    },
  })
}
