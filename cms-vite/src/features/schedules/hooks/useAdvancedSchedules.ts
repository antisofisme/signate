/**
 * Advanced Schedules React Query Hooks
 * Custom hooks for advanced scheduling features
 */

import { useQuery, UseQueryOptions } from '@tanstack/react-query'
import { useState, useEffect, useMemo } from 'react'
import {
  checkScheduleConflict,
  validateSchedule,
  calculateNextOccurrence,
  getActiveSchedule,
} from '../api/scheduleAdvancedApi'
import type {
  CheckConflictRequest,
  CheckConflictResponse,
  ValidateScheduleRequest,
  ValidateScheduleResponse,
  CalculateNextOccurrenceResponse,
  ActiveScheduleResponse,
  ConflictState,
  ValidationState,
  PreviewOccurrence,
} from '../types/advanced'

// ========================================
// Schedule Conflict Detection Hook
// ========================================

export const useScheduleConflicts = (
  data: CheckConflictRequest,
  options?: {
    enabled?: boolean
    debounceMs?: number
  }
) => {
  const [debouncedData, setDebouncedData] = useState(data)

  // Debounce the data changes
  useEffect(() => {
    const timeout = setTimeout(() => {
      setDebouncedData(data)
    }, options?.debounceMs || 500)

    return () => clearTimeout(timeout)
  }, [data, options?.debounceMs])

  return useQuery({
    queryKey: ['schedule-conflicts', debouncedData],
    queryFn: () => checkScheduleConflict(debouncedData),
    enabled: options?.enabled !== false && !!debouncedData.playlist_id,
    staleTime: 30000, // 30 seconds
    retry: 1,
  })
}

// ========================================
// Schedule Validation Hook
// ========================================

export const useScheduleValidation = (
  data: ValidateScheduleRequest,
  options?: {
    enabled?: boolean
    debounceMs?: number
  }
) => {
  const [debouncedData, setDebouncedData] = useState(data)

  // Debounce the data changes
  useEffect(() => {
    const timeout = setTimeout(() => {
      setDebouncedData(data)
    }, options?.debounceMs || 500)

    return () => clearTimeout(timeout)
  }, [data, options?.debounceMs])

  return useQuery({
    queryKey: ['schedule-validation', debouncedData],
    queryFn: () => validateSchedule(debouncedData),
    enabled: options?.enabled !== false && !!debouncedData.start_date,
    staleTime: 30000, // 30 seconds
    retry: 1,
  })
}

// ========================================
// Next Occurrences Hook
// ========================================

export const useNextOccurrences = (
  scheduleId: number,
  options?: UseQueryOptions<CalculateNextOccurrenceResponse>
) => {
  return useQuery({
    queryKey: ['schedule-occurrences', scheduleId],
    queryFn: () => calculateNextOccurrence(scheduleId),
    enabled: !!scheduleId,
    staleTime: 60000, // 1 minute
    ...options,
  })
}

// ========================================
// Active Schedule Hook (with auto-refresh)
// ========================================

export const useActiveSchedule = (
  checkDate?: string,
  checkTime?: string,
  options?: {
    enabled?: boolean
    refetchInterval?: number
  }
) => {
  return useQuery({
    queryKey: ['active-schedule', checkDate, checkTime],
    queryFn: () => getActiveSchedule({ check_date: checkDate, check_time: checkTime }),
    enabled: options?.enabled !== false,
    refetchInterval: options?.refetchInterval || 60000, // 1 minute by default
    staleTime: 30000, // 30 seconds
  })
}

// ========================================
// Conflict State Hook (UI helper)
// ========================================

export const useConflictState = (
  conflictData?: CheckConflictResponse,
  isLoading?: boolean
): ConflictState => {
  return useMemo(() => {
    if (isLoading) {
      return {
        isChecking: true,
        hasConflicts: false,
        conflicts: [],
        severity: null,
      }
    }

    if (!conflictData) {
      return {
        isChecking: false,
        hasConflicts: false,
        conflicts: [],
        severity: null,
      }
    }

    // Determine severity based on conflicts
    let severity: 'critical' | 'warning' | 'info' | null = null
    if (conflictData.has_conflicts) {
      // Critical if any conflict has same priority
      const hasSamePriority = conflictData.conflicts.some(
        (c) => c.priority !== undefined
      )
      severity = hasSamePriority ? 'critical' : 'warning'
    }

    return {
      isChecking: false,
      hasConflicts: conflictData.has_conflicts,
      conflicts: conflictData.conflicts,
      severity,
      lastChecked: new Date(),
    }
  }, [conflictData, isLoading])
}

