/**
 * Schedule List Component
 * Display schedules with filters and actions
 */

import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { CheckCircle, XCircle, Clock, Calendar, ClipboardList, Smartphone, Eye, Pause, X, Play, Edit, Trash2 } from 'lucide-react'
import {
  PRIORITY_LEVELS,
  RECURRENCE_TYPES,
  type Schedule,
  type ScheduleStatus,
  type PriorityLevel,
  type RecurrenceType,
} from '../types/schedule.types'
import { formatDateTime } from '@/shared/utils/formatters'
import { renderIcon } from '@/shared/utils/iconHelper'

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
  const { t } = useTranslation()
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
          <div key={i} className="h-32 bg-gray-100 dark:bg-gray-700 rounded-lg animate-pulse" />
        ))}
      </div>
    )
  }

  if (schedules.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 dark:bg-gray-800 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600">
        <Calendar className="w-16 h-16 mx-auto mb-4 text-gray-400 dark:text-gray-500" />
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">{t('schedules.noSchedulesYet')}</h3>
        <p className="text-gray-600 dark:text-gray-400 mb-4">{t('schedules.createFirstSchedule')}</p>
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
            placeholder={t('schedules.searchPlaceholder')}
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
          <option value="all">{t('schedules.filters.allStatus')}</option>
          <option value="active">{t('schedules.status.active')}</option>
          <option value="inactive">{t('schedules.status.inactive')}</option>
          <option value="paused">{t('schedules.status.paused')}</option>
          <option value="expired">{t('schedules.status.expired')}</option>
        </select>

        {/* Priority filter */}
        <select
          value={filterPriority}
          onChange={(e) => setFilterPriority(e.target.value as PriorityLevel | 'all')}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
        >
          <option value="all">{t('schedules.filters.allPriority')}</option>
          {Object.values(PRIORITY_LEVELS).map((priority) => (
            <option key={priority.level} value={priority.level}>
              {priority.label}
            </option>
          ))}
        </select>

        {/* Recurrence filter */}
        <select
          value={filterRecurrence}
          onChange={(e) => setFilterRecurrence(e.target.value as RecurrenceType | 'all')}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
        >
          <option value="all">{t('schedules.filters.allTypes')}</option>
          {Object.values(RECURRENCE_TYPES).map((type) => (
            <option key={type.type} value={type.type}>
              {type.label}
            </option>
          ))}
        </select>
      </div>

      {/* Results count */}
      <div className="text-sm text-gray-600 dark:text-gray-400">
        {t('schedules.showing', {
          filtered: filteredSchedules.length,
          total: schedules.length,
        })}
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
                    <div className={`px-3 py-1 rounded-full text-sm font-medium flex items-center gap-1.5 ${
                      schedule.status === 'active'
                        ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                        : schedule.status === 'inactive'
                        ? 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                        : schedule.status === 'paused'
                        ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300'
                        : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
                    }`}>
                      {schedule.status === 'active' && (
                        <>
                          <CheckCircle className="w-4 h-4" />
                          <span>{t('schedules.status.active')}</span>
                        </>
                      )}
                      {schedule.status === 'inactive' && (
                        <>
                          <XCircle className="w-4 h-4" />
                          <span>{t('schedules.status.inactive')}</span>
                        </>
                      )}
                      {schedule.status === 'paused' && (
                        <>
                          <Clock className="w-4 h-4" />
                          <span>{t('schedules.status.paused')}</span>
                        </>
                      )}
                      {schedule.status === 'expired' && (
                        <>
                          <Clock className="w-4 h-4" />
                          <span>{t('schedules.status.expired')}</span>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Metadata badges */}
                  <div className="flex flex-wrap items-center gap-2 mb-3">
                    {/* Priority */}
                    <div className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm ${
                      priority.color === 'red'
                        ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
                        : priority.color === 'orange'
                        ? 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300'
                        : priority.color === 'blue'
                        ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                    }`}>
                      {renderIcon(priority.icon, { className: 'w-4 h-4' })}
                      <span>{priority.label}</span>
                    </div>

                    {/* Recurrence */}
                    <div className="inline-flex items-center gap-1 px-3 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full text-sm">
                      {renderIcon(recurrenceType.icon, { className: 'w-4 h-4' })}
                      <span>{recurrenceType.label}</span>
                    </div>

                    {/* Playlist */}
                    {schedule.playlist_name && (
                      <div className="inline-flex items-center gap-1 px-3 py-1 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded-full text-sm">
                        <ClipboardList className="w-4 h-4" />
                        <span>{schedule.playlist_name}</span>
                      </div>
                    )}

                    {/* Devices count */}
                    <div className="inline-flex items-center gap-1 px-3 py-1 bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300 rounded-full text-sm">
                      <Smartphone className="w-4 h-4" />
                      <span>
                        {schedule.device_ids.length}{' '}
                        {t(schedule.device_ids.length !== 1 ? 'schedules.devices' : 'schedules.device')}
                      </span>
                    </div>
                  </div>

                  {/* Schedule details */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-gray-600 dark:text-gray-400">
                    <div>
                      <span className="font-medium">{t('schedules.labels.time')}:</span>{' '}
                      {schedule.start_time} - {schedule.end_time}
                    </div>
                    <div>
                      <span className="font-medium">{t('schedules.labels.timezone')}:</span>{' '}
                      {schedule.timezone}
                    </div>
                    <div>
                      <span className="font-medium">{t('schedules.labels.start')}:</span>{' '}
                      {new Date(schedule.start_date).toLocaleDateString()}
                    </div>
                    <div>
                      <span className="font-medium">{t('schedules.labels.end')}:</span>{' '}
                      {schedule.end_date
                        ? new Date(schedule.end_date).toLocaleDateString()
                        : t('schedules.labels.noEndDate')}
                    </div>
                  </div>

                  {/* Additional info */}
                  <div className="flex items-center gap-4 mt-3 text-xs text-gray-500 dark:text-gray-400">
                    {schedule.last_run && (
                      <span>
                        {t('schedules.labels.lastRun')}: {formatDateTime(schedule.last_run)}
                      </span>
                    )}
                    {schedule.next_run && (
                      <span>
                        {t('schedules.labels.nextRun')}: {formatDateTime(schedule.next_run)}
                      </span>
                    )}
                  </div>

                  {/* Exception dates */}
                  {schedule.exception_dates && schedule.exception_dates.length > 0 && (
                    <div className="mt-3 p-2 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded text-xs">
                      <span className="font-medium text-red-900 dark:text-red-200">
                        {t('schedules.labels.exceptionDates')}:
                      </span>{' '}
                      <span className="text-red-700 dark:text-red-300">
                        {schedule.exception_dates
                          .slice(0, 3)
                          .map((d) => new Date(d).toLocaleDateString())
                          .join(', ')}
                        {schedule.exception_dates.length > 3 &&
                          ' ' +
                            t('schedules.labels.more', {
                              count: schedule.exception_dates.length - 3,
                            })}
                      </span>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex flex-col gap-2 ml-4">
                  <button
                    onClick={() => onView(schedule)}
                    className="px-3 py-1.5 text-sm bg-gray-50 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-100 dark:hover:bg-gray-600 flex items-center gap-1"
                    title={t('schedules.actions.viewDetails')}
                  >
                    <Eye className="w-4 h-4" />
                    {t('schedules.actions.view')}
                  </button>

                  {schedule.status === 'active' && (
                    <>
                      <button
                        onClick={() => onPause(schedule)}
                        className="px-3 py-1.5 text-sm bg-yellow-50 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 rounded hover:bg-yellow-100 dark:hover:bg-yellow-900/50 flex items-center gap-1"
                        title={t('schedules.actions.pauseSchedule')}
                      >
                        <Pause className="w-4 h-4" />
                        {t('schedules.actions.pause')}
                      </button>
                      <button
                        onClick={() => onDeactivate(schedule)}
                        className="px-3 py-1.5 text-sm bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded hover:bg-red-100 dark:hover:bg-red-900/50 flex items-center gap-1"
                        title={t('schedules.actions.deactivateSchedule')}
                      >
                        <X className="w-4 h-4" />
                        {t('schedules.actions.stop')}
                      </button>
                    </>
                  )}

                  {schedule.status === 'inactive' && (
                    <button
                      onClick={() => onActivate(schedule)}
                      className="px-3 py-1.5 text-sm bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded hover:bg-green-100 dark:hover:bg-green-900/50 flex items-center gap-1"
                      title={t('schedules.actions.activateSchedule')}
                    >
                      <CheckCircle className="w-4 h-4" />
                      {t('schedules.actions.start')}
                    </button>
                  )}

                  {schedule.status === 'paused' && (
                    <button
                      onClick={() => onActivate(schedule)}
                      className="px-3 py-1.5 text-sm bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded hover:bg-green-100 dark:hover:bg-green-900/50 flex items-center gap-1"
                      title={t('schedules.actions.resumeSchedule')}
                    >
                      <Play className="w-4 h-4" />
                      {t('schedules.actions.resume')}
                    </button>
                  )}

                  {schedule.status !== 'expired' && (
                    <button
                      onClick={() => onEdit(schedule)}
                      className="px-3 py-1.5 text-sm bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded hover:bg-blue-100 dark:hover:bg-blue-900/50 flex items-center gap-1"
                      title={t('schedules.actions.editSchedule')}
                    >
                      <Edit className="w-4 h-4" />
                      {t('schedules.actions.edit')}
                    </button>
                  )}

                  <button
                    onClick={() => onDelete(schedule)}
                    className="px-3 py-1.5 text-sm bg-gray-50 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-100 dark:hover:bg-gray-600 flex items-center gap-1"
                    title={t('schedules.actions.deleteSchedule')}
                  >
                    <Trash2 className="w-4 h-4" />
                    {t('schedules.actions.delete')}
                  </button>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* No results */}
      {filteredSchedules.length === 0 && (
        <div className="text-center py-8 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <p className="text-gray-600 dark:text-gray-400">{t('schedules.noMatches')}</p>
          <button
            onClick={() => {
              setSearchQuery('')
              setFilterStatus('all')
              setFilterPriority('all')
              setFilterRecurrence('all')
            }}
            className="mt-2 text-sm text-blue-600 dark:text-blue-400 hover:underline"
          >
            {t('schedules.clearFilters')}
          </button>
        </div>
      )}
    </div>
  )
}

export default ScheduleList