/**
 * Active Schedule Indicator Component
 * Real-time display of currently active schedule with countdown
 */

import { useState, useEffect } from 'react'
import { Play, Clock, Calendar, TrendingUp, ChevronRight } from 'lucide-react'
import { useActiveSchedule, useTimeUntilNextChange } from '../hooks/useAdvancedSchedules'
import { format } from 'date-fns'

type DisplayMode = 'banner' | 'widget' | 'inline'

interface ActiveScheduleIndicatorProps {
  mode?: DisplayMode
  className?: string
  onScheduleClick?: (scheduleId: number) => void
  autoRefresh?: boolean
  refreshInterval?: number
}

export const ActiveScheduleIndicator = ({
  mode = 'banner',
  className = '',
  onScheduleClick,
  autoRefresh = true,
  refreshInterval = 60000, // 1 minute
}: ActiveScheduleIndicatorProps) => {
  const [currentTime, setCurrentTime] = useState(new Date())

  // Update current time every second for countdown
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date())
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  // Fetch active schedule
  const { data, isLoading, refetch } = useActiveSchedule(
    format(currentTime, 'yyyy-MM-dd'),
    format(currentTime, 'HH:mm'),
    {
      enabled: true,
      refetchInterval: autoRefresh ? refreshInterval : false,
    }
  )

  // Calculate time until change (if we have next occurrence data)
  const timeRemaining = useTimeUntilNextChange(
    data?.schedule?.next_run
      ? {
          date: data.schedule.next_run.split('T')[0],
          start_time: data.schedule.next_run.split('T')[1]?.substring(0, 5),
        }
      : undefined
  )

  if (isLoading) {
    return (
      <div className={getModeClasses(mode, className)}>
        <div className="flex items-center gap-2">
          <div className="animate-spin h-4 w-4 border-2 border-purple-500 border-t-transparent rounded-full" />
          <span className="text-sm text-gray-600 dark:text-gray-400">Checking active schedule...</span>
        </div>
      </div>
    )
  }

  if (!data?.is_found || !data.schedule) {
    return (
      <div className={getModeClasses(mode, className)}>
        <div className="flex items-center gap-2">
          <Calendar className="h-5 w-5 text-gray-400" />
          <span className="text-sm text-gray-600 dark:text-gray-400">No active schedule</span>
        </div>
      </div>
    )
  }

  // Render based on mode
  switch (mode) {
    case 'banner':
      return <BannerMode data={data} timeRemaining={timeRemaining} currentTime={currentTime} onClick={onScheduleClick} className={className} />
    case 'widget':
      return <WidgetMode data={data} timeRemaining={timeRemaining} currentTime={currentTime} onClick={onScheduleClick} className={className} />
    case 'inline':
      return <InlineMode data={data} timeRemaining={timeRemaining} onClick={onScheduleClick} className={className} />
    default:
      return null
  }
}

// ========================================
// Helper Functions
// ========================================

const getModeClasses = (mode: DisplayMode, className: string) => {
  const base = 'rounded-lg border'
  switch (mode) {
    case 'banner':
      return `${base} bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 border-purple-200 dark:border-purple-800 p-4 ${className}`
    case 'widget':
      return `${base} bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 p-4 ${className}`
    case 'inline':
      return `${base} bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 px-3 py-2 ${className}`
    default:
      return className
  }
}

// ========================================
// Banner Mode Component
// ========================================

