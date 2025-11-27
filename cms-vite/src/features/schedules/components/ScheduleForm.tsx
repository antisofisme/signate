/**
 * Schedule Form Component
 * Create/Edit schedule with all configurations
 */

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useState, useEffect } from 'react'
import { Loader2 } from 'lucide-react'
import RecurrenceBuilder from './RecurrenceBuilder'
import ConflictDetector from './ConflictDetector'
import {
  PRIORITY_LEVELS,
  TIMEZONES,
  type Schedule,
  type CreateScheduleRequest,
  type UpdateScheduleRequest,
  type RecurrenceType,
  type RecurrencePattern,
  type PriorityLevel,
} from '../types/schedule.types'
import { apiClient } from '@/lib/api/client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import { renderIcon } from '@/shared/utils/iconHelper'

// Validation schema
const scheduleFormSchema = z.object({
  name: z.string().min(1, 'Schedule name is required').max(255),
  description: z.string().optional(),
  playlist_id: z.number().min(1, 'Please select a playlist'),
  device_ids: z.array(z.number()).min(1, 'Please select at least one device'),
  start_date: z.string().min(1, 'Start date is required'),
  end_date: z.string().optional(),
  start_time: z.string().min(1, 'Start time is required'),
  end_time: z.string().min(1, 'End time is required'),
  recurrence_type: z.enum(['once', 'daily', 'weekly', 'monthly', 'custom']),
  priority: z.enum(['low', 'normal', 'high', 'critical']),
  timezone: z.string().min(1, 'Timezone is required'),
})

type ScheduleFormData = z.infer<typeof scheduleFormSchema>

interface ScheduleFormProps {
  schedule?: Schedule
  onSubmit: (data: CreateScheduleRequest | UpdateScheduleRequest) => void
  onCancel: () => void
  isLoading?: boolean
  showButtons?: boolean // For modal usage - buttons can be in footer
}

interface Playlist {
  id: number
  name: string
}

interface Device {
  id: number
  name: string
  status: string
}

