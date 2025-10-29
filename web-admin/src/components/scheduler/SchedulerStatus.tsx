/**
 * SchedulerStatus Component
 *
 * Displays scheduler service status and provides controls for:
 * - Service status monitoring (running/stopped)
 * - Next scheduled run countdown
 * - Manual refresh all devices
 * - Device schedule grid
 * - Auto-refresh every 30 seconds
 */

import { memo, useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AxiosResponse, AxiosError } from 'axios'
import {
  Activity,
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertCircle,
  Clock,
  Server,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { schedulerAPI } from '../../services/api'
import { Button, LoadingSkeleton } from '../shared'
import DeviceScheduleCard from './DeviceScheduleCard'
import type {
  SchedulerStatus as SchedulerStatusType,
  DeviceSchedule,
  BulkRefreshResult,
} from '../../types/scheduler'

const SchedulerStatus = memo(function SchedulerStatus() {
  const queryClient = useQueryClient()
  const [autoRefreshCountdown, setAutoRefreshCountdown] = useState<number>(30)

  // Fetch scheduler status with auto-refresh every 30 seconds
  const { data: statusData, isLoading: isLoadingStatus } = useQuery<
    AxiosResponse<SchedulerStatusType>
  >({
    queryKey: ['scheduler-status'],
    queryFn: () => schedulerAPI.getStatus(),
    refetchInterval: 30000, // Auto-refresh every 30 seconds
  })

  // Fetch device schedules with auto-refresh every 30 seconds
  const { data: schedulesData, isLoading: isLoadingSchedules } = useQuery<
    AxiosResponse<DeviceSchedule[]>
  >({
    queryKey: ['device-schedules'],
    queryFn: () => schedulerAPI.getAllDeviceSchedules(),
    refetchInterval: 30000, // Auto-refresh every 30 seconds
  })

  // Countdown timer for auto-refresh
  useEffect(() => {
    setAutoRefreshCountdown(30)
    const interval = setInterval(() => {
      setAutoRefreshCountdown((prev) => {
        if (prev <= 1) {
          return 30
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(interval)
  }, [statusData, schedulesData])

  // Manual refresh all devices mutation
  const refreshAllMutation = useMutation<
    AxiosResponse<BulkRefreshResult>,
    AxiosError<{ detail: string }>,
    void
  >({
    mutationFn: () => schedulerAPI.refreshAll(),
    onSuccess: (response) => {
      const result = response.data
      toast.success(
        `Refreshed ${result.successful} of ${result.total_devices} devices`,
        { duration: 4000, position: 'bottom-right' }
      )
      if (result.failed > 0) {
        toast.error(
          `${result.failed} devices failed to refresh. Check logs for details.`,
          { duration: 5000, position: 'bottom-right' }
        )
      }
      // Refresh schedules after bulk refresh
      queryClient.invalidateQueries({ queryKey: ['device-schedules'] })
    },
    onError: (error) => {
      toast.error(
        error.response?.data?.detail || 'Failed to refresh devices',
        { duration: 4000, position: 'bottom-right' }
      )
    },
  })

  const handleRefreshAll = () => {
    refreshAllMutation.mutate()
  }

  const handleDeviceRefresh = () => {
    // Invalidate schedules to fetch fresh data
    queryClient.invalidateQueries({ queryKey: ['device-schedules'] })
  }

  const status = statusData?.data
  const schedules = schedulesData?.data || []

  // Filter online and offline devices
  const onlineDevices = schedules.filter((s) => s.is_online)
  const offlineDevices = schedules.filter((s) => !s.is_online)

  // Get status icon and color
  const getStatusIcon = () => {
    if (!status) return <Activity className="w-5 h-5 text-gray-500" />
    switch (status.status) {
      case 'running':
        return <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
      case 'stopped':
        return <XCircle className="w-5 h-5 text-gray-600 dark:text-gray-400" />
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
      default:
        return <Activity className="w-5 h-5 text-gray-500" />
    }
  }

  const getStatusText = () => {
    if (!status) return 'Loading...'
    switch (status.status) {
      case 'running':
        return 'Running'
      case 'stopped':
        return 'Stopped'
      case 'error':
        return 'Error'
      default:
        return 'Unknown'
    }
  }

  const getStatusColor = () => {
    if (!status) return 'bg-gray-100 dark:bg-gray-800 border-gray-300 dark:border-gray-600'
    switch (status.status) {
      case 'running':
        return 'bg-green-50 dark:bg-green-900/20 border-green-300 dark:border-green-600'
      case 'stopped':
        return 'bg-gray-100 dark:bg-gray-800 border-gray-300 dark:border-gray-600'
      case 'error':
        return 'bg-red-50 dark:bg-red-900/20 border-red-300 dark:border-red-600'
      default:
        return 'bg-gray-100 dark:bg-gray-800 border-gray-300 dark:border-gray-600'
    }
  }

  if (isLoadingStatus || isLoadingSchedules) {
    return (
      <div className="space-y-6">
        <LoadingSkeleton variant="card" count={1} />
        <LoadingSkeleton variant="grid" count={3} />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Scheduler Service Status Card */}
      <div className={`rounded-lg border-2 p-6 ${getStatusColor()}`}>
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            {getStatusIcon()}
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                Scheduler Service
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Status: <span className="font-medium">{getStatusText()}</span>
              </p>
            </div>
          </div>

          {/* Manual Refresh All Button */}
          <Button
            variant="primary"
            size="md"
            onClick={handleRefreshAll}
            disabled={refreshAllMutation.isPending || status?.status !== 'running'}
            loading={refreshAllMutation.isPending}
            leftIcon={<RefreshCw className="w-5 h-5" />}
          >
            Refresh All Devices
          </Button>
        </div>

        {/* Service Statistics Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Devices Count */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
            <div className="flex items-center gap-2 mb-2">
              <Server className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Total Devices
              </span>
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {status?.devices_count || 0}
            </p>
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
              {onlineDevices.length} online, {offlineDevices.length} offline
            </p>
          </div>

          {/* Total Refreshes */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
            <div className="flex items-center gap-2 mb-2">
              <RefreshCw className="w-5 h-5 text-green-600 dark:text-green-400" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Total Refreshes
              </span>
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {status?.total_refreshes || 0}
            </p>
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
              Since service started
            </p>
          </div>

          {/* Last Run */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
            <div className="flex items-center gap-2 mb-2">
              <Clock className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Last Run
              </span>
            </div>
            <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              {status?.last_run
                ? new Date(status.last_run).toLocaleString()
                : 'Never'}
            </p>
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
              Last execution time
            </p>
          </div>

          {/* Auto-Refresh Countdown */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-5 h-5 text-orange-600 dark:text-orange-400" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Auto-Refresh
              </span>
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 tabular-nums">
              {autoRefreshCountdown}s
            </p>
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
              Until next update
            </p>
          </div>
        </div>

        {/* Error Message */}
        {status?.error_message && (
          <div className="mt-4 p-3 bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-600 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-red-900 dark:text-red-100">
                  Error Message
                </p>
                <p className="text-sm text-red-800 dark:text-red-200 mt-1">
                  {status.error_message}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Device Schedules Section */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Device Schedules ({schedules.length})
        </h3>

        {/* Online Devices */}
        {onlineDevices.length > 0 && (
          <div className="mb-6">
            <h4 className="text-md font-medium text-green-700 dark:text-green-400 mb-3 flex items-center gap-2">
              <CheckCircle className="w-5 h-5" />
              Online Devices ({onlineDevices.length})
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {onlineDevices.map((schedule) => (
                <DeviceScheduleCard
                  key={schedule.device_id}
                  schedule={schedule}
                  onRefresh={handleDeviceRefresh}
                />
              ))}
            </div>
          </div>
        )}

        {/* Offline Devices */}
        {offlineDevices.length > 0 && (
          <div>
            <h4 className="text-md font-medium text-gray-600 dark:text-gray-400 mb-3 flex items-center gap-2">
              <XCircle className="w-5 h-5" />
              Offline Devices ({offlineDevices.length})
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {offlineDevices.map((schedule) => (
                <DeviceScheduleCard
                  key={schedule.device_id}
                  schedule={schedule}
                  onRefresh={handleDeviceRefresh}
                />
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {schedules.length === 0 && (
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-8 text-center">
            <Server className="w-12 h-12 text-gray-400 dark:text-gray-600 mx-auto mb-3" />
            <p className="text-gray-600 dark:text-gray-400">
              No devices to display. Register devices to see their schedules.
            </p>
          </div>
        )}
      </div>
    </div>
  )
})

export default SchedulerStatus
