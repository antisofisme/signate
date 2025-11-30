/**
 * Schedule List Component
 * Display schedules with filters and card layout
 *
 * LAYER 1: PRESENTATION
 */

import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Calendar } from 'lucide-react'
import { TableSkeleton, EmptyState } from '@/shared/components'
import {
  PRIORITY_LEVELS,
  RECURRENCE_TYPES,
  getScheduleStatus,
  type Schedule,
  type ScheduleStatus,
  type PriorityLevel,
  type RecurrenceType,
} from '../types/schedule.types'
import { ScheduleCard } from './ScheduleCard'

interface ScheduleListProps {
  schedules: Schedule[]
  isLoading?: boolean
  onView: (schedule: Schedule) => void
  onEdit: (schedule: Schedule) => void
  onDelete: (schedule: Schedule) => void
  onActivate: (schedule: Schedule) => void
  onDeactivate: (schedule: Schedule) => void
  onPause: (schedule: Schedule) => void
  onTimelineClick?: (schedule: Schedule) => void
  canUpdate?: boolean
  canDelete?: boolean
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
  onTimelineClick,
  canUpdate = true,
  canDelete = true,
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

    // Derive status from is_active and dates
    const derivedStatus = getScheduleStatus(schedule)
    const matchesStatus = filterStatus === 'all' || derivedStatus === filterStatus
    const matchesPriority = filterPriority === 'all' || schedule.priority === filterPriority
    const matchesRecurrence = filterRecurrence === 'all' || schedule.recurrence_type === filterRecurrence

    return matchesSearch && matchesStatus && matchesPriority && matchesRecurrence
  })

  if (isLoading) {
    return <TableSkeleton rows={5} columns={1} />
  }

  if (schedules.length === 0) {
    return (
      <EmptyState
        icon={Calendar}
        title={t('schedules.noSchedulesYet')}
        description={t('schedules.createFirstSchedule')}
      />
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
        {filteredSchedules.map((schedule) => (
          <ScheduleCard
            key={schedule.id}
            schedule={schedule}
            onView={onView}
            onEdit={onEdit}
            onDelete={onDelete}
            onActivate={onActivate}
            onDeactivate={onDeactivate}
            onPause={onPause}
            onTimelineClick={onTimelineClick}
            canUpdate={canUpdate}
            canDelete={canDelete}
          />
        ))}
      </div>

      {/* No results */}
      {filteredSchedules.length === 0 && (
        <EmptyState
          icon={Calendar}
          title={t('schedules.noMatches')}
          description={t('schedules.tryDifferentFilters')}
        />
      )}
    </div>
  )
}

export default ScheduleList
