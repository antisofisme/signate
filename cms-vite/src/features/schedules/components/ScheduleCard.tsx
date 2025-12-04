/**
 * Schedule Card Component
 * Horizontal card layout with timeline visualization
 *
 * LAYER 1: PRESENTATION
 */

import { useTranslation } from 'react-i18next'
import {
  CheckCircle,
  XCircle,
  Clock,
  ClipboardList,
  Monitor,
  Eye,
  Pause,
  X,
  Play,
  Edit,
  Trash2,
} from 'lucide-react'
import { ScheduleTimeline } from './ScheduleTimeline'
import {
  DEFAULT_SCHEDULE_COLOR,
  getScheduleStatus,
  type Schedule,
  type ScheduleStatus,
  type DayOfWeek,
} from '../types/schedule.types'
import { formatDateTime } from '@/shared/utils/formatters'

interface ScheduleCardProps {
  schedule: Schedule
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

// Status icon component
const StatusIcon = ({ status }: { status: ScheduleStatus }) => {
  switch (status) {
    case 'active':
      return <CheckCircle className="w-5 h-5 text-green-500" />
    case 'inactive':
      return <XCircle className="w-5 h-5 text-gray-400" />
    case 'paused':
      return <Pause className="w-5 h-5 text-yellow-500" />
    case 'expired':
      return <Clock className="w-5 h-5 text-red-400" />
    default:
      return null
  }
}

// Status badge component
const StatusBadge = ({ status, t }: { status: ScheduleStatus; t: (key: string) => string }) => {
  const styles: Record<ScheduleStatus, string> = {
    active: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
    inactive: 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300',
    paused: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300',
    expired: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300',
  }

  return (
    <span className={`px-3 py-1 rounded-full text-sm font-medium ${styles[status]}`}>
      {t(`schedules.status.${status}`)}
    </span>
  )
}

export const ScheduleCard = ({
  schedule,
  onView,
  onEdit,
  onDelete,
  onActivate,
  onDeactivate,
  onPause,
  onTimelineClick,
  canUpdate = true,
  canDelete = true,
}: ScheduleCardProps) => {
  const { t } = useTranslation()

  // Derive status from is_active and dates
  const status = getScheduleStatus(schedule)
  const scheduleColor = schedule.color || DEFAULT_SCHEDULE_COLOR

  // Extract recurrence days for weekly schedules
  const recurrenceDays = schedule.recurrence_pattern?.days_of_week as DayOfWeek[] | undefined
  const recurrenceInterval = schedule.recurrence_pattern?.interval

  // Handle timeline click
  const handleTimelineClick = () => {
    if (onTimelineClick) {
      onTimelineClick(schedule)
    } else if (canUpdate && status !== 'expired') {
      onEdit(schedule)
    }
  }

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-5 hover:shadow-md transition-shadow">
      {/* Header Row */}
      <div className="flex items-start justify-between mb-4">
        {/* Left: Status icon + Title + Badges */}
        <div className="flex items-start gap-3 flex-1 min-w-0">
          {/* Status icon */}
          <div className="flex-shrink-0 mt-0.5">
            <StatusIcon status={status} />
          </div>

          {/* Title and badges */}
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
              {schedule.name}
            </h3>

            {/* Metadata badges */}
            <div className="flex flex-wrap items-center gap-2 mt-1.5">
              {/* Playlist badge */}
              {schedule.playlist_name && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded text-xs">
                  <ClipboardList className="w-3 h-3" />
                  {schedule.playlist_name}
                </span>
              )}

              {/* Device count badge (placeholder - would need actual count) */}
              <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded text-xs">
                <Monitor className="w-3 h-3" />
                {t('schedules.devices', 'devices')}
              </span>
            </div>
          </div>
        </div>

        {/* Right: Status badge + Color */}
        <div className="flex items-start gap-3 flex-shrink-0 ml-4">
          {/* Status badge */}
          <StatusBadge status={status} t={t} />

          {/* Color indicator */}
          <div
            className="w-5 h-5 rounded-full border-2 border-white dark:border-gray-800 shadow-sm"
            style={{ backgroundColor: scheduleColor }}
            title={t('schedules.labels.scheduleColor')}
          />
        </div>
      </div>

      {/* Timeline Section */}
      <div className="mb-4">
        <ScheduleTimeline
          startTime={schedule.start_time}
          endTime={schedule.end_time}
          recurrenceType={schedule.recurrence_type}
          recurrenceDays={recurrenceDays}
          recurrenceInterval={recurrenceInterval}
          onClick={handleTimelineClick}
          isClickable={canUpdate && status !== 'expired'}
          showNowIndicator={true}
          isActive={status === 'active'}
        />
      </div>