// ========================================
// Validation State Hook (UI helper)
// ========================================

export const useValidationState = (
  validationData?: ValidateScheduleResponse,
  isLoading?: boolean
): ValidationState => {
  return useMemo(() => {
    if (isLoading) {
      return {
        isValidating: true,
        isValid: false,
        errors: [],
        warnings: [],
      }
    }

    if (!validationData) {
      return {
        isValidating: false,
        isValid: false,
        errors: [],
        warnings: [],
      }
    }

    return {
      isValidating: false,
      isValid: validationData.is_valid,
      errors: validationData.errors,
      warnings: validationData.warnings,
      lastChecked: new Date(),
    }
  }, [validationData, isLoading])
}

// ========================================
// Schedule Preview Hook (calendar data)
// ========================================

export const useSchedulePreview = (
  occurrences?: CalculateNextOccurrenceResponse,
  priority: number = 0
): PreviewOccurrence[] => {
  return useMemo(() => {
    if (!occurrences?.occurrences) {
      return []
    }

    return occurrences.occurrences.map((occ) => ({
      date: new Date(occ.date),
      dateString: occ.date,
      startTime: occ.start_time || '00:00',
      endTime: occ.end_time || '23:59',
      isException: occ.is_exception,
      isActive: false, // To be determined by active schedule check
      priority,
    }))
  }, [occurrences, priority])
}

// ========================================
// Time Until Next Change Hook
// ========================================

export const useTimeUntilNextChange = (
  nextOccurrence?: { date: string; start_time?: string | null }
) => {
  const [timeRemaining, setTimeRemaining] = useState<string>('')

  useEffect(() => {
    if (!nextOccurrence) {
      setTimeRemaining('')
      return
    }

    const calculateTimeRemaining = () => {
      const now = new Date()
      const nextDate = new Date(nextOccurrence.date)

      if (nextOccurrence.start_time) {
        const [hours, minutes] = nextOccurrence.start_time.split(':')
        nextDate.setHours(parseInt(hours), parseInt(minutes))
      }

      const diff = nextDate.getTime() - now.getTime()

      if (diff <= 0) {
        setTimeRemaining('Starting now')
        return
      }

      const days = Math.floor(diff / (1000 * 60 * 60 * 24))
      const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))

      if (days > 0) {
        setTimeRemaining(`${days}d ${hours}h ${minutes}m`)
      } else if (hours > 0) {
        setTimeRemaining(`${hours}h ${minutes}m`)
      } else {
        setTimeRemaining(`${minutes}m`)
      }
    }

    calculateTimeRemaining()
    const interval = setInterval(calculateTimeRemaining, 60000) // Update every minute

    return () => clearInterval(interval)
  }, [nextOccurrence])

  return timeRemaining
}

// ========================================
// Combined Schedule Form State Hook
// ========================================

export const useCombinedScheduleState = (
  conflictRequest: CheckConflictRequest,
  validationRequest: ValidateScheduleRequest,
  scheduleId?: number
) => {
  // Fetch conflicts
  const conflictsQuery = useScheduleConflicts(conflictRequest, {
    enabled: !!conflictRequest.playlist_id,
  })

  // Fetch validation
  const validationQuery = useScheduleValidation(validationRequest, {
    enabled: !!validationRequest.start_date,
  })

  // Fetch next occurrences if editing
  const occurrencesQuery = useNextOccurrences(scheduleId!, {
    enabled: !!scheduleId,
  })

  const conflictState = useConflictState(conflictsQuery.data, conflictsQuery.isLoading)
  const validationState = useValidationState(validationQuery.data, validationQuery.isLoading)

  return {
    // Conflicts
    conflicts: conflictState,
    conflictsQuery,

    // Validation
    validation: validationState,
    validationQuery,

    // Occurrences
    occurrences: occurrencesQuery.data,
    occurrencesQuery,

    // Overall state
    isLoading: conflictsQuery.isLoading || validationQuery.isLoading,
    hasErrors: !validationState.isValid || conflictState.severity === 'critical',
    hasWarnings: validationState.warnings.length > 0 || conflictState.severity === 'warning',
  }
}
