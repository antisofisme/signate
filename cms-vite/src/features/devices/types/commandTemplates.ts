/**
 * Command Templates & Scheduled Commands Types
 * Enhanced command management types
 */

import type { CommandType } from './commands'

// Command Template
export interface CommandTemplate {
  id: number
  name: string
  description?: string
  command_type: CommandType
  command_data?: Record<string, any>
  parameters?: Record<string, any>
  priority?: number
  expires_in_minutes?: number
  tags?: string[]
  is_favorite?: boolean
  usage_count?: number
  organization_id: number
  created_by?: number
  created_at: string
  updated_at?: string
}

export interface CreateCommandTemplateRequest {
  name: string
  description?: string
  command_type: CommandType
  command_data?: Record<string, any>
  parameters?: Record<string, any>
  priority?: number
  expires_in_minutes?: number
  tags?: string[]
  is_favorite?: boolean
}

export interface UpdateCommandTemplateRequest {
  name?: string
  description?: string
  command_data?: Record<string, any>
  parameters?: Record<string, any>
  priority?: number
  expires_in_minutes?: number
  tags?: string[]
  is_favorite?: boolean
}

// Scheduled Command
export type ScheduleFrequency = 'once' | 'daily' | 'weekly' | 'monthly'

export interface ScheduledCommand {
  id: number
  name: string
  description?: string
  device_ids: number[]
  device_group_ids?: number[]
  command_type: CommandType
  command_data?: Record<string, any>
  parameters?: Record<string, any>
  priority?: number
  frequency: ScheduleFrequency
  schedule_time: string // HH:MM format
  schedule_date?: string // For 'once' frequency
  schedule_days?: number[] // 0-6 for 'weekly', 1-31 for 'monthly'
  timezone?: string
  is_active: boolean
  last_run?: string
  next_run?: string
  run_count?: number
  organization_id: number
  created_by?: number
  created_at: string
  updated_at?: string
}

export interface CreateScheduledCommandRequest {
  name: string
  description?: string
  device_ids: number[]
  device_group_ids?: number[]
  command_type: CommandType
  command_data?: Record<string, any>
  parameters?: Record<string, any>
  priority?: number
  frequency: ScheduleFrequency
  schedule_time: string
  schedule_date?: string
  schedule_days?: number[]
  timezone?: string
  is_active?: boolean
}

export interface UpdateScheduledCommandRequest {
  name?: string
  description?: string
  device_ids?: number[]
  device_group_ids?: number[]
  command_data?: Record<string, any>
  parameters?: Record<string, any>
  priority?: number
  frequency?: ScheduleFrequency
  schedule_time?: string
  schedule_date?: string
  schedule_days?: number[]
  timezone?: string
  is_active?: boolean
}

// Command History Filters
export interface CommandHistoryFilters {
  device_id?: number
  device_group_id?: number
  command_type?: CommandType
  status?: string
  date_from?: string
  date_to?: string
  created_by?: number
  search?: string
  skip?: number
  limit?: number
}

// Command Statistics
export interface CommandStatistics {
  total_commands: number
  by_status: {
    pending: number
    sent: number
    executed: number
    failed: number
    expired: number
  }
  by_type: Record<CommandType, number>
  by_device: Array<{
    device_id: number
    device_name: string
    total_commands: number
    success_rate: number
  }>
  success_rate: number
  average_execution_time_ms?: number
  most_used_command: CommandType
  recent_failures: number
}

// Bulk Command Result
export interface BulkCommandResult {
  total_devices: number
  success_count: number
  failure_count: number
  commands: Array<{
    device_id: number
    device_name: string
    command_id?: number
    status: 'success' | 'failed'
    error?: string
  }>
}

// Command Type Info
export interface CommandTypeInfo {
  type: CommandType
  label: string
  description: string
  icon: string // lucide-react icon name
  color: string
  requiresParameters: boolean
  commonParameters?: Record<string, any>
  examples?: string[]
}

export const COMMAND_TYPE_INFO: Record<CommandType, CommandTypeInfo> = {
  reboot: {
    type: 'reboot',
    label: 'Reboot Device',
    description: 'Restart the device completely',
    icon: 'RotateCw',
    color: 'orange',
    requiresParameters: false,
    examples: ['System maintenance', 'After software update'],
  },
  refresh_content: {
    type: 'refresh_content',
    label: 'Refresh Content',
    description: 'Reload current content from server',
    icon: 'RefreshCw',
    color: 'blue',
    requiresParameters: false,
  },
  update_settings: {
    type: 'update_settings',
    label: 'Update Settings',
    description: 'Update device configuration settings',
    icon: 'Settings',
    color: 'gray',
    requiresParameters: true,
    commonParameters: { setting_key: '', setting_value: '' },
  },
  clear_cache: {
    type: 'clear_cache',
    label: 'Clear Cache',
    description: 'Clear all cached data',
    icon: 'Trash2',
    color: 'red',
    requiresParameters: false,
  },
  screenshot: {
    type: 'screenshot',
    label: 'Take Screenshot',
    description: 'Capture current screen',
    icon: 'Camera',
    color: 'purple',
    requiresParameters: false,
  },
  update_playlist: {
    type: 'update_playlist',
    label: 'Update Playlist',
    description: 'Refresh playlist content',
    icon: 'Music',
    color: 'green',
    requiresParameters: true,
    commonParameters: { playlist_id: 0 },
  },
  reset: {
    type: 'reset',
    label: 'Factory Reset',
    description: 'Reset device to factory settings',
    icon: 'AlertTriangle',
    color: 'red',
    requiresParameters: false,
  },
  refresh: {
    type: 'refresh',
    label: 'Refresh Display',
    description: 'Refresh the display',
    icon: 'Monitor',
    color: 'blue',
    requiresParameters: false,
  },
  reload: {
    type: 'reload',
    label: 'Reload Application',
    description: 'Reload the player application',
    icon: 'RotateCcw',
    color: 'blue',
    requiresParameters: false,
  },
  volume: {
    type: 'volume',
    label: 'Set Volume',
    description: 'Adjust device volume',
    icon: 'Volume2',
    color: 'blue',
    requiresParameters: true,
    commonParameters: { volume_level: 50 },
  },
  brightness: {
    type: 'brightness',
    label: 'Set Brightness',
    description: 'Adjust screen brightness',
    icon: 'Sun',
    color: 'yellow',
    requiresParameters: true,
    commonParameters: { brightness_level: 75 },
  },
  speed_test: {
    type: 'speed_test',
    label: 'Network Speed Test',
    description: 'Test network connection speed',
    icon: 'Wifi',
    color: 'cyan',
    requiresParameters: false,
  },
  update_content: {
    type: 'update_content',
    label: 'Update Content',
    description: 'Update content from server',
    icon: 'Download',
    color: 'green',
    requiresParameters: false,
  },
}
