/**
 * Schedule Types
 * Type definitions for content scheduling system
 */

// Recurrence types
export type RecurrenceType = 'once' | 'daily' | 'weekly' | 'monthly' | 'custom'

// Days of week
export type DayOfWeek = 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday' | 'sunday'

// Schedule mode - how the schedule behaves when active
export type ScheduleMode = 'override' | 'rotate'

// Schedule status
export type ScheduleStatus = 'active' | 'inactive' | 'expired' | 'paused'

// Target device info (from junction table)
export interface TargetDeviceInfo {
  id: number
  device_name: string
}

// Target tag info (from junction table)
export interface TargetTagInfo {
  id: number
  name: string
}

// Base schedule interface
export interface Schedule {
  id: number
  name: string
  description?: string
  playlist_id: number
  playlist_name?: string
  start_date: string
  end_date?: string
  start_time: string
  end_time: string
  recurrence_type: RecurrenceType | string
  recurrence_pattern?: RecurrencePattern
  color: string  // Hex color for calendar display (e.g. #3B82F6)
  mode: ScheduleMode
  is_active: boolean // From backend
  status?: ScheduleStatus // Derived from is_active for UI display
  exception_dates?: string[]
  timezone?: string
  created_at: string
  updated_at: string
  // Audit trail fields (Migration 046)
  created_by_id?: number
  updated_by_id?: number
  last_run?: string
  next_run?: string

  // Targeting fields (Migration 078)
  device_ids?: number[]         // DEPRECATED: Legacy JSONB array
  tag_ids?: number[]            // DEPRECATED: Legacy JSONB array
  target_devices?: TargetDeviceInfo[]  // New: From junction table with device info
  target_tags?: TargetTagInfo[]        // New: From junction table with tag info
  applies_to_all?: boolean      // Apply to all devices in organization
}

// Helper to derive status from is_active and dates
export const getScheduleStatus = (schedule: Schedule): ScheduleStatus => {
  // Check if expired (end_date passed)
  if (schedule.end_date) {
    const endDate = new Date(schedule.end_date)
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    if (endDate < today) {
      return 'expired'
    }
  }
  // Use is_active for active/inactive
  return schedule.is_active ? 'active' : 'inactive'
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

// Default schedule color
export const DEFAULT_SCHEDULE_COLOR = '#3B82F6'  // Tailwind blue-500

// Schedule mode information
export interface ScheduleModeInfo {
  mode: ScheduleMode
  label: string
  icon: string
  description: string
  color: string
}

export const SCHEDULE_MODES: Record<ScheduleMode, ScheduleModeInfo> = {
  override: {
    mode: 'override',
    label: 'Override',
    icon: 'Ban',
    description: 'Stop all other content when this schedule is active. Only this scheduled content will play.',
    color: 'red',
  },
  rotate: {
    mode: 'rotate',
    label: 'Rotate',
    icon: 'RefreshCw',
    description: 'Play alongside other content. Takes turns in rotation with other active content.',
    color: 'blue',
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
  start_date: string
  end_date?: string
  start_time: string
  end_time: string
  recurrence_type: RecurrenceType | string
  recurrence_pattern?: RecurrencePattern
  color?: string  // Hex color for calendar display
  mode: ScheduleMode
  exception_dates?: string[]
  is_active?: boolean
  // Targeting fields (use target_devices/target_tags, device_ids/tag_ids are deprecated)
  target_devices?: number[]     // Device IDs to target
  target_tags?: number[]        // Tag IDs to target
  applies_to_all?: boolean      // Apply to all devices
  device_ids?: number[]         // DEPRECATED: Use target_devices
  tag_ids?: number[]            // DEPRECATED: Use target_tags
}

export interface UpdateScheduleRequest {
  name?: string
  description?: string
  start_date?: string
  end_date?: string
  start_time?: string
  end_time?: string
  recurrence_type?: RecurrenceType | string
  recurrence_pattern?: RecurrencePattern
  color?: string  // Hex color for calendar display
  mode?: ScheduleMode
  status?: ScheduleStatus
  exception_dates?: string[]
  is_active?: boolean
  // Targeting fields (use target_devices/target_tags, device_ids/tag_ids are deprecated)
  target_devices?: number[]     // Device IDs to target
  target_tags?: number[]        // Tag IDs to target
  applies_to_all?: boolean      // Apply to all devices
  device_ids?: number[]         // DEPRECATED: Use target_devices
  tag_ids?: number[]            // DEPRECATED: Use target_tags
}

// Schedule conflict detection
export interface ScheduleConflict {
  schedule_id: number
  schedule_name: string
  conflict_type: 'time_overlap' | 'device_overlap' | 'mode_conflict'
  severity: 'warning' | 'error'
  message: string
  conflicting_schedule_id?: number
  conflicting_schedule_name?: string
  resolution_suggestion?: string
}

export interface ConflictCheckRequest {
  playlist_id: number
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
  color: string
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
