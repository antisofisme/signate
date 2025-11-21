/**
 * Schedule Conflict Detector Component
 * Real-time conflict detection with visual indicators
 */

import { useState } from 'react'
import { AlertTriangle, AlertCircle, Info, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react'
import { useScheduleConflicts, useConflictState } from '../hooks/useAdvancedSchedules'
import type { CheckConflictRequest, ConflictSchedule } from '../types/advanced'
import type { RecurrencePattern } from '../types/schedule.types'

interface ScheduleConflictDetectorProps {
  playlistId: number
  startDate: string
  endDate?: string
  startTime?: string
  endTime?: string
  recurrenceType: string
  recurrencePattern?: RecurrencePattern
  excludeScheduleId?: number
  onConflictClick?: (scheduleId: number) => void
}

export const ScheduleConflictDetector = ({
  playlistId,
  startDate,
  endDate,
  startTime,
  endTime,
  recurrenceType,
  recurrencePattern,
  excludeScheduleId,
  onConflictClick,
}: ScheduleConflictDetectorProps) => {
  const [isExpanded, setIsExpanded] = useState(true)

  // Build conflict check request
  const conflictRequest: CheckConflictRequest = {
    playlist_id: playlistId,
    start_date: startDate,
    end_date: endDate || null,
    start_time: startTime || null,
    end_time: endTime || null,
    recurrence_type: recurrenceType,
    exclude_schedule_id: excludeScheduleId || null,
  }

  // Query for conflicts with debouncing
  const { data, isLoading } = useScheduleConflicts(conflictRequest, {
    enabled: !!playlistId && !!startDate,
    debounceMs: 500,
  })

  const conflictState = useConflictState(data, isLoading)

  // Determine visual style based on severity
  const getSeverityStyle = () => {
    switch (conflictState.severity) {
      case 'critical':
        return {
          bg: 'bg-red-50 dark:bg-red-900/20',
          border: 'border-red-200 dark:border-red-800',
          text: 'text-red-900 dark:text-red-200',
          icon: AlertCircle,
          iconColor: 'text-red-600 dark:text-red-400',
          badge: 'bg-red-100 text-red-700 dark:bg-red-800 dark:text-red-200',
        }
      case 'warning':
        return {
          bg: 'bg-yellow-50 dark:bg-yellow-900/20',
          border: 'border-yellow-200 dark:border-yellow-800',
          text: 'text-yellow-900 dark:text-yellow-200',
          icon: AlertTriangle,
          iconColor: 'text-yellow-600 dark:text-yellow-400',
          badge: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-800 dark:text-yellow-200',
        }
      case 'info':
        return {
          bg: 'bg-blue-50 dark:bg-blue-900/20',
          border: 'border-blue-200 dark:border-blue-800',
          text: 'text-blue-900 dark:text-blue-200',
          icon: Info,
          iconColor: 'text-blue-600 dark:text-blue-400',
          badge: 'bg-blue-100 text-blue-700 dark:bg-blue-800 dark:text-blue-200',
        }
      default:
        return {
          bg: 'bg-green-50 dark:bg-green-900/20',
          border: 'border-green-200 dark:border-green-800',
          text: 'text-green-900 dark:text-green-200',
          icon: Info,
          iconColor: 'text-green-600 dark:text-green-400',
          badge: 'bg-green-100 text-green-700 dark:bg-green-800 dark:text-green-200',
        }
    }
  }

  const style = getSeverityStyle()
  const Icon = style.icon

  if (isLoading) {
    return (
      <div className="p-4 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <div className="flex items-center gap-3">
          <div className="animate-spin h-5 w-5 border-2 border-purple-500 border-t-transparent rounded-full" />
          <span className="text-sm text-gray-600 dark:text-gray-400">Checking for conflicts...</span>
        </div>
      </div>
    )
  }

  return (
    <div className={`border rounded-lg ${style.bg} ${style.border}`}>
      {/* Header */}
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 flex items-center justify-between hover:opacity-80 transition-opacity"
      >
        <div className="flex items-center gap-3">
          <Icon className={`h-5 w-5 ${style.iconColor}`} />
          <div className="text-left">
            <h4 className={`text-sm font-semibold ${style.text}`}>
              {conflictState.hasConflicts ? 'Schedule Conflicts Detected' : 'No Conflicts Found'}
            </h4>
            <p className={`text-xs ${style.text} opacity-80 mt-0.5`}>
              {data?.message || 'Schedule is clear'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {conflictState.hasConflicts && (
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${style.badge}`}>
              {conflictState.conflicts.length} conflict{conflictState.conflicts.length !== 1 ? 's' : ''}
            </span>
          )}
          {isExpanded ? (
            <ChevronUp className={`h-4 w-4 ${style.iconColor}`} />
          ) : (
            <ChevronDown className={`h-4 w-4 ${style.iconColor}`} />
          )}
        </div>
      </button>

      {/* Conflict List */}
      {isExpanded && conflictState.hasConflicts && (
        <div className="px-4 pb-4 space-y-2">
          <div className="border-t border-current opacity-20 mb-3" />
          {conflictState.conflicts.map((conflict, index) => (
            <ConflictCard
              key={`${conflict.id}-${index}`}
              conflict={conflict}
              onClick={() => onConflictClick?.(conflict.id)}
            />
          ))}
        </div>
      )}

      {/* Last Checked */}
      {isExpanded && conflictState.lastChecked && (
        <div className="px-4 pb-3">
          <p className={`text-xs ${style.text} opacity-60`}>
            Last checked: {conflictState.lastChecked.toLocaleTimeString()}
          </p>
        </div>
      )}
    </div>
  )
}

// ========================================
// Conflict Card Component
// ========================================

interface ConflictCardProps {
  conflict: ConflictSchedule
  onClick?: () => void
}

const ConflictCard = ({ conflict, onClick }: ConflictCardProps) => {
  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  const formatTime = (time: string | null | undefined) => {
    if (!time) return 'All day'
    return new Date(`2000-01-01T${time}`).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h5 className="text-sm font-medium text-gray-900 dark:text-white truncate">
              {conflict.name}
            </h5>
            <span className="text-xs px-2 py-0.5 bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-200 rounded">
              Priority {conflict.priority}
            </span>
          </div>

          <div className="space-y-1">
            <p className="text-xs text-gray-600 dark:text-gray-400">
              <span className="font-medium">Date:</span>{' '}
              {formatDate(conflict.start_date)}
              {conflict.end_date && ` - ${formatDate(conflict.end_date)}`}
            </p>
            <p className="text-xs text-gray-600 dark:text-gray-400">
              <span className="font-medium">Time:</span>{' '}
              {formatTime(conflict.start_time)} - {formatTime(conflict.end_time)}
            </p>
          </div>
        </div>

        {onClick && (
          <button
            type="button"
            onClick={onClick}
            className="flex-shrink-0 p-1.5 text-gray-400 hover:text-purple-600 dark:hover:text-purple-400 transition-colors"
            title="View schedule"
          >
            <ExternalLink className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  )
}

export default ScheduleConflictDetector