const BannerMode = ({
  data,
  timeRemaining,
  currentTime,
  onClick,
  className,
}: any) => {
  return (
    <div className={getModeClasses('banner', className)}>
      <div className="flex items-center justify-between gap-4">
        {/* Left: Currently Playing */}
        <div className="flex items-start gap-3 flex-1">
          <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
            <Play className="h-5 w-5 text-green-600 dark:text-green-400" fill="currentColor" />
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                Currently Playing
              </h3>
              <span className="px-2 py-0.5 bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200 text-xs rounded-full font-medium">
                Live
              </span>
            </div>

            <div className="space-y-1">
              <p className="text-base font-medium text-gray-900 dark:text-white truncate">
                {data.schedule_name}
              </p>
              <div className="flex items-center gap-4 text-xs text-gray-600 dark:text-gray-400">
                <span className="flex items-center gap-1">
                  <Calendar className="h-3 w-3" />
                  {format(currentTime, 'MMM d, yyyy')}
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {data.schedule?.start_time || '00:00'} - {data.schedule?.end_time || '23:59'}
                </span>
                <span className="flex items-center gap-1">
                  <TrendingUp className="h-3 w-3" />
                  Priority {data.priority || 0}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Time Remaining */}
        {timeRemaining && (
          <div className="text-right">
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Next change in</p>
            <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
              {timeRemaining}
            </p>
          </div>
        )}

        {/* View Button */}
        {onClick && data.schedule?.id && (
          <button
            type="button"
            onClick={() => onClick(data.schedule.id)}
            className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors text-sm font-medium"
          >
            View Schedule
          </button>
        )}
      </div>
    </div>
  )
}

// ========================================
// Widget Mode Component
// ========================================

const WidgetMode = ({
  data,
  timeRemaining,
  currentTime,
  onClick,
  className,
}: any) => {
  return (
    <div className={getModeClasses('widget', className)}>
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Play className="h-4 w-4 text-green-600 dark:text-green-400" fill="currentColor" />
            <h4 className="text-sm font-semibold text-gray-900 dark:text-white">Active Now</h4>
          </div>
          <span className="px-2 py-0.5 bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200 text-xs rounded-full">
            Live
          </span>
        </div>

        {/* Schedule Info */}
        <div>
          <p className="text-sm font-medium text-gray-900 dark:text-white mb-2 truncate">
            {data.schedule_name}
          </p>

          <div className="space-y-1.5 text-xs text-gray-600 dark:text-gray-400">
            <div className="flex items-center gap-2">
              <Clock className="h-3 w-3 flex-shrink-0" />
              <span>
                {data.schedule?.start_time || '00:00'} - {data.schedule?.end_time || '23:59'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-3 w-3 flex-shrink-0" />
              <span>Priority {data.priority || 0}</span>
            </div>
            {timeRemaining && (
              <div className="flex items-center gap-2">
                <Calendar className="h-3 w-3 flex-shrink-0" />
                <span>Changes in {timeRemaining}</span>
              </div>
            )}
          </div>
        </div>

        {/* View Link */}
        {onClick && data.schedule?.id && (
          <button
            type="button"
            onClick={() => onClick(data.schedule.id)}
            className="w-full flex items-center justify-center gap-1 px-3 py-1.5 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded text-xs font-medium transition-colors"
          >
            View Details
            <ChevronRight className="h-3 w-3" />
          </button>
        )}
      </div>
    </div>
  )
}

// ========================================
// Inline Mode Component
// ========================================

const InlineMode = ({ data, timeRemaining, onClick, className }: any) => {
  return (
    <div className={getModeClasses('inline', className)}>
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <Play className="h-3 w-3 text-green-600 dark:text-green-400 flex-shrink-0" fill="currentColor" />
          <span className="text-xs font-medium text-gray-900 dark:text-white truncate">
            {data.schedule_name}
          </span>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            ({data.schedule?.start_time || '00:00'} - {data.schedule?.end_time || '23:59'})
          </span>
        </div>

        {timeRemaining && (
          <span className="text-xs font-medium text-purple-600 dark:text-purple-400 whitespace-nowrap">
            {timeRemaining}
          </span>
        )}

        {onClick && data.schedule?.id && (
          <button
            type="button"
            onClick={() => onClick(data.schedule.id)}
            className="text-gray-400 hover:text-purple-600 dark:hover:text-purple-400 transition-colors"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  )
}

export default ActiveScheduleIndicator
