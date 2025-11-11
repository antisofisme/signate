/**
 * Conflict Detector Component
 * Check and display schedule conflicts
 */

import { useEffect } from 'react'
import { useCheckConflicts } from '../hooks/useSchedules'
import type { RecurrenceType, RecurrencePattern } from '../types/schedule.types'

interface ConflictDetectorProps {
  playlistId: number
  deviceIds: number[]
  startDate: string
  endDate?: string
  startTime: string
  endTime: string
  recurrenceType: RecurrenceType
  recurrencePattern?: RecurrencePattern
  excludeScheduleId?: number
}

export const ConflictDetector = ({
  playlistId,
  deviceIds,
  startDate,
  endDate,
  startTime,
  endTime,
  recurrenceType,
  recurrencePattern,
  excludeScheduleId,
}: ConflictDetectorProps) => {
  const checkConflicts = useCheckConflicts()

  useEffect(() => {
    // Check conflicts when props change
    if (playlistId && deviceIds.length > 0 && startDate && startTime && endTime) {
      checkConflicts.mutate({
        playlist_id: playlistId,
        device_ids: deviceIds,
        start_date: startDate,
        end_date: endDate,
        start_time: startTime,
        end_time: endTime,
        recurrence_type: recurrenceType,
        recurrence_pattern: recurrencePattern,
        exclude_schedule_id: excludeScheduleId,
      })
    }
  }, [playlistId, deviceIds, startDate, endDate, startTime, endTime, recurrenceType, recurrencePattern, excludeScheduleId])

  if (checkConflicts.isPending) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <div className="flex items-center gap-3">
          <div className="animate-spin h-5 w-5 border-3 border-gray-600 border-t-transparent rounded-full"></div>
          <p className="text-sm text-gray-700">Checking for conflicts...</p>
        </div>
      </div>
    )
  }

  if (checkConflicts.error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <span className="text-xl">❌</span>
          <div>
            <h4 className="text-sm font-semibold text-red-900">Error checking conflicts</h4>
            <p className="text-xs text-red-700 mt-1">
              {(checkConflicts.error as any)?.response?.data?.detail || 'Failed to check conflicts'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  const data = checkConflicts.data

  if (!data) {
    return null
  }

  if (!data.has_conflicts) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <div className="flex items-center gap-3">
          <span className="text-xl">✅</span>
          <div>
            <h4 className="text-sm font-semibold text-green-900">No conflicts detected</h4>
            <p className="text-xs text-green-700 mt-1">
              This schedule can be created without conflicts
            </p>
          </div>
        </div>
      </div>
    )
  }

  // Group conflicts by type
  const timeOverlaps = data.conflicts.filter(c => c.conflict_type === 'time_overlap')
  const deviceOverlaps = data.conflicts.filter(c => c.conflict_type === 'device_overlap')
  const priorityConflicts = data.conflicts.filter(c => c.conflict_type === 'priority_conflict')

  return (
    <div className="space-y-4">
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <span className="text-xl">⚠️</span>
          <div className="flex-1">
            <h4 className="text-sm font-semibold text-red-900">
              {data.conflicts.length} conflict{data.conflicts.length > 1 ? 's' : ''} detected
            </h4>
            <p className="text-xs text-red-700 mt-1">
              Please review the conflicts below and adjust your schedule
            </p>
          </div>
        </div>
      </div>

      {/* Time Overlaps */}
      {timeOverlaps.length > 0 && (
        <div className="space-y-2">
          <h5 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
            <span>🕐</span>
            Time Overlaps ({timeOverlaps.length})
          </h5>
          {timeOverlaps.map((conflict, index) => (
            <ConflictCard key={index} conflict={conflict} />
          ))}
        </div>
      )}

      {/* Device Overlaps */}
      {deviceOverlaps.length > 0 && (
        <div className="space-y-2">
          <h5 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
            <span>📱</span>
            Device Conflicts ({deviceOverlaps.length})
          </h5>
          {deviceOverlaps.map((conflict, index) => (
            <ConflictCard key={index} conflict={conflict} />
          ))}
        </div>
      )}

      {/* Priority Conflicts */}
      {priorityConflicts.length > 0 && (
        <div className="space-y-2">
          <h5 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
            <span>⚡</span>
            Priority Conflicts ({priorityConflicts.length})
          </h5>
          {priorityConflicts.map((conflict, index) => (
            <ConflictCard key={index} conflict={conflict} />
          ))}
        </div>
      )}
    </div>
  )
}

// Conflict Card Component
const ConflictCard = ({ conflict }: { conflict: any }) => {
  const isWarning = conflict.severity === 'warning'

  return (
    <div className={`border rounded-lg p-3 ${
      isWarning ? 'bg-yellow-50 border-yellow-200' : 'bg-red-50 border-red-200'
    }`}>
      <div className="flex items-start gap-3">
        <span className={`text-lg ${isWarning ? '⚠️' : '🚫'}`}></span>
        <div className="flex-1">
          <p className={`text-sm ${isWarning ? 'text-yellow-900' : 'text-red-900'}`}>
            {conflict.message}
          </p>
          {conflict.conflicting_schedule_name && (
            <p className={`text-xs mt-1 ${isWarning ? 'text-yellow-700' : 'text-red-700'}`}>
              Conflicting schedule: <strong>{conflict.conflicting_schedule_name}</strong>
            </p>
          )}
          {conflict.resolution_suggestion && (
            <p className={`text-xs mt-2 ${isWarning ? 'text-yellow-600' : 'text-red-600'}`}>
              💡 {conflict.resolution_suggestion}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

export default ConflictDetector