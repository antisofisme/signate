/**
 * Schedule Timeline Component
 * Visual 24-hour timeline bar showing active schedule time
 * Clickable to edit schedule time
 */

import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import type { RecurrenceType, DayOfWeek } from '../types/schedule.types'
import { DAYS_OF_WEEK, RECURRENCE_TYPES } from '../types/schedule.types'

interface ScheduleTimelineProps {
  startTime: string // "06:00"
  endTime: string // "12:00"
  recurrenceType: RecurrenceType | string
  recurrenceDays?: DayOfWeek[] // For weekly recurrence
  recurrenceInterval?: number // For daily recurrence
  onClick?: () => void
  isClickable?: boolean
  showNowIndicator?: boolean
  isActive?: boolean
}

// Parse time string to hours (decimal)
const parseTimeToHours = (time: string): number => {
  const [hours, minutes] = time.split(':').map(Number)
  return hours + minutes / 60
}

// Get current time as decimal hours
const getCurrentHours = (): number => {
  const now = new Date()
  return now.getHours() + now.getMinutes() / 60
}

// Format recurrence for display
const formatRecurrence = (
  type: RecurrenceType | string,
  days?: DayOfWeek[],
  interval?: number
): string => {
  switch (type) {
    case 'daily':
      if (interval && interval > 1) {
        return `Every ${interval} days`
      }
      return 'Daily'
    case 'weekly':
      if (days && days.length > 0) {
        if (days.length === 7) return 'Every day'
        if (days.length === 5 && !days.includes('saturday') && !days.includes('sunday')) {
          return 'Weekdays'
        }
        if (days.length === 2 && days.includes('saturday') && days.includes('sunday')) {
          return 'Weekends'
        }
        return days.map(d => DAYS_OF_WEEK[d]?.short || d).join(', ')
      }
      return 'Weekly'
    case 'monthly':
      return 'Monthly'
    case 'once':
      return 'One time'
    case 'custom':
      return 'Custom'
    default:
      return RECURRENCE_TYPES[type as RecurrenceType]?.label || type
  }
}

export const ScheduleTimeline = ({
  startTime,
  endTime,
  recurrenceType,
  recurrenceDays,
  recurrenceInterval,
  onClick,
  isClickable = true,
  showNowIndicator = true,
  isActive = false,
}: ScheduleTimelineProps) => {
  const { t } = useTranslation()

  // Calculate positions
  const { startPercent, widthPercent, nowPercent, isNowInRange } = useMemo(() => {
    const startHours = parseTimeToHours(startTime)
    const endHours = parseTimeToHours(endTime)
    const nowHours = getCurrentHours()

    // Handle overnight schedules (e.g., 22:00 - 06:00)
    let width: number
    if (endHours < startHours) {
      // Overnight: show two segments visually, but for simplicity show as one wrap
      width = (24 - startHours + endHours) / 24 * 100
    } else {
      width = (endHours - startHours) / 24 * 100
    }

    const start = (startHours / 24) * 100
    const now = (nowHours / 24) * 100

    // Check if current time is in schedule range
    let inRange: boolean
    if (endHours < startHours) {
      // Overnight schedule
      inRange = nowHours >= startHours || nowHours <= endHours
    } else {
      inRange = nowHours >= startHours && nowHours <= endHours
    }

    return {
      startPercent: start,
      widthPercent: Math.min(width, 100 - start), // Clamp to not overflow
      nowPercent: now,
      isNowInRange: inRange && isActive,
    }
  }, [startTime, endTime, isActive])

  // Hour markers
  const hourMarkers = [
    { hour: 0, label: '00', position: 0 },
    { hour: 6, label: '06', position: 25 },
    { hour: 12, label: '12', position: 50 },
    { hour: 18, label: '18', position: 75 },
    { hour: 24, label: '24', position: 100 },
  ]

  const recurrenceLabel = formatRecurrence(recurrenceType, recurrenceDays, recurrenceInterval)

  return (
    <div
      className={`relative ${isClickable ? 'cursor-pointer group' : ''}`}
      onClick={isClickable ? onClick : undefined}
      title={isClickable ? t('schedules.card.clickToEditTime', 'Click to edit schedule time') : undefined}
    >
      {/* Timeline container */}
      <div className="flex items-center gap-4">
        {/* Timeline bar */}
        <div className={`
          relative flex-1 h-10 bg-gray-100 dark:bg-gray-700 rounded-lg overflow-hidden
          ${isClickable ? 'group-hover:ring-2 group-hover:ring-blue-300 dark:group-hover:ring-blue-600 transition-all' : ''}
        `}>
          {/* Active time segment */}
          <div
            className={`
              absolute top-0 h-full rounded-lg transition-all
              ${isNowInRange
                ? 'bg-green-500 dark:bg-green-600'
                : 'bg-blue-500 dark:bg-blue-600'
              }
            `}
            style={{
              left: `${startPercent}%`,
              width: `${widthPercent}%`,
            }}
          />

          {/* Hour markers */}
          {hourMarkers.map(({ hour, label, position }) => (
            <div
              key={hour}
              className="absolute top-0 h-full flex flex-col justify-end"
              style={{ left: `${position}%`, transform: 'translateX(-50%)' }}
            >
              <div className="h-2 w-px bg-gray-300 dark:bg-gray-500" />
              <span className="text-[10px] text-gray-400 dark:text-gray-500 mt-0.5 hidden md:block">
                {label}
              </span>
            </div>
          ))}

          {/* Mobile simplified markers */}
          <div className="absolute bottom-1 left-0 right-0 flex justify-between px-2 md:hidden">
            <span className="text-[10px] text-gray-400">00</span>
            <span className="text-[10px] text-gray-400">12</span>
            <span className="text-[10px] text-gray-400">24</span>
          </div>

          {/* Now indicator */}
          {showNowIndicator && isActive && (
            <div
              className="absolute top-0 h-full w-0.5 bg-red-500 z-10"
              style={{ left: `${nowPercent}%` }}
            >
              <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-red-500 rounded-full" />
            </div>
          )}

          {/* Time range overlay text */}
          <div className="absolute inset-0 flex items-center justify-center">
            <span className={`
              text-sm font-medium px-2 py-0.5 rounded
              ${isNowInRange
                ? 'text-white'
                : widthPercent > 20
                  ? 'text-white'
                  : 'text-gray-700 dark:text-gray-300 bg-white/80 dark:bg-gray-800/80'
              }
            `}>
              {startTime} - {endTime}
            </span>
          </div>
        </div>

        {/* Recurrence info */}
        <div className="w-28 text-right">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {recurrenceLabel}
          </span>
        </div>
      </div>

      {/* Now playing indicator */}
      {isNowInRange && (
        <div className="mt-2 flex items-center gap-1.5 text-xs text-green-600 dark:text-green-400">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500" />
          </span>
          {t('schedules.card.nowPlaying', 'Now playing')}
        </div>
      )}
    </div>
  )
}

export default ScheduleTimeline
