/**
 * Schedule Form Component
 * Create/Edit schedule with all configurations
 */

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useState, useEffect } from 'react'
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
import axios from 'axios'

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
          axios.get('/api/v1/playlists'),
          axios.get('/api/v1/devices'),
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

  const handleFormSubmit = (data: ScheduleFormData) => {
    const formData = {
      ...data,
      recurrence_pattern: recurrenceType === 'once' ? undefined : recurrencePattern,
      exception_dates: exceptionDates.length > 0 ? exceptionDates : undefined,
    }

    if (isEdit) {
      // For edit, only send changed fields
      const updateData: UpdateScheduleRequest = {}
      
      Object.keys(formData).forEach((key) => {
        const k = key as keyof ScheduleFormData
        if (formData[k] !== schedule[k as keyof Schedule]) {
          (updateData as any)[k] = formData[k]
        }
      })

      onSubmit(updateData)
    } else {
      onSubmit(formData as CreateScheduleRequest)
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
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
      {/* Basic Information */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Basic Information</h3>
        
        {/* Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Schedule Name *
          </label>
          <input
            {...register('name')}
            type="text"
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            placeholder="e.g., Morning Playlist Schedule"
            disabled={isLoading}
          />
          {errors.name && (
            <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
          )}
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Description
          </label>
          <textarea
            {...register('description')}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            placeholder="Optional description..."
            disabled={isLoading}
          />
        </div>
      </div>

      {/* Playlist Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Playlist *
        </label>
        <select
          {...register('playlist_id', { valueAsNumber: true })}
          disabled={isLoading || isEdit}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
        >
          <option value="">-- Select Playlist --</option>
          {playlists.map((playlist) => (
            <option key={playlist.id} value={playlist.id}>
              {playlist.name}
            </option>
          ))}
        </select>
        {errors.playlist_id && (
          <p className="mt-1 text-sm text-red-600">{errors.playlist_id.message}</p>
        )}
      </div>

      {/* Device Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          Devices * ({selectedDevices.length} selected)
        </label>
        <div className="max-h-40 overflow-y-auto border border-gray-300 dark:border-gray-600 rounded-md p-3 bg-white dark:bg-gray-800">
          <div className="space-y-2">
            {devices.map((device) => (
              <label key={device.id} className="flex items-center gap-3">
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
                  className="w-4 h-4"
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
          <p className="mt-1 text-sm text-red-600">{errors.device_ids.message}</p>
        )}
      </div>

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
                  <span className="text-2xl">{priority.icon}</span>
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

      {/* Action Buttons */}
      <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
        <button
          type="button"
          onClick={onCancel}
          disabled={isLoading}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isLoading}
          className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2"
        >
          {isLoading && (
            <svg
              className="animate-spin h-4 w-4"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          )}
          {isEdit ? 'Update Schedule' : 'Create Schedule'}
        </button>
      </div>
    </form>
  )
}

export default ScheduleForm