      {/* Meta Row */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-500 dark:text-gray-400 mb-4">
        {schedule.next_run && (
          <span>
            <span className="font-medium">{t('schedules.labels.nextRun')}:</span>{' '}
            {formatDateTime(schedule.next_run)}
          </span>
        )}
        {schedule.last_run && (
          <span>
            <span className="font-medium">{t('schedules.labels.lastRun')}:</span>{' '}
            {formatDateTime(schedule.last_run)}
          </span>
        )}
        {schedule.end_date ? (
          <span>
            <span className="font-medium">{t('schedules.labels.end')}:</span>{' '}
            {new Date(schedule.end_date).toLocaleDateString()}
          </span>
        ) : (
          <span className="text-gray-400 dark:text-gray-500">
            {t('schedules.labels.noEndDate')}
          </span>
        )}
      </div>

      {/* Exception dates warning */}
      {schedule.exception_dates && schedule.exception_dates.length > 0 && (
        <div className="mb-4 p-2 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded text-xs text-amber-700 dark:text-amber-300">
          <span className="font-medium">{t('schedules.labels.exceptionDates')}:</span>{' '}
          {schedule.exception_dates
            .slice(0, 3)
            .map((d) => new Date(d).toLocaleDateString())
            .join(', ')}
          {schedule.exception_dates.length > 3 &&
            ` +${schedule.exception_dates.length - 3} ${t('schedules.labels.more', { count: schedule.exception_dates.length - 3 })}`}
        </div>
      )}

      {/* Actions Row */}
      <div className="flex flex-wrap items-center gap-2 pt-4 border-t border-gray-100 dark:border-gray-700">
        {/* View - always available */}
        <button
          onClick={() => onView(schedule)}
          className="px-3 py-1.5 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 flex items-center gap-1.5 transition-colors"
          title={t('schedules.actions.viewDetails')}
        >
          <Eye className="w-4 h-4" />
          {t('schedules.actions.view')}
        </button>

        {/* Edit - if can update and not expired */}
        {canUpdate && status !== 'expired' && (
          <button
            onClick={() => onEdit(schedule)}
            className="px-3 py-1.5 text-sm bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-md hover:bg-blue-100 dark:hover:bg-blue-900/50 flex items-center gap-1.5 transition-colors"
            title={t('schedules.actions.editSchedule')}
          >
            <Edit className="w-4 h-4" />
            {t('schedules.actions.edit')}
          </button>
        )}

        {/* Pause - only for active */}
        {canUpdate && status === 'active' && (
          <button
            onClick={() => onPause(schedule)}
            className="px-3 py-1.5 text-sm bg-yellow-50 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 rounded-md hover:bg-yellow-100 dark:hover:bg-yellow-900/50 flex items-center gap-1.5 transition-colors"
            title={t('schedules.actions.pauseSchedule')}
          >
            <Pause className="w-4 h-4" />
            {t('schedules.actions.pause')}
          </button>
        )}

        {/* Stop/Deactivate - only for active */}
        {canUpdate && status === 'active' && (
          <button
            onClick={() => onDeactivate(schedule)}
            className="px-3 py-1.5 text-sm bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-md hover:bg-red-100 dark:hover:bg-red-900/50 flex items-center gap-1.5 transition-colors"
            title={t('schedules.actions.deactivateSchedule')}
          >
            <X className="w-4 h-4" />
            {t('schedules.actions.stop')}
          </button>
        )}

        {/* Start/Activate - for inactive */}
        {canUpdate && status === 'inactive' && (
          <button
            onClick={() => onActivate(schedule)}
            className="px-3 py-1.5 text-sm bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-md hover:bg-green-100 dark:hover:bg-green-900/50 flex items-center gap-1.5 transition-colors"
            title={t('schedules.actions.activateSchedule')}
          >
            <Play className="w-4 h-4" />
            {t('schedules.actions.start')}
          </button>
        )}

        {/* Resume - for paused */}
        {canUpdate && status === 'paused' && (
          <button
            onClick={() => onActivate(schedule)}
            className="px-3 py-1.5 text-sm bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-md hover:bg-green-100 dark:hover:bg-green-900/50 flex items-center gap-1.5 transition-colors"
            title={t('schedules.actions.resumeSchedule')}
          >
            <Play className="w-4 h-4" />
            {t('schedules.actions.resume')}
          </button>
        )}

        {/* Spacer */}
        <div className="flex-1" />

        {/* Delete - always available if permitted */}
        {canDelete && (
          <button
            onClick={() => onDelete(schedule)}
            className="px-3 py-1.5 text-sm text-gray-500 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-md flex items-center gap-1.5 transition-colors"
            title={t('schedules.actions.deleteSchedule')}
          >
            <Trash2 className="w-4 h-4" />
            {t('schedules.actions.delete')}
          </button>
        )}
      </div>
    </div>
  )
}

export default ScheduleCard
