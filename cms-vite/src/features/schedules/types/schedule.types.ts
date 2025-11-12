/**
 * Schedule Types
 * Type definitions for content scheduling system
 */

// Recurrence types
export type RecurrenceType = 'once' | 'daily' | 'weekly' | 'monthly' | 'custom'

// Days of week
export type DayOfWeek = 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday' | 'sunday'

// Priority levels
export type PriorityLevel = 'low' | 'normal' | 'high' | 'critical'

// Schedule status
export type ScheduleStatus = 'active' | 'inactive' | 'expired' | 'paused'

// Base schedule interface
export interface Schedule {
  id: number
  name: string
  description?: string
  playlist_id: number
  playlist_name?: string
  device_ids: number[]
  device_names?: string[]
  start_date: string
  end_date?: string
  start_time: string
  end_time: string
  recurrence_type: RecurrenceType
  recurrence_pattern?: RecurrencePattern
  priority: PriorityLevel
  status: ScheduleStatus
  exception_dates?: string[]
  timezone: string
  created_at: string
  updated_at: string
  created_by?: number
  last_run?: string
  next_run?: string
}

// Recurrence pattern details
export interface RecurrencePattern {
  // Daily: every N days
  interval?: number

  // Weekly: which days of week
  days_of_week?: DayOfWeek[]

  // Monthly: which day of month (1-31) or last day
  day_of_month?: number
  last_day_of_month?: boolean

  // Custom: cron expression
  cron_expression?: string
}

// Priority level information
export interface PriorityInfo {
  level: PriorityLevel
  label: string
  color: string
  icon: string
  description: string
  weight: number
}

export const PRIORITY_LEVELS: Record<PriorityLevel, PriorityInfo> = {
  low: {
    level: 'low',
    label: 'Low Priority',
    color: 'gray',
    icon: 'ChevronDown',
    description: 'Lowest priority, runs if no other schedules',
    weight: 1,
  },
  normal: {
    level: 'normal',
    label: 'Normal Priority',
    color: 'blue',
    icon: 'ChevronRight',
    description: 'Standard priority for regular content',
    weight: 2,
  },
  high: {
    level: 'high',
    label: 'High Priority',
    color: 'orange',
    icon: 'ChevronUp',
    description: 'High priority, runs before normal schedules',
    weight: 3,
  },
  critical: {
    level: 'critical',
    label: 'Critical Priority',
    color: 'red',
    icon: 'AlertCircle',
    description: 'Highest priority, always runs',
    weight: 4,
  },
}

// Recurrence type information
export interface RecurrenceTypeInfo {
  type: RecurrenceType
  label: string
  icon: string
  description: string
}

export const RECURRENCE_TYPES: Record<RecurrenceType, RecurrenceTypeInfo> = {
  once: {
    type: 'once',
    label: 'One Time',
    icon: 'Calendar',
    description: 'Schedule runs only once',
  },
  daily: {
    type: 'daily',
    label: 'Daily',
    icon: 'Calendar',
    description: 'Repeats every day or every N days',
  },
  weekly: {
    type: 'weekly',
    label: 'Weekly',
    icon: 'CalendarDays',
    description: 'Repeats on specific days of the week',
  },
  monthly: {
    type: 'monthly',
    label: 'Monthly',
    icon: 'CalendarRange',
    description: 'Repeats on specific day of month',
  },
  custom: {
    type: 'custom',
    label: 'Custom',
    icon: 'Settings',
    description: 'Custom schedule using cron expression',
  },
}

// Days of week information
export const DAYS_OF_WEEK: Record<DayOfWeek, { label: string; short: string; index: number }> = {
  monday: { label: 'Monday', short: 'Mon', index: 1 },
  tuesday: { label: 'Tuesday', short: 'Tue', index: 2 },
  wednesday: { label: 'Wednesday', short: 'Wed', index: 3 },
  thursday: { label: 'Thursday', short: 'Thu', index: 4 },
  friday: { label: 'Friday', short: 'Fri', index: 5 },
  saturday: { label: 'Saturday', short: 'Sat', index: 6 },
  sunday: { label: 'Sunday', short: 'Sun', index: 0 },
}

