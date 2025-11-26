/**
 * Schedule Preview Calendar Component
 * Visual calendar preview showing next occurrences with priority indicators
 */

import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { ChevronLeft, ChevronRight, Calendar, Clock, X } from 'lucide-react'
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameMonth, isSameDay, addMonths, subMonths } from 'date-fns'
import type { PreviewOccurrence } from '../types/advanced'

interface SchedulePreviewCalendarProps {
  occurrences: PreviewOccurrence[]
  playlistName?: string
  priority?: number
  exceptionDates?: string[]
  className?: string
}

export const SchedulePreviewCalendar = ({
  occurrences,
  playlistName,
  priority = 0,
  exceptionDates = [],
  className = '',
}: SchedulePreviewCalendarProps) => {
  const { t } = useTranslation()
  const [currentMonth, setCurrentMonth] = useState(new Date())
  const [selectedDate, setSelectedDate] = useState<Date | null>(null)

  // Generate calendar days
  const calendarDays = useMemo(() => {
    const start = startOfMonth(currentMonth)
    const end = endOfMonth(currentMonth)

    // Get first day of week (adjust to start on Monday)
    const firstDayOfWeek = start.getDay()
    const adjustedStart = new Date(start)
    adjustedStart.setDate(adjustedStart.getDate() - (firstDayOfWeek === 0 ? 6 : firstDayOfWeek - 1))

    // Get days to fill the calendar (6 weeks)
    const days: Date[] = []
    for (let i = 0; i < 42; i++) {
      const day = new Date(adjustedStart)
      day.setDate(day.getDate() + i)
      days.push(day)
    }

    return days
  }, [currentMonth])

  // Map occurrences to dates
  const occurrenceMap = useMemo(() => {
    const map = new Map<string, PreviewOccurrence[]>()
    occurrences.forEach((occ) => {
      const dateKey = format(occ.date, 'yyyy-MM-dd')
      const existing = map.get(dateKey) || []
      map.set(dateKey, [...existing, occ])
    })
    return map
  }, [occurrences])

  // Check if date is exception
  const isException = (date: Date) => {
    const dateStr = format(date, 'yyyy-MM-dd')
    return exceptionDates.includes(dateStr)
  }

  // Get occurrence for date
  const getOccurrenceForDate = (date: Date) => {
    const dateKey = format(date, 'yyyy-MM-dd')
    return occurrenceMap.get(dateKey)?.[0]
  }

  // Get priority color
  const getPriorityColor = (priorityValue: number) => {
    if (priorityValue >= 75) return 'bg-red-500'
    if (priorityValue >= 50) return 'bg-orange-500'
    if (priorityValue >= 25) return 'bg-blue-500'
    return 'bg-gray-500'
  }

  const selectedOccurrences = selectedDate
    ? occurrenceMap.get(format(selectedDate, 'yyyy-MM-dd'))
    : null

  return (
    <div className={`bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden ${className}`}>
      {/* Header */}
      <div className="p-4 bg-purple-50 dark:bg-purple-900/20 border-b border-purple-100 dark:border-purple-800">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Calendar className="h-5 w-5 text-purple-600 dark:text-purple-400" />
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
              {t('schedules.previewCalendar.title')}
            </h3>
          </div>
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => setCurrentMonth(subMonths(currentMonth, 1))}
              className="p-1 hover:bg-purple-100 dark:hover:bg-purple-800 rounded transition-colors"
            >
              <ChevronLeft className="h-4 w-4 text-gray-600 dark:text-gray-400" />
            </button>
            <span className="px-3 text-sm font-medium text-gray-900 dark:text-white">
              {format(currentMonth, 'MMMM yyyy')}
            </span>
            <button
              type="button"
              onClick={() => setCurrentMonth(addMonths(currentMonth, 1))}
              className="p-1 hover:bg-purple-100 dark:hover:bg-purple-800 rounded transition-colors"
            >
              <ChevronRight className="h-4 w-4 text-gray-600 dark:text-gray-400" />
            </button>
          </div>
        </div>

        {playlistName && (
          <p className="text-xs text-gray-600 dark:text-gray-400">
            {t('schedules.previewCalendar.playlist')} <span className="font-medium">{playlistName}</span>
          </p>
        )}
      </div>

      {/* Calendar Grid */}
      <div className="p-4">
        {/* Weekday Headers */}
        <div className="grid grid-cols-7 gap-1 mb-2">
          {['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'].map((day) => (
            <div
              key={day}
              className="text-center text-xs font-medium text-gray-500 dark:text-gray-400 py-1"
            >
              {t(`schedules.previewCalendar.weekdays.${day}`)}
            </div>
          ))}
        </div>

        {/* Calendar Days */}
        <div className="grid grid-cols-7 gap-1">
          {calendarDays.map((day, index) => {
            const occurrence = getOccurrenceForDate(day)
            const isExceptionDay = isException(day)
            const isCurrentMonth = isSameMonth(day, currentMonth)
            const isToday = isSameDay(day, new Date())
            const isSelected = selectedDate ? isSameDay(day, selectedDate) : false

            return (
              <button
                key={index}
                type="button"
                onClick={() => occurrence && setSelectedDate(day)}
                className={`
                  relative aspect-square p-1 rounded-md text-xs transition-all
                  ${!isCurrentMonth ? 'opacity-30' : ''}
                  ${isToday ? 'ring-2 ring-purple-500' : ''}
                  ${isSelected ? 'bg-purple-100 dark:bg-purple-900' : 'hover:bg-gray-100 dark:hover:bg-gray-700'}
                  ${occurrence && !isExceptionDay ? 'font-semibold' : ''}
                  ${isExceptionDay ? 'line-through opacity-50' : ''}
                  ${occurrence && !isSelected ? 'cursor-pointer' : 'cursor-default'}
                `}
                disabled={!occurrence}
              >
                <span className={`
                  ${isToday ? 'text-purple-600 dark:text-purple-400' : 'text-gray-700 dark:text-gray-300'}
                `}>
                  {format(day, 'd')}
                </span>

                {/* Occurrence Indicator */}
                {occurrence && !isExceptionDay && (
                  <div className={`
                    absolute bottom-1 left-1/2 transform -translate-x-1/2
                    w-1 h-1 rounded-full
                    ${getPriorityColor(occurrence.priority)}
                  `} />
                )}

                {/* Exception Indicator */}
                {isExceptionDay && (
                  <div className="absolute top-0 right-0">
                    <X className="h-3 w-3 text-red-500" />
                  </div>
                )}
              </button>
            )
          })}
        </div>

        {/* Legend */}
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex flex-wrap gap-3 text-xs">
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-red-500" />
              <span className="text-gray-600 dark:text-gray-400">{t('schedules.priorityManager.levels.critical')}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-orange-500" />
              <span className="text-gray-600 dark:text-gray-400">{t('schedules.priorityManager.levels.high')}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-blue-500" />
              <span className="text-gray-600 dark:text-gray-400">{t('schedules.priorityManager.levels.normal')}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-gray-500" />
              <span className="text-gray-600 dark:text-gray-400">{t('schedules.priorityManager.levels.low')}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <X className="h-3 w-3 text-red-500" />
              <span className="text-gray-600 dark:text-gray-400">{t('schedules.previewCalendar.legend.exception')}</span>
            </div>
          </div>
        </div>

        {/* Selected Date Details */}
        {selectedDate && selectedOccurrences && selectedOccurrences.length > 0 && (
          <div className="mt-4 p-3 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-md">
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {format(selectedDate, 'MMMM d, yyyy')}
                </span>
              </div>
              <button
                type="button"
                onClick={() => setSelectedDate(null)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="space-y-2">
              {selectedOccurrences.map((occ, idx) => (
                <div key={idx} className="text-xs text-gray-600 dark:text-gray-400">
                  <div className="flex items-center justify-between">
                    <span>
                      {occ.startTime} - {occ.endTime}
                    </span>
                    <span className="px-2 py-0.5 bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-200 rounded">
                      {t('schedules.previewCalendar.priorityLabel', { value: occ.priority })}
                    </span>
                  </div>
                  {occ.isException && (
                    <p className="text-red-600 dark:text-red-400 mt-1">{t('schedules.previewCalendar.exceptionWillNotRun')}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Summary */}
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <p className="text-xs text-gray-600 dark:text-gray-400">
            {t('schedules.previewCalendar.showingNext')}{' '}
            <span className="font-medium">{occurrences.length}</span>{' '}
            {t(occurrences.length !== 1 ? 'schedules.previewCalendar.occurrences' : 'schedules.previewCalendar.occurrence')}
            {exceptionDates.length > 0 && (
              <span> {t(
                exceptionDates.length !== 1
                  ? 'schedules.previewCalendar.exceptionCount_plural'
                  : 'schedules.previewCalendar.exceptionCount',
                { count: exceptionDates.length }
              )}</span>
            )}
          </p>
        </div>
      </div>
    </div>
  )
}

export default SchedulePreviewCalendar
