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
  DEFAULT_SCHEDULE_COLOR,
  SCHEDULE_MODES,
  TIMEZONES,
  type Schedule,
  type CreateScheduleRequest,
  type UpdateScheduleRequest,
  type RecurrenceType,
  type RecurrencePattern,
  type ScheduleMode,
} from '../types/schedule.types'
import { ColorPicker } from '@/shared/components'

// Helper to map backend recurrence type to frontend
const mapRecurrenceType = (type: string): RecurrenceType => {
  if (type === 'yearly') return 'custom'
  if (['once', 'daily', 'weekly', 'monthly', 'custom'].includes(type)) {
    return type as RecurrenceType
  }
  return 'once'
}
import { apiClient } from '@/lib/api/client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import { renderIcon } from '@/shared/utils/iconHelper'

// Validation schema
const scheduleFormSchema = z.object({
  name: z.string().min(1, 'Schedule name is required').max(255),
  description: z.string().optional(),
  playlist_id: z.number().min(1, 'Please select a playlist'),
  start_date: z.string().min(1, 'Start date is required'),
  end_date: z.string().optional(),
  start_time: z.string().min(1, 'Start time is required'),
  end_time: z.string().min(1, 'End time is required'),
  recurrence_type: z.enum(['once', 'daily', 'weekly', 'monthly', 'custom']),
  color: z.string().regex(/^#[0-9A-Fa-f]{6}$/, 'Invalid hex color'),
  mode: z.enum(['override', 'rotate']),
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

export const ScheduleForm = ({
  schedule,
  onSubmit,
  onCancel,
  isLoading = false,
  showButtons = true,
}: ScheduleFormProps) => {
  const [playlists, setPlaylists] = useState<Playlist[]>([])
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
          start_date: schedule.start_date,
          end_date: schedule.end_date,
          start_time: schedule.start_time,
          end_time: schedule.end_time,
          recurrence_type: mapRecurrenceType(schedule.recurrence_type as string),
          color: schedule.color || DEFAULT_SCHEDULE_COLOR,
          mode: schedule.mode || 'rotate',
          timezone: schedule.timezone || 'Asia/Jakarta',
        }
      : {
          name: '',
          description: '',
          playlist_id: 0,
          start_date: new Date().toISOString().split('T')[0],
          end_date: '',
          start_time: '09:00',
          end_time: '18:00',
          recurrence_type: 'once',
          color: DEFAULT_SCHEDULE_COLOR,
          mode: 'rotate',
          timezone: 'Asia/Jakarta',
        },
  })

  const recurrenceType = watch('recurrence_type')
  const startDate = watch('start_date')
  const endDate = watch('end_date')

  // Fetch playlists
  useEffect(() => {
    const fetchData = async () => {
      setLoadingData(true)
      try {
        const playlistsRes = await apiClient.get(API_ENDPOINTS.PLAYLISTS.LIST)

        // Handle both wrapped and unwrapped API responses
        const playlistData = playlistsRes.data?.data?.items || playlistsRes.data?.items || playlistsRes.data || []

        setPlaylists(Array.isArray(playlistData) ? playlistData.map((p: any) => ({
          id: p.id,
          name: p.name
        })) : [])
      } catch (error) {
        console.error('Failed to fetch playlists:', error)
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

  // Format time to HH:MM:SS if only HH:MM
  const formatTime = (time: string): string => {
    if (time && time.length === 5) {
      return `${time}:00`
    }
    return time
  }

  const handleFormSubmit = (data: ScheduleFormData) => {
    // Map 'custom' to 'yearly' for backend compatibility
    const mappedRecurrenceType = data.recurrence_type === 'custom' ? 'yearly' : data.recurrence_type

    // Build form data without timezone (backend doesn't support it yet)
    const formData = {
      name: data.name,
      description: data.description,
      playlist_id: data.playlist_id,
      start_date: data.start_date,
      end_date: data.end_date || undefined,
      start_time: formatTime(data.start_time),
      end_time: formatTime(data.end_time),
      recurrence_type: mappedRecurrenceType,
      recurrence_pattern: mappedRecurrenceType === 'once' ? undefined : recurrencePattern,
      exception_dates: exceptionDates.length > 0 ? exceptionDates : undefined,
      color: data.color,
      mode: data.mode,
      is_active: true, // Default to active
    }

    if (isEdit && schedule) {
      // For edit, only send changed fields
      const updateData: UpdateScheduleRequest = {}

      // Compare each field properly
      if (!isEqual(formData.name, schedule.name)) updateData.name = formData.name
      if (!isEqual(formData.description, schedule.description)) updateData.description = formData.description
      if (!isEqual(formData.start_date, schedule.start_date)) updateData.start_date = formData.start_date
      if (!isEqual(formData.end_date, schedule.end_date)) updateData.end_date = formData.end_date
      // Compare times after formatting
      const scheduleStartTime = formatTime(schedule.start_time)
      const scheduleEndTime = formatTime(schedule.end_time)
      if (!isEqual(formData.start_time, scheduleStartTime)) updateData.start_time = formData.start_time
      if (!isEqual(formData.end_time, scheduleEndTime)) updateData.end_time = formData.end_time
      if (!isEqual(formData.recurrence_type, schedule.recurrence_type)) {
        updateData.recurrence_type = formData.recurrence_type as RecurrenceType
      }
      if (!isEqual(formData.recurrence_pattern, schedule.recurrence_pattern)) {
        updateData.recurrence_pattern = formData.recurrence_pattern
      }
      if (!isEqual(formData.exception_dates, schedule.exception_dates)) {
        updateData.exception_dates = formData.exception_dates
      }
      // Compare color
      if (!isEqual(formData.color, schedule.color)) {
        updateData.color = formData.color
      }
      if (!isEqual(formData.mode, schedule.mode)) updateData.mode = formData.mode

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

  if (loadingData) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin h-8 w-8 border-4 border-purple-500 border-t-transparent rounded-full mx-auto mb-4"></div>
        <p className="text-gray-600">Loading playlists...</p>
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

      {/* Schedule Color */}
      <div>
        <ColorPicker
          label="Schedule Color"
          value={watch('color')}
          onChange={(newColor) => setValue('color', newColor)}
          disabled={isLoading}
          error={errors.color?.message}
        />
        <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
          Color will be displayed in calendar view to differentiate schedules
        </p>
      </div>

      {/* Schedule Mode */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          Playback Mode *
        </label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.values(SCHEDULE_MODES).map((modeInfo) => {
            const selected = watch('mode') === modeInfo.mode

            return (
              <button
                key={modeInfo.mode}
                type="button"
                onClick={() => setValue('mode', modeInfo.mode)}
                disabled={isLoading}
                className={`
                  p-4 rounded-lg border-2 transition-all text-left
                  ${
                    selected
                      ? modeInfo.mode === 'override'
                        ? 'border-red-500 bg-red-50 dark:bg-red-900/30 shadow-md'
                        : 'border-blue-500 bg-blue-50 dark:bg-blue-900/30 shadow-md'
                      : 'border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 hover:border-gray-300 dark:hover:border-gray-500'
                  }
                  ${isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                `}
              >
                <div className="flex items-start gap-3">
                  <div className={`mt-0.5 ${selected ? (modeInfo.mode === 'override' ? 'text-red-600' : 'text-blue-600') : 'text-gray-400'}`}>
                    {renderIcon(modeInfo.icon, { className: 'w-6 h-6' })}
                  </div>
                  <div className="flex-1">
                    <h4 className={`font-semibold ${selected ? 'text-gray-900 dark:text-white' : 'text-gray-700 dark:text-gray-300'}`}>
                      {modeInfo.label}
                    </h4>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {modeInfo.description}
                    </p>
                  </div>
                  {selected && (
                    <div className={`w-5 h-5 rounded-full flex items-center justify-center ${modeInfo.mode === 'override' ? 'bg-red-500' : 'bg-blue-500'}`}>
                      <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                  )}
                </div>
              </button>
            )
          })}
        </div>
        <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
          <strong>Override:</strong> Stops all other content. <strong>Rotate:</strong> Plays together with others.
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