// Timezone information (common timezones)
export const TIMEZONES = [
  { value: 'UTC', label: 'UTC (Universal Time Coordinated)' },
  { value: 'Asia/Jakarta', label: 'Asia/Jakarta (WIB - GMT+7)' },
  { value: 'Asia/Makassar', label: 'Asia/Makassar (WITA - GMT+8)' },
  { value: 'Asia/Jayapura', label: 'Asia/Jayapura (WIT - GMT+9)' },
  { value: 'Asia/Singapore', label: 'Asia/Singapore (SGT - GMT+8)' },
  { value: 'Asia/Tokyo', label: 'Asia/Tokyo (JST - GMT+9)' },
  { value: 'Asia/Seoul', label: 'Asia/Seoul (KST - GMT+9)' },
  { value: 'Asia/Bangkok', label: 'Asia/Bangkok (ICT - GMT+7)' },
  { value: 'Asia/Shanghai', label: 'Asia/Shanghai (CST - GMT+8)' },
  { value: 'America/New_York', label: 'America/New_York (EST - GMT-5)' },
  { value: 'Europe/London', label: 'Europe/London (GMT - GMT+0)' },
]

// API Request/Response types
export interface ScheduleFilters {
  playlist_id?: number
  device_id?: number
  status?: ScheduleStatus
  priority?: PriorityLevel
  recurrence_type?: RecurrenceType
  search?: string
  start_date?: string
  end_date?: string
}

export interface ScheduleListResponse {
  schedules: Schedule[]
  total: number
}

export interface CreateScheduleRequest {
  name: string
  description?: string
  playlist_id: number
  device_ids: number[]
  start_date: string
  end_date?: string
  start_time: string
  end_time: string
  recurrence_type: RecurrenceType
  recurrence_pattern?: RecurrencePattern
  priority: PriorityLevel
  exception_dates?: string[]
  timezone: string
}

export interface UpdateScheduleRequest {
  name?: string
  description?: string
  device_ids?: number[]
  start_date?: string
  end_date?: string
  start_time?: string
  end_time?: string
  recurrence_pattern?: RecurrencePattern
  priority?: PriorityLevel
  status?: ScheduleStatus
  exception_dates?: string[]
  timezone?: string
}

// Schedule conflict detection
export interface ScheduleConflict {
  schedule_id: number
  schedule_name: string
  conflict_type: 'time_overlap' | 'device_overlap' | 'priority_conflict'
  severity: 'warning' | 'error'
  message: string
  conflicting_schedule_id?: number
  conflicting_schedule_name?: string
  resolution_suggestion?: string
}

export interface ConflictCheckRequest {
  playlist_id: number
  device_ids: number[]
  start_date: string
  end_date?: string
  start_time: string
  end_time: string
  recurrence_type: RecurrenceType
  recurrence_pattern?: RecurrencePattern
  exclude_schedule_id?: number
}

export interface ConflictCheckResponse {
  has_conflicts: boolean
  conflicts: ScheduleConflict[]
}

// Calendar event for visualization
export interface CalendarEvent {
  id: number
  title: string
  start: Date
  end: Date
  schedule: Schedule
  isException?: boolean
  color?: string
}

// Schedule occurrence (for calendar)
export interface ScheduleOccurrence {
  schedule_id: number
  schedule_name: string
  playlist_name: string
  occurrence_date: string
  start_time: string
  end_time: string
  priority: PriorityLevel
  devices: number[]
}

// Get occurrences request
export interface GetOccurrencesRequest {
  start_date: string
  end_date: string
  device_id?: number
  playlist_id?: number
}

export interface GetOccurrencesResponse {
  occurrences: ScheduleOccurrence[]
  total: number
}
