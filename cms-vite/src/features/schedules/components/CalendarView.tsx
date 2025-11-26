/**
 * Calendar View Component
 * Monthly calendar view for schedule visualization
 */

import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { PRIORITY_LEVELS, type CalendarEvent } from '../types/schedule.types'

interface CalendarViewProps {
  events: CalendarEvent[]
  selectedDate?: Date
  onDateSelect?: (date: Date) => void
  onEventClick?: (event: CalendarEvent) => void
  isLoading?: boolean
}

export const CalendarView = ({
  events,
  selectedDate,
  onDateSelect,
  onEventClick,
  isLoading = false,
}: CalendarViewProps) => {
  const { t } = useTranslation()
  const [currentMonth, setCurrentMonth] = useState(new Date())

  // Get days in month
  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear()
    const month = date.getMonth()
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    const daysInMonth = lastDay.getDate()
    const startDayOfWeek = firstDay.getDay() // 0 = Sunday

    const days: Date[] = []

    // Add previous month's trailing days
    for (let i = startDayOfWeek - 1; i >= 0; i--) {
      days.push(new Date(year, month, -i))
    }

    // Add current month's days
    for (let i = 1; i <= daysInMonth; i++) {
      days.push(new Date(year, month, i))
    }

    // Add next month's leading days to complete the grid
    const remainingDays = 42 - days.length // 6 rows * 7 days
    for (let i = 1; i <= remainingDays; i++) {
      days.push(new Date(year, month + 1, i))
    }

    return days
  }

  const navigateMonth = (direction: 'prev' | 'next') => {
    setCurrentMonth(new Date(
      currentMonth.getFullYear(),
      currentMonth.getMonth() + (direction === 'prev' ? -1 : 1),
      1
    ))
  }

  const isToday = (date: Date) => {
    const today = new Date()
    return date.toDateString() === today.toDateString()
  }

  const isCurrentMonth = (date: Date) => {
    return date.getMonth() === currentMonth.getMonth() && 
           date.getFullYear() === currentMonth.getFullYear()
  }

  const isSelected = (date: Date) => {
    return selectedDate ? date.toDateString() === selectedDate.toDateString() : false
  }

  const getEventsForDate = (date: Date) => {
    return events.filter(event => {
      const eventDate = new Date(event.start)
      return eventDate.toDateString() === date.toDateString()
    })
  }

  const days = getDaysInMonth(currentMonth)
  const monthYear = currentMonth.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded animate-pulse mb-4"></div>
        <div className="grid grid-cols-7 gap-1">
          {[...Array(42)].map((_, i) => (
            <div key={i} className="h-24 bg-gray-100 dark:bg-gray-700 rounded animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
      {/* Calendar Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{monthYear}</h3>
        <div className="flex gap-2">
          <button
            onClick={() => setCurrentMonth(new Date())}
            className="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md"
          >
            Today
          </button>
          <button
            onClick={() => navigateMonth('prev')}
            className="p-1.5 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <button
            onClick={() => navigateMonth('next')}
            className="p-1.5 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Days of Week Header */}
      <div className="grid grid-cols-7 border-b border-gray-200 dark:border-gray-700">
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
          <div key={day} className="p-2 text-center">
            <span className="text-xs font-medium text-gray-700 dark:text-gray-300">{day}</span>
          </div>
        ))}
      </div>

      {/* Calendar Grid */}
      <div className="grid grid-cols-7">
        {days.map((date, index) => {
          const dateEvents = getEventsForDate(date)
          const hasEvents = dateEvents.length > 0
          const inCurrentMonth = isCurrentMonth(date)
          const today = isToday(date)
          const selected = isSelected(date)

          return (
            <div
              key={index}
              onClick={() => onDateSelect?.(date)}
              className={`
                min-h-[100px] p-2 border-r border-b border-gray-200 dark:border-gray-700 cursor-pointer transition-colors
                ${!inCurrentMonth ? 'bg-gray-50 dark:bg-gray-700' : 'bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700'}
                ${today ? 'bg-blue-50 dark:bg-blue-900' : ''}
                ${selected ? 'bg-purple-50 dark:bg-purple-900 ring-2 ring-purple-500' : ''}
              `}
            >
              {/* Date Number */}
              <div className="flex items-center justify-between mb-1">
                <span
                  className={`
                    text-sm font-medium
                    ${!inCurrentMonth ? 'text-gray-400 dark:text-gray-600' : 'text-gray-900 dark:text-white'}
                    ${today ? 'bg-blue-500 text-white px-2 py-0.5 rounded-full' : ''}
                  `}
                >
                  {date.getDate()}
                </span>
                {hasEvents && (
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {dateEvents.length}
                  </span>
                )}
              </div>

              {/* Events */}
              <div className="space-y-1">
                {dateEvents.slice(0, 3).map((event) => {
                  const priority = PRIORITY_LEVELS[event.schedule.priority]
                  
                  return (
                    <div
                      key={event.id}
                      onClick={(e) => {
                        e.stopPropagation()
                        onEventClick?.(event)
                      }}
                      className={`
                        text-xs p-1 rounded truncate cursor-pointer
                        ${priority.color === 'red' ? 'bg-red-100 text-red-700 hover:bg-red-200' : ''}
                        ${priority.color === 'orange' ? 'bg-orange-100 text-orange-700 hover:bg-orange-200' : ''}
                        ${priority.color === 'blue' ? 'bg-blue-100 text-blue-700 hover:bg-blue-200' : ''}
                        ${priority.color === 'gray' ? 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600' : ''}
                        ${event.isException ? 'line-through opacity-50' : ''}
                      `}
                      title={event.title}
                    >
                      {event.title}
                    </div>
                  )
                })}
                {dateEvents.length > 3 && (
                  <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
                    +{dateEvents.length - 3} more
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Legend */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700">
        <div className="flex flex-wrap gap-4 text-xs">
          <div className="flex items-center gap-2">
            <span className="font-medium text-gray-700 dark:text-gray-300">
              {t('schedules.activeIndicator.priority')}:
            </span>
            {Object.values(PRIORITY_LEVELS).map((priority) => (
              <div key={priority.level} className="flex items-center gap-1">
                <div
                  className={`w-3 h-3 rounded
                    ${priority.color === 'red' ? 'bg-red-500' : ''}
                    ${priority.color === 'orange' ? 'bg-orange-500' : ''}
                    ${priority.color === 'blue' ? 'bg-blue-500' : ''}
                    ${priority.color === 'gray' ? 'bg-gray-500' : ''}
                  `}
                />
                <span className="text-gray-600 dark:text-gray-300">{priority.label}</span>
              </div>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-gray-300 dark:bg-gray-500 rounded line-through"></div>
            <span className="text-gray-600 dark:text-gray-300">
              {t('schedules.exceptionDates.exceptionDate')}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CalendarView