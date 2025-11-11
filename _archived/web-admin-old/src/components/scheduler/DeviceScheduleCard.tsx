/**
 * DeviceScheduleCard Component
 *
 * Displays individual device schedule information including:
 * - Device name and online status
 * - Current content being played
 * - Next deadline with countdown timer
 * - Manual refresh button
 */

import { memo, useState, useEffect, useCallback } from 'react'
import { Clock, RefreshCw, CheckCircle, XCircle, PlayCircle, AlertCircle } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { AxiosResponse, AxiosError } from 'axios'
import toast from 'react-hot-toast'
import { schedulerAPI } from '../../services/api'
import { Button } from '../shared'
import type { DeviceSchedule, DeviceRefreshResult, CountdownState } from '../../types/scheduler'

interface DeviceScheduleCardProps {
  /** Device schedule data */
  schedule: DeviceSchedule
  /** Callback when device is refreshed */
  onRefresh?: () => void
}

/**
 * Calculate countdown from deadline
 */
function calculateCountdown(deadline: string | null): CountdownState {
  if (!deadline) {
    return {
      days: 0,
      hours: 0,
      minutes: 0,
      seconds: 0,
      totalSeconds: 0,
      isExpired: true,
    }
  }

  const now = new Date().getTime()
  const deadlineTime = new Date(deadline).getTime()
  const diff = Math.floor((deadlineTime - now) / 1000)

  if (diff <= 0) {
    return {
      days: 0,
      hours: 0,
      minutes: 0,
      seconds: 0,
      totalSeconds: 0,
      isExpired: true,
    }
  }

  const days = Math.floor(diff / 86400)
  const hours = Math.floor((diff % 86400) / 3600)
  const minutes = Math.floor((diff % 3600) / 60)
  const seconds = diff % 60

  return {
    days,
    hours,
    minutes,
    seconds,
    totalSeconds: diff,
    isExpired: false,
  }
}

/**
 * Format countdown for display
 */
function formatCountdown(countdown: CountdownState): string {
  if (countdown.isExpired) {
    return 'Expired'
  }

  const parts: string[] = []

  if (countdown.days > 0) {
    parts.push(`${countdown.days}d`)
  }
  if (countdown.hours > 0 || countdown.days > 0) {
    parts.push(`${countdown.hours}h`)
  }
  if (countdown.minutes > 0 || countdown.hours > 0 || countdown.days > 0) {
    parts.push(`${countdown.minutes}m`)
  }
  parts.push(`${countdown.seconds}s`)

  return parts.join(' ')
}

/**
 * Get countdown color based on time remaining
 */
function getCountdownColor(countdown: CountdownState): string {
  if (countdown.isExpired) {
    return 'text-red-600 dark:text-red-400'
  }
  if (countdown.totalSeconds < 300) { // Less than 5 minutes
    return 'text-orange-600 dark:text-orange-400'
  }
  return 'text-green-600 dark:text-green-400'
}

