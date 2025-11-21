/**
 * Schedule Priority Manager Component
 * Visual priority management with conflict resolution
 */

import { useState, useMemo } from 'react'
import { Slider } from '@/shared/components/ui/slider'
import { ArrowUp, ArrowDown, AlertTriangle, CheckCircle, TrendingUp } from 'lucide-react'
import type { Schedule } from '../types/schedule.types'

interface SchedulePriorityManagerProps {
  currentPriority: number
  onPriorityChange: (priority: number) => void
  relatedSchedules?: Schedule[]
  className?: string
}

export const SchedulePriorityManager = ({
  currentPriority,
  onPriorityChange,
  relatedSchedules = [],
  className = '',
}: SchedulePriorityManagerProps) => {
  const [localPriority, setLocalPriority] = useState(currentPriority)

  // Analyze conflicts with related schedules
  const conflictAnalysis = useMemo(() => {
    const conflicts: Array<{
      schedule: Schedule
      conflict: 'same' | 'higher' | 'lower'
      suggestion: string
    }> = []

    relatedSchedules.forEach((schedule) => {
      // Map priority level to numeric values for comparison
      const priorityMap = { low: 25, normal: 50, high: 75, critical: 100 }
      const schedulePriority = priorityMap[schedule.priority] || 50

      if (Math.abs(schedulePriority - localPriority) < 10) {
        conflicts.push({
          schedule,
          conflict: 'same',
          suggestion: `Adjust to ${schedulePriority + 10} to avoid tie`,
        })
      } else if (schedulePriority > localPriority) {
        conflicts.push({
          schedule,
          conflict: 'higher',
          suggestion: `${schedule.name} has higher priority`,
        })
      }
    })

    return conflicts
  }, [relatedSchedules, localPriority])

  // Get priority level from numeric value
  const getPriorityLevel = (value: number): string => {
    if (value >= 75) return 'Critical'
    if (value >= 50) return 'High'
    if (value >= 25) return 'Normal'
    return 'Low'
  }

  // Get priority color
  const getPriorityColor = (value: number): string => {
    if (value >= 75) return 'text-red-600 dark:text-red-400'
    if (value >= 50) return 'text-orange-600 dark:text-orange-400'
    if (value >= 25) return 'text-blue-600 dark:text-blue-400'
    return 'text-gray-600 dark:text-gray-400'
  }

  const handleSliderChange = (values: number[]) => {
    setLocalPriority(values[0])
  }

  const handleApply = () => {
    onPriorityChange(localPriority)
  }

  const hasConflicts = conflictAnalysis.length > 0
  const hasChanged = localPriority !== currentPriority

  return (
    <div className={`bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp className="h-5 w-5 text-purple-600 dark:text-purple-400" />
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
          Priority Management
        </h3>
      </div>

      {/* Priority Slider */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Priority Level
          </label>
          <div className="flex items-center gap-2">
            <span className={`text-2xl font-bold ${getPriorityColor(localPriority)}`}>
              {localPriority}
            </span>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              ({getPriorityLevel(localPriority)})
            </span>
          </div>
        </div>

        {/* Slider */}
        <div className="px-2">
          <Slider
            value={[localPriority]}
            onValueChange={handleSliderChange}
            min={0}
            max={100}
            step={5}
            className="w-full"
          />

          {/* Markers */}
          <div className="flex justify-between mt-2 text-xs text-gray-500 dark:text-gray-400">
            <span>0</span>
            <span>25</span>
            <span>50</span>
            <span>75</span>
            <span>100</span>
          </div>
        </div>

        {/* Priority Levels Guide */}
        <div className="grid grid-cols-4 gap-2 mt-4">
          {[
            { label: 'Low', range: '0-24', color: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300' },
            { label: 'Normal', range: '25-49', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200' },
            { label: 'High', range: '50-74', color: 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-200' },
            { label: 'Critical', range: '75-100', color: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200' },
          ].map((level) => (
            <div
              key={level.label}
              className={`p-2 rounded text-center ${level.color}`}
            >
              <div className="text-xs font-semibold">{level.label}</div>
              <div className="text-xs opacity-75">{level.range}</div>
            </div>
          ))}
        </div>

        {/* Quick Adjustments */}
        <div className="flex items-center justify-between gap-2">
          <button
            type="button"
            onClick={() => setLocalPriority(Math.max(0, localPriority - 10))}
            className="flex-1 flex items-center justify-center gap-1 px-3 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md text-sm transition-colors"
          >
            <ArrowDown className="h-4 w-4" />
            -10
          </button>
          <button
            type="button"
            onClick={() => setLocalPriority(50)}
            className="flex-1 px-3 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md text-sm transition-colors"
          >
            Reset (50)
          </button>
          <button
            type="button"
            onClick={() => setLocalPriority(Math.min(100, localPriority + 10))}
            className="flex-1 flex items-center justify-center gap-1 px-3 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md text-sm transition-colors"
          >
            <ArrowUp className="h-4 w-4" />
            +10
          </button>
        </div>

        {/* Conflict Analysis */}
        {relatedSchedules.length > 0 && (
          <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
            <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
              Related Schedules ({relatedSchedules.length})
            </h4>

            <div className="space-y-2 max-h-40 overflow-y-auto">
              {relatedSchedules.map((schedule) => {
                const priorityMap = { low: 25, normal: 50, high: 75, critical: 100 }
                const schedulePriority = priorityMap[schedule.priority] || 50
                const diff = localPriority - schedulePriority

                return (
                  <div
                    key={schedule.id}
                    className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700/50 rounded text-xs"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 dark:text-white truncate">
                        {schedule.name}
                      </p>
                      <p className="text-gray-500 dark:text-gray-400">
                        {schedule.start_time} - {schedule.end_time}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded ${
                        diff > 10
                          ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200'
                          : diff < -10
                          ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-200'
                          : 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200'
                      }`}>
                        {schedulePriority}
                      </span>
                      {Math.abs(diff) < 10 && (
                        <AlertTriangle className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Conflict Warnings */}
        {hasConflicts && (
          <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md">
            <div className="flex items-start gap-2">
              <AlertTriangle className="h-4 w-4 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-yellow-900 dark:text-yellow-200 mb-1">
                  Priority Conflicts Detected
                </p>
                <ul className="text-xs text-yellow-800 dark:text-yellow-300 space-y-1">
                  {conflictAnalysis.map((conflict, idx) => (
                    <li key={idx}>
                      {conflict.schedule.name}: {conflict.suggestion}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Success Message */}
        {!hasConflicts && relatedSchedules.length > 0 && (
          <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
            <CheckCircle className="h-4 w-4" />
            <span>No priority conflicts detected</span>
          </div>
        )}

        {/* Apply Button */}
        {hasChanged && (
          <button
            type="button"
            onClick={handleApply}
            className="w-full px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors text-sm font-medium"
          >
            Apply Priority Change
          </button>
        )}
      </div>
    </div>
  )
}

export default SchedulePriorityManager
