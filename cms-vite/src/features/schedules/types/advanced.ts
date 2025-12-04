/**
 * Advanced Schedule Types
 * Extended type definitions for advanced scheduling features
 */

import type { RecurrenceType, RecurrencePattern } from './schedule.types'

// ========================================
// Conflict Detection Types
// ========================================

export interface CheckConflictRequest {
  playlist_id: number
  start_date: string
  end_date?: string | null
  start_time?: string | null
  end_time?: string | null
  recurrence_type: string
  exclude_schedule_id?: number | null
}

export interface ConflictSchedule {
  id: number
  name: string
  color: string
  start_date: string
  end_date?: string | null
  start_time?: string | null
  end_time?: string | null
}

export interface CheckConflictResponse {
  has_conflicts: boolean
  conflicts: ConflictSchedule[]
  message: string
}

// ========================================
// Schedule Validation Types
// ========================================

export interface ValidateScheduleRequest {
  start_date: string
  end_date?: string | null
  start_time?: string | null
  end_time?: string | null
  recurrence_type: string
  recurrence_pattern?: RecurrencePattern | null
}

export interface ValidateScheduleResponse {
  is_valid: boolean
  errors: string[]
  warnings: string[]
}

// ========================================
// Recurrence Calculation Types
// ========================================

export interface NextOccurrence {
  date: string
  start_time?: string | null
  end_time?: string | null
  is_exception: boolean
}

export interface CalculateNextOccurrenceRequest {
  from_date?: string | null
}

export interface CalculateNextOccurrenceResponse {
  schedule_id: number
  schedule_name: string
  next_occurrence?: NextOccurrence | null
  occurrences: NextOccurrence[]
}

// ========================================
// Active Schedule Types
// ========================================

export interface ActiveScheduleRequest {
  check_date?: string | null
  check_time?: string | null
}

export interface ActiveScheduleResponse {
  schedule?: any | null
  playlist_id?: number | null
  schedule_name?: string | null
  color?: string | null
  is_found: boolean
}

// ========================================
// UI State Types
// ========================================

export interface ConflictSeverity {
  type: 'critical' | 'warning' | 'info'
  label: string
  color: string
  description: string
}

export interface ValidationState {
  isValidating: boolean
  isValid: boolean
  errors: string[]
  warnings: string[]
  lastChecked?: Date
}

export interface ConflictState {
  isChecking: boolean
  hasConflicts: boolean
  conflicts: ConflictSchedule[]
  severity: 'critical' | 'warning' | 'info' | null
  lastChecked?: Date
}

export interface PreviewOccurrence {
  date: Date
  dateString: string
  startTime: string
  endTime: string
  isException: boolean
  isActive: boolean
  color: string
}


// ========================================
// Recurrence Pattern Presets
// ========================================

export interface RecurrencePreset {
  id: string
  label: string
  description: string
  type: RecurrenceType
  pattern: RecurrencePattern
  icon: string
}

export const RECURRENCE_PRESETS: RecurrencePreset[] = [
  {
    id: 'weekdays',
    label: 'Weekdays',
    description: 'Monday to Friday',
    type: 'weekly',
    pattern: {
      days_of_week: ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
    },
    icon: 'Briefcase',
  },
  {
    id: 'weekends',
    label: 'Weekends',
    description: 'Saturday and Sunday',
    type: 'weekly',
    pattern: {
      days_of_week: ['saturday', 'sunday'],
    },
    icon: 'Home',
  },
  {
    id: 'every-day',
    label: 'Every Day',
    description: 'All days of the week',
    type: 'daily',
    pattern: {
      interval: 1,
    },
    icon: 'CalendarRange',
  },
  {
    id: 'every-other-day',
    label: 'Every Other Day',
    description: 'Every 2 days',
    type: 'daily',
    pattern: {
      interval: 2,
    },
    icon: 'CalendarDays',
  },
  {
    id: 'first-of-month',
    label: 'First of Month',
    description: '1st day of each month',
    type: 'monthly',
    pattern: {
      day_of_month: 1,
    },
    icon: 'Calendar',
  },
  {
    id: 'last-of-month',
    label: 'Last of Month',
    description: 'Last day of each month',
    type: 'monthly',
    pattern: {
      last_day_of_month: true,
    },
    icon: 'CalendarX',
  },
]

// ========================================
// Helper Types
// ========================================

export interface TimeRange {
  start: string
  end: string
}

export interface DateRange {
  start: string
  end?: string | null
}

export interface ScheduleFormState {
  playlist_id: number
  start_date: string
  end_date?: string | null
  start_time: string
  end_time: string
  recurrence_type: RecurrenceType
  recurrence_pattern?: RecurrencePattern
}