const DeviceScheduleCard = memo(function DeviceScheduleCard({
  schedule,
  onRefresh,
}: DeviceScheduleCardProps) {
  const [countdown, setCountdown] = useState<CountdownState>(() =>
    calculateCountdown(schedule.next_deadline)
  )

  // Update countdown every second
  useEffect(() => {
    const interval = setInterval(() => {
      setCountdown(calculateCountdown(schedule.next_deadline))
    }, 1000)

    return () => clearInterval(interval)
  }, [schedule.next_deadline])

  // Manual refresh mutation
  const refreshMutation = useMutation<
    AxiosResponse<DeviceRefreshResult>,
    AxiosError<{ detail: string }>,
    number
  >({
    mutationFn: (deviceId: number) => schedulerAPI.refreshDevice(deviceId),
    onSuccess: (response) => {
      const result = response.data
      if (result.success) {
        toast.success(
          `Refreshed ${result.items_refreshed} items for ${result.device_name}`,
          { duration: 3000, position: 'bottom-right' }
        )
        onRefresh?.()
      } else {
        toast.error(
          result.error_message || `Failed to refresh ${result.device_name}`,
          { duration: 4000, position: 'bottom-right' }
        )
      }
    },
    onError: (error) => {
      toast.error(
        error.response?.data?.detail || 'Failed to refresh device',
        { duration: 4000, position: 'bottom-right' }
      )
    },
  })

  const handleRefresh = useCallback(() => {
    refreshMutation.mutate(schedule.device_id)
  }, [refreshMutation, schedule.device_id])

  // Determine card border color based on status
  const getBorderColor = (): string => {
    if (!schedule.is_online) return 'border-gray-300 dark:border-gray-600'
    if (countdown.isExpired) return 'border-red-300 dark:border-red-600'
    if (countdown.totalSeconds < 300) return 'border-orange-300 dark:border-orange-600'
    return 'border-green-300 dark:border-green-600'
  }

  return (
    <div
      className={`
        bg-white dark:bg-gray-800
        rounded-lg
        shadow-md
        border-2
        ${getBorderColor()}
        p-4
        hover:shadow-lg
        transition-all
        duration-200
      `}
    >
      {/* Header: Device Name and Status */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 truncate mb-1">
            {schedule.device_name}
          </h3>
          <div className="flex items-center gap-2 text-sm">
            {schedule.is_online ? (
              <div className="flex items-center gap-1 text-green-600 dark:text-green-400">
                <CheckCircle className="w-4 h-4" />
                <span>Online</span>
              </div>
            ) : (
              <div className="flex items-center gap-1 text-gray-500 dark:text-gray-400">
                <XCircle className="w-4 h-4" />
                <span>Offline</span>
              </div>
            )}
          </div>
        </div>

        {/* Refresh Button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={handleRefresh}
          disabled={refreshMutation.isPending || !schedule.is_online}
          loading={refreshMutation.isPending}
          leftIcon={<RefreshCw className="w-4 h-4" />}
        >
          Refresh
        </Button>
      </div>

      {/* Current Content */}
      <div className="mb-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
        <div className="flex items-center gap-2 mb-2">
          <PlayCircle className="w-4 h-4 text-blue-600 dark:text-blue-400" />
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Currently Playing
          </span>
        </div>
        {schedule.current_content?.title || schedule.current_playlist?.name ? (
          <div className="text-sm text-gray-900 dark:text-gray-100">
            {schedule.current_playlist ? (
              <div>
                <span className="font-medium">Playlist:</span> {schedule.current_playlist.name}
              </div>
            ) : schedule.current_content ? (
              <div>
                <span className="font-medium">Content:</span> {schedule.current_content.title}
                <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">
                  ({schedule.current_content.type})
                </span>
              </div>
            ) : null}
          </div>
        ) : (
          <p className="text-sm text-gray-500 dark:text-gray-400 italic">
            No content assigned
          </p>
        )}
      </div>

      {/* Next Deadline and Countdown */}
      <div className="p-3 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-gray-700 dark:to-gray-600 rounded-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Next Deadline
            </span>
          </div>
          {schedule.next_deadline && (
            <span className="text-xs text-gray-600 dark:text-gray-400">
              {new Date(schedule.next_deadline).toLocaleString()}
            </span>
          )}
        </div>

        {/* Countdown Timer */}
        <div className="mt-2 text-center">
          {schedule.next_deadline ? (
            <div className="flex items-center justify-center gap-2">
              <span className={`text-2xl font-bold tabular-nums ${getCountdownColor(countdown)}`}>
                {formatCountdown(countdown)}
              </span>
              {countdown.isExpired && (
                <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400 italic">
              No deadline scheduled
            </p>
          )}
        </div>

        {/* Last Refresh */}
        {schedule.last_refresh && (
          <div className="mt-2 text-xs text-gray-600 dark:text-gray-400 text-center">
            Last refresh: {new Date(schedule.last_refresh).toLocaleString()}
          </div>
        )}
      </div>
    </div>
  )
})

export default DeviceScheduleCard
