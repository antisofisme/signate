/**
 * Schedule List Component
 * Display schedules with filters and actions
 */

import { useState } from 'react'
import {
  PRIORITY_LEVELS,
  RECURRENCE_TYPES,
  type Schedule,
  type ScheduleStatus,
  type PriorityLevel,
  type RecurrenceType,
} from '../types/schedule.types'
import { formatDateTime } from '@/shared/utils/formatters'

interface ScheduleListProps {
  schedules: Schedule[]
  isLoading?: boolean
  onView: (schedule: Schedule) => void
  onEdit: (schedule: Schedule) => void
  onDelete: (schedule: Schedule) => void
  onActivate: (schedule: Schedule) => void
  onDeactivate: (schedule: Schedule) => void
  onPause: (schedule: Schedule) => void
}

export const ScheduleList = ({
  schedules,
  isLoading,
  onView,
  onEdit,
  onDelete,
  onActivate,
  onDeactivate,
  onPause,
}: ScheduleListProps) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [filterStatus, setFilterStatus] = useState<ScheduleStatus | 'all'>('all')
  const [filterPriority, setFilterPriority] = useState<PriorityLevel | 'all'>('all')
  const [filterRecurrence, setFilterRecurrence] = useState<RecurrenceType | 'all'>('all')

  // Filter schedules
  const filteredSchedules = schedules.filter((schedule) => {
    const matchesSearch = 
      schedule.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (schedule.playlist_name?.toLowerCase().includes(searchQuery.toLowerCase()))

    const matchesStatus = filterStatus === 'all' || schedule.status === filterStatus
    const matchesPriority = filterPriority === 'all' || schedule.priority === filterPriority
    const matchesRecurrence = filterRecurrence === 'all' || schedule.recurrence_type === filterRecurrence

    return matchesSearch && matchesStatus && matchesPriority && matchesRecurrence
  })

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-32 bg-gray-100 rounded-lg animate-pulse" />
        ))}
      </div>
    )
  }

  if (schedules.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 dark:bg-gray-700 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600">
        <div className="text-4xl mb-4">📅</div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">No schedules yet</h3>
        <p className="text-gray-600 dark:text-gray-400 mb-4">Create your first schedule to start automating content playback</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-3">
        {/* Search */}
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search schedules or playlists..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          />
        </div>

        {/* Status filter */}
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value as ScheduleStatus | 'all')}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
        >
          <option value="all">All Status</option>
          <option value="active">✅ Active</option>
          <option value="inactive">❌ Inactive</option>
          <option value="paused">⏸️ Paused</option>
          <option value="expired">⏰ Expired</option>
        </select>

        {/* Priority filter */}
        <select
          value={filterPriority}
          onChange={(e) => setFilterPriority(e.target.value as PriorityLevel | 'all')}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
        >
          <option value="all">All Priority</option>
          {Object.values(PRIORITY_LEVELS).map((priority) => (
            <option key={priority.level} value={priority.level}>
              {priority.icon} {priority.label}
            </option>
          ))}
        </select>

        {/* Recurrence filter */}
        <select
          value={filterRecurrence}
          onChange={(e) => setFilterRecurrence(e.target.value as RecurrenceType | 'all')}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
        >
          <option value="all">All Types</option>
          {Object.values(RECURRENCE_TYPES).map((type) => (
            <option key={type.type} value={type.type}>
              {type.icon} {type.label}
            </option>
          ))}
        </select>
      </div>

      {/* Results count */}
      <div className="text-sm text-gray-600 dark:text-gray-400">
        Showing {filteredSchedules.length} of {schedules.length} schedules
      </div>

      {/* Schedule cards */}
      <div className="space-y-4">
        {filteredSchedules.map((schedule) => {
          const priority = PRIORITY_LEVELS[schedule.priority]
          const recurrenceType = RECURRENCE_TYPES[schedule.recurrence_type]

          return (
            <div
              key={schedule.id}
              className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                {/* Schedule info */}
                <div className="flex-1">
                  {/* Header */}
                  <div className="flex items-start gap-3 mb-3">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        {schedule.name}
                      </h3>
                      {schedule.description && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          {schedule.description}
                        </p>
                      )}
                    </div>

                    {/* Status badge */}
                    <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                      schedule.status === 'active'
                        ? 'bg-green-100 text-green-700'
                        : schedule.status === 'inactive'
                        ? 'bg-gray-100 text-gray-700'
                        : schedule.status === 'paused'
                        ? 'bg-yellow-100 text-yellow-700'
                        : 'bg-red-100 text-red-700'
                    }`}>
                      {schedule.status === 'active' && '✅ Active'}
                      {schedule.status === 'inactive' && '❌ Inactive'}
                      {schedule.status === 'paused' && '⏸️ Paused'}
                      {schedule.status === 'expired' && '⏰ Expired'}
                    </div>
                  </div>

                  {/* Metadata badges */}
                  <div className="flex flex-wrap items-center gap-2 mb-3">
                    {/* Priority */}
                    <div className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm ${
                      priority.color === 'red' 
                        ? 'bg-red-100 text-red-700' 
                        : priority.color === 'orange' 
                        ? 'bg-orange-100 text-orange-700' 
                        : priority.color === 'blue' 
                        ? 'bg-blue-100 text-blue-700' 
                        : 'bg-gray-100 text-gray-700'
                    }`}>
                      <span>{priority.icon}</span>
                      <span>{priority.label}</span>
                    </div>

                    {/* Recurrence */}
                    <div className="inline-flex items-center gap-1 px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm">
                      <span>{recurrenceType.icon}</span>
                      <span>{recurrenceType.label}</span>
                    </div>

                    {/* Playlist */}
                    {schedule.playlist_name && (
                      <div className="inline-flex items-center gap-1 px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm">
                        <span>📋</span>
                        <span>{schedule.playlist_name}</span>
                      </div>
                    )}

                    {/* Devices count */}
                    <div className="inline-flex items-center gap-1 px-3 py-1 bg-cyan-100 text-cyan-700 rounded-full text-sm">
                      <span>📱</span>
                      <span>{schedule.device_ids.length} device{schedule.device_ids.length !== 1 ? 's' : ''}</span>
                    </div>
                  </div>

                  {/* Schedule details */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-gray-600 dark:text-gray-400">
                    <div>
                      <span className="font-medium">Time:</span>{' '}
                      {schedule.start_time} - {schedule.end_time}
                    </div>
                    <div>
                      <span className="font-medium">Timezone:</span>{' '}
                      {schedule.timezone}
                    </div>
                    <div>
                      <span className="font-medium">Start:</span>{' '}
                      {new Date(schedule.start_date).toLocaleDateString()}
                    </div>
                    <div>
                      <span className="font-medium">End:</span>{' '}
                      {schedule.end_date ? new Date(schedule.end_date).toLocaleDateString() : 'No end date'}
                    </div>
                  </div>

                  {/* Additional info */}
                  <div className="flex items-center gap-4 mt-3 text-xs text-gray-500 dark:text-gray-400">
                    {schedule.last_run && (
                      <span>Last run: {formatDateTime(schedule.last_run)}</span>
                    )}
                    {schedule.next_run && (
                      <span>Next run: {formatDateTime(schedule.next_run)}</span>
                    )}
                  </div>

                  {/* Exception dates */}
                  {schedule.exception_dates && schedule.exception_dates.length > 0 && (
                    <div className="mt-3 p-2 bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-800 rounded text-xs">
                      <span className="font-medium text-red-900 dark:text-red-200">Exception dates:</span>{' '}
                      <span className="text-red-700 dark:text-red-300">
                        {schedule.exception_dates.slice(0, 3).map(d =>
                          new Date(d).toLocaleDateString()
                        ).join(', ')}
                        {schedule.exception_dates.length > 3 && ` +${schedule.exception_dates.length - 3} more`}
                      </span>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex flex-col gap-2 ml-4">
                  <button
                    onClick={() => onView(schedule)}
                    className="px-3 py-1.5 text-sm bg-gray-50 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-100 dark:hover:bg-gray-600"
                    title="View Details"
                  >
                    👁️ View
                  </button>
                  
                  {schedule.status === 'active' && (
                    <>
                      <button
                        onClick={() => onPause(schedule)}
                        className="px-3 py-1.5 text-sm bg-yellow-50 text-yellow-700 rounded hover:bg-yellow-100"
                        title="Pause Schedule"
                      >
                        ⏸️ Pause
                      </button>
                      <button
                        onClick={() => onDeactivate(schedule)}
                        className="px-3 py-1.5 text-sm bg-red-50 text-red-700 rounded hover:bg-red-100"
                        title="Deactivate Schedule"
                      >
                        ❌ Stop
                      </button>
                    </>
                  )}

                  {schedule.status === 'inactive' && (
                    <button
                      onClick={() => onActivate(schedule)}
                      className="px-3 py-1.5 text-sm bg-green-50 text-green-700 rounded hover:bg-green-100"
                      title="Activate Schedule"
                    >
                      ✅ Start
                    </button>
                  )}

                  {schedule.status === 'paused' && (
                    <button
                      onClick={() => onActivate(schedule)}
                      className="px-3 py-1.5 text-sm bg-green-50 text-green-700 rounded hover:bg-green-100"
                      title="Resume Schedule"
                    >
                      ▶️ Resume
                    </button>
                  )}

                  {schedule.status !== 'expired' && (
                    <button
                      onClick={() => onEdit(schedule)}
                      className="px-3 py-1.5 text-sm bg-blue-50 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded hover:bg-blue-100 dark:hover:bg-blue-800"
                      title="Edit Schedule"
                    >
                      ✏️ Edit
                    </button>
                  )}

                  <button
                    onClick={() => onDelete(schedule)}
                    className="px-3 py-1.5 text-sm bg-gray-50 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-100 dark:hover:bg-gray-600"
                    title="Delete Schedule"
                  >
                    🗑️ Delete
                  </button>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* No results */}
      {filteredSchedules.length === 0 && (
        <div className="text-center py-8 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <p className="text-gray-600 dark:text-gray-400">No schedules match your filters</p>
          <button
            onClick={() => {
              setSearchQuery('')
              setFilterStatus('all')
              setFilterPriority('all')
              setFilterRecurrence('all')
            }}
            className="mt-2 text-sm text-blue-600 hover:underline"
          >
            Clear filters
          </button>
        </div>
      )}
    </div>
  )
}

export default ScheduleList