export const ScheduleForm = ({
  schedule,
  onSubmit,
  onCancel,
  isLoading = false,
  showButtons = true,
}: ScheduleFormProps) => {
  const [playlists, setPlaylists] = useState<Playlist[]>([])
  const [devices, setDevices] = useState<Device[]>([])
  const [loadingData, setLoadingData] = useState(true)
  const [recurrencePattern, setRecurrencePattern] = useState<RecurrencePattern>(
    schedule?.recurrence_pattern || {}
  )
  const [exceptionDates, setExceptionDates] = useState<string[]>(
    schedule?.exception_dates || []
  )
  const [showConflictDetector, setShowConflictDetector] = useState(false)

  const isEdit = !!schedule

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<ScheduleFormData>({
    resolver: zodResolver(scheduleFormSchema),
    defaultValues: schedule
      ? {
          name: schedule.name,
          description: schedule.description,
          playlist_id: schedule.playlist_id,
          device_ids: schedule.device_ids,
          start_date: schedule.start_date,
          end_date: schedule.end_date,
          start_time: schedule.start_time,
          end_time: schedule.end_time,
          recurrence_type: schedule.recurrence_type,
          priority: schedule.priority,
          timezone: schedule.timezone,
        }
      : {
          name: '',
          description: '',
          playlist_id: 0,
          device_ids: [],
          start_date: new Date().toISOString().split('T')[0],
          end_date: '',
          start_time: '09:00',
          end_time: '18:00',
          recurrence_type: 'once',
          priority: 'normal',
          timezone: 'Asia/Jakarta',
        },
  })

  const recurrenceType = watch('recurrence_type')
  const startDate = watch('start_date')
  const endDate = watch('end_date')
  const selectedDeviceIds = watch('device_ids')

  // Fetch playlists and devices
  useEffect(() => {
    const fetchData = async () => {
      setLoadingData(true)
      try {
        const [playlistsRes, devicesRes] = await Promise.all([
          apiClient.get(API_ENDPOINTS.PLAYLISTS.LIST),
          apiClient.get(API_ENDPOINTS.DEVICES.LIST),
        ])

        setPlaylists(playlistsRes.data.playlists || [])
        setDevices(devicesRes.data.devices || [])
      } catch (error) {
        console.error('Failed to fetch data:', error)
      } finally {
        setLoadingData(false)
      }
    }

    fetchData()
  }, [])

  // Helper to compare values (handles arrays properly)
  const isEqual = (a: unknown, b: unknown): boolean => {
    if (Array.isArray(a) && Array.isArray(b)) {
      return JSON.stringify(a.slice().sort()) === JSON.stringify(b.slice().sort())
    }
    if (typeof a === 'object' && typeof b === 'object' && a !== null && b !== null) {
      return JSON.stringify(a) === JSON.stringify(b)
    }
    return a === b
  }

  // Convert priority string to number for backend
  const priorityToNumber = (priority: PriorityLevel): number => {
    const mapping: Record<PriorityLevel, number> = {
      low: 10,
      normal: 50,
      high: 75,
      critical: 100,
    }
    return mapping[priority] ?? 50
  }

  const handleFormSubmit = (data: ScheduleFormData) => {
    const formData = {
      ...data,
      priority: priorityToNumber(data.priority), // Convert to number for backend
      recurrence_pattern: recurrenceType === 'once' ? undefined : recurrencePattern,
      exception_dates: exceptionDates.length > 0 ? exceptionDates : undefined,
    }

    if (isEdit && schedule) {
      // For edit, only send changed fields
      const updateData: UpdateScheduleRequest = {}

      // Compare each field properly (including arrays)
      if (!isEqual(formData.name, schedule.name)) updateData.name = formData.name
      if (!isEqual(formData.description, schedule.description)) updateData.description = formData.description
      if (!isEqual(formData.device_ids, schedule.device_ids)) updateData.device_ids = formData.device_ids
      if (!isEqual(formData.start_date, schedule.start_date)) updateData.start_date = formData.start_date
      if (!isEqual(formData.end_date, schedule.end_date)) updateData.end_date = formData.end_date
      if (!isEqual(formData.start_time, schedule.start_time)) updateData.start_time = formData.start_time
      if (!isEqual(formData.end_time, schedule.end_time)) updateData.end_time = formData.end_time
      if (!isEqual(formData.recurrence_pattern, schedule.recurrence_pattern)) {
        updateData.recurrence_pattern = formData.recurrence_pattern
      }
      if (!isEqual(formData.exception_dates, schedule.exception_dates)) {
        updateData.exception_dates = formData.exception_dates
      }
      if (formData.priority !== priorityToNumber(schedule.priority)) {
        updateData.priority = formData.priority as unknown as PriorityLevel
      }
      if (!isEqual(formData.timezone, schedule.timezone)) updateData.timezone = formData.timezone

      onSubmit(updateData)
    } else {
      onSubmit(formData as unknown as CreateScheduleRequest)
    }
  }

  const addExceptionDate = (date: string) => {
    if (!exceptionDates.includes(date)) {
      setExceptionDates([...exceptionDates, date])
    }
  }

  const removeExceptionDate = (date: string) => {
    setExceptionDates(exceptionDates.filter((d) => d !== date))
  }

  const selectedDevices = devices.filter((d) => selectedDeviceIds.includes(d.id))

  if (loadingData) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin h-8 w-8 border-4 border-purple-500 border-t-transparent rounded-full mx-auto mb-4"></div>
        <p className="text-gray-600">Loading playlists and devices...</p>
      </div>
    )
  }

  return (
    <form id="schedule-form" onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6" aria-label={isEdit ? 'Edit schedule form' : 'Create schedule form'}>
      {/* Basic Information */}
      <fieldset className="space-y-4">
        <legend className="text-lg font-semibold text-gray-900 dark:text-white">Basic Information</legend>

        {/* Name */}
        <div>
          <label htmlFor="schedule-name" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Schedule Name <span className="text-red-500" aria-hidden="true">*</span>
          </label>
          <input
            {...register('name')}
            id="schedule-name"
            type="text"
            aria-required="true"
            aria-invalid={!!errors.name}
            aria-describedby={errors.name ? 'schedule-name-error' : undefined}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
            placeholder="e.g., Morning Playlist Schedule"
            disabled={isLoading}
          />
          {errors.name && (
            <p id="schedule-name-error" className="mt-1 text-sm text-red-600" role="alert">{errors.name.message}</p>
          )}
        </div>

        {/* Description */}
        <div>
          <label htmlFor="schedule-description" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Description
          </label>
          <textarea
            {...register('description')}
            id="schedule-description"
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
            placeholder="Optional description..."
            disabled={isLoading}
          />
        </div>
      </fieldset>

      {/* Playlist Selection */}
      <div>
        <label htmlFor="schedule-playlist" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Playlist <span className="text-red-500" aria-hidden="true">*</span>
        </label>
        <select
          {...register('playlist_id', { valueAsNumber: true })}
          id="schedule-playlist"
          disabled={isLoading || isEdit}
          aria-required="true"
          aria-invalid={!!errors.playlist_id}
          aria-describedby={errors.playlist_id ? 'playlist-error' : undefined}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
        >
          <option value="">-- Select Playlist --</option>
          {playlists.map((playlist) => (
            <option key={playlist.id} value={playlist.id}>
              {playlist.name}
            </option>
          ))}
        </select>
        {errors.playlist_id && (
          <p id="playlist-error" className="mt-1 text-sm text-red-600" role="alert">{errors.playlist_id.message}</p>
        )}
      </div>

      {/* Device Selection */}
      <fieldset>
        <legend className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          Devices <span className="text-red-500" aria-hidden="true">*</span> ({selectedDevices.length} selected)
        </legend>
        <div
          className="max-h-40 overflow-y-auto border border-gray-300 dark:border-gray-600 rounded-md p-3 bg-white dark:bg-gray-800"
          role="group"
          aria-label="Select devices for schedule"
          aria-describedby={errors.device_ids ? 'devices-error' : undefined}
        >
          <div className="space-y-2">
            {devices.map((device) => (
              <label key={device.id} className="flex items-center gap-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 p-1 rounded">
                <input
                  type="checkbox"
                  value={device.id}
                  checked={selectedDeviceIds.includes(device.id)}
                  onChange={(e) => {
                    const id = Number(e.target.value)
                    if (e.target.checked) {
                      setValue('device_ids', [...selectedDeviceIds, id])
                    } else {
                      setValue('device_ids', selectedDeviceIds.filter((d) => d !== id))
                    }
                  }}
                  disabled={isLoading}
                  className="w-4 h-4 rounded border-gray-300 text-purple-600 focus:ring-purple-500 focus:ring-2"
                  aria-label={`Select ${device.name}`}
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">{device.name}</span>
                <span className={`text-xs px-2 py-0.5 rounded ${
                  device.status === 'online'
                    ? 'bg-green-100 text-green-700'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                }`}>
                  {device.status}
                </span>
              </label>
            ))}
          </div>
        </div>
        {errors.device_ids && (
          <p id="devices-error" className="mt-1 text-sm text-red-600" role="alert">{errors.device_ids.message}</p>
        )}
      </fieldset>

      {/* Schedule Timing */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Schedule Timing</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Start Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Start Date *
            </label>
            <input
              {...register('start_date')}
              type="date"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              disabled={isLoading}
            />
            {errors.start_date && (
              <p className="mt-1 text-sm text-red-600">{errors.start_date.message}</p>
            )}
          </div>

          {/* End Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              End Date
            </label>
            <input
              {...register('end_date')}
              type="date"
              min={startDate}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              disabled={isLoading}
            />
          </div>

          {/* Start Time */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Start Time *
            </label>
            <input
              {...register('start_time')}
              type="time"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              disabled={isLoading}
            />
            {errors.start_time && (
              <p className="mt-1 text-sm text-red-600">{errors.start_time.message}</p>
            )}
          </div>

          {/* End Time */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              End Time *
            </label>
            <input
              {...register('end_time')}
              type="time"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              disabled={isLoading}
            />
            {errors.end_time && (
              <p className="mt-1 text-sm text-red-600">{errors.end_time.message}</p>
            )}
          </div>
        </div>

        {/* Timezone */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Timezone *
          </label>
          <select
            {...register('timezone')}
            disabled={isLoading}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          >
            {TIMEZONES.map((tz) => (
              <option key={tz.value} value={tz.value}>
                {tz.label}
              </option>
            ))}
          </select>
          {errors.timezone && (
            <p className="mt-1 text-sm text-red-600">{errors.timezone.message}</p>
          )}
        </div>
      </div>

      {/* Recurrence */}
      <RecurrenceBuilder
        recurrenceType={recurrenceType}
        recurrencePattern={recurrencePattern}
        onTypeChange={(type) => setValue('recurrence_type', type)}
        onPatternChange={setRecurrencePattern}
        disabled={isLoading}
      />

      {/* Exception Dates */}
      {recurrenceType !== 'once' && (
        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Exception Dates</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Specify dates when this schedule should not run
          </p>

          <div className="flex items-center gap-2">
            <input
              type="date"
              min={startDate}
              max={endDate}
              id="exception-date-input"
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              disabled={isLoading}
            />
            <button
              type="button"
              onClick={() => {
                const input = document.getElementById('exception-date-input') as HTMLInputElement
                if (input.value) {
                  addExceptionDate(input.value)
                  input.value = ''
                }
              }}
              disabled={isLoading}
              className="px-3 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
            >
              Add Exception
            </button>
          </div>

          {exceptionDates.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {exceptionDates.map((date) => (
                <div
                  key={date}
                  className="inline-flex items-center gap-1 px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm"
                >
                  <span>{new Date(date).toLocaleDateString()}</span>
                  <button
                    type="button"
                    onClick={() => removeExceptionDate(date)}
                    className="hover:text-red-900"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Priority */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          Priority Level *
        </label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {Object.values(PRIORITY_LEVELS).map((priority) => {
            const selected = watch('priority') === priority.level

            return (
              <button
                key={priority.level}
                type="button"
                onClick={() => setValue('priority', priority.level)}
                disabled={isLoading}
                className={`
                  p-3 rounded-lg border-2 transition-all
                  ${
                    selected
                      ? `border-${priority.color}-500 bg-${priority.color}-50 dark:bg-${priority.color}-900 shadow-md`
                      : `border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 hover:border-${priority.color}-300 dark:hover:border-${priority.color}-500`
                  }
                  ${isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                `}
              >
                <div className="flex flex-col items-center gap-1">
                  {renderIcon(priority.icon, { className: 'w-8 h-8' })}
                  <span className="text-xs font-semibold text-gray-900 dark:text-white">
                    {priority.label}
                  </span>
                </div>
              </button>
            )
          })}
        </div>
        <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
          {PRIORITY_LEVELS[watch('priority')].description}
        </p>
      </div>

      {/* Conflict Detection */}
      <div className="flex items-center justify-between p-4 bg-yellow-50 dark:bg-yellow-900 border border-yellow-200 dark:border-yellow-800 rounded-lg">
        <div>
          <h4 className="text-sm font-semibold text-yellow-900 dark:text-yellow-200">Check for Conflicts</h4>
          <p className="text-xs text-yellow-800 dark:text-yellow-300 mt-1">
            Detect scheduling conflicts with existing schedules
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowConflictDetector(!showConflictDetector)}
          className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 text-sm"
        >
          {showConflictDetector ? 'Hide' : 'Check'} Conflicts
        </button>
      </div>

      {/* Conflict Detector */}
      {showConflictDetector && (
        <ConflictDetector
          playlistId={watch('playlist_id')}
          deviceIds={selectedDeviceIds}
          startDate={startDate}
          endDate={endDate}
          startTime={watch('start_time')}
          endTime={watch('end_time')}
          recurrenceType={recurrenceType}
          recurrencePattern={recurrencePattern}
          excludeScheduleId={schedule?.id}
        />
      )}

      {/* Action Buttons - Only rendered when showButtons is true */}
      {showButtons && (
        <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700" role="group" aria-label="Form actions">
          <button
            type="button"
            onClick={onCancel}
            disabled={isLoading}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
            aria-label="Cancel and close form"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isLoading}
            aria-busy={isLoading}
            className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2 transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
          >
            {isLoading && <Loader2 className="animate-spin h-4 w-4" aria-hidden="true" />}
            {isEdit ? 'Update Schedule' : 'Create Schedule'}
          </button>
        </div>
      )}
    </form>
  )
}

export default ScheduleForm