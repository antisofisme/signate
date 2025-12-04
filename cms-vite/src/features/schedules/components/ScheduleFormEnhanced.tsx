/**
 * Enhanced Schedule Form Component
 * Complete schedule form with real-time validation, conflict detection, and preview
 */

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useState, useEffect } from 'react'
import { CheckCircle, XCircle, AlertTriangle, Eye, Loader2 } from 'lucide-react'
import ScheduleConflictDetector from './ScheduleConflictDetector'
import SchedulePreviewCalendar from './SchedulePreviewCalendar'
import RecurrencePatternBuilder from './RecurrencePatternBuilder'
import ExceptionDatesManager from './ExceptionDatesManager'
import { useCombinedScheduleState, useSchedulePreview } from '../hooks/useAdvancedSchedules'
import { TIMEZONES, DEFAULT_SCHEDULE_COLOR } from '../types/schedule.types'
import { ColorPicker } from '@/shared/components'
import type {
  Schedule,
  CreateScheduleRequest,
  UpdateScheduleRequest,
  RecurrenceType,
  RecurrencePattern,
} from '../types/schedule.types'
import axios from 'axios'

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
  color: z.string().regex(/^#[0-9A-Fa-f]{6}$/, 'Invalid color format'),
  timezone: z.string().min(1, 'Timezone is required'),
})

type ScheduleFormData = z.infer<typeof scheduleFormSchema>

interface ScheduleFormEnhancedProps {
  schedule?: Schedule
  onSubmit: (data: CreateScheduleRequest | UpdateScheduleRequest) => void
  onCancel: () => void
  isLoading?: boolean
}

interface Playlist {
  id: number
  name: string
}

export const ScheduleFormEnhanced = ({
  schedule,
  onSubmit,
  onCancel,
  isLoading = false,
}: ScheduleFormEnhancedProps) => {
  const [playlists, setPlaylists] = useState<Playlist[]>([])
  const [loadingData, setLoadingData] = useState(true)
  const [recurrencePattern, setRecurrencePattern] = useState<RecurrencePattern>(
    schedule?.recurrence_pattern || {}
  )
  const [exceptionDates, setExceptionDates] = useState<string[]>(
    schedule?.exception_dates || []
  )
  const [showPreview, setShowPreview] = useState(false)

  const isEdit = !!schedule

  // Map backend recurrence type to frontend
  const mapRecurrenceType = (type: string): RecurrenceType => {
    if (type === 'yearly') return 'custom'
    if (['once', 'daily', 'weekly', 'monthly', 'custom'].includes(type)) {
      return type as RecurrenceType
    }
    return 'once'
  }

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
          timezone: 'Asia/Jakarta',
        },
  })

  const formValues = watch()
  const recurrenceType = watch('recurrence_type')
  const color = watch('color')

  // Fetch playlists
  useEffect(() => {
    const fetchData = async () => {
      setLoadingData(true)
      try {
        const playlistsRes = await axios.get('/api/v1/playlists')
        setPlaylists(playlistsRes.data.playlists || [])
      } catch (error) {
        console.error('Failed to fetch playlists:', error)
      } finally {
        setLoadingData(false)
      }
    }
    fetchData()
  }, [])

  // Use combined state hook for validation and conflicts
  const combinedState = useCombinedScheduleState(
    {
      playlist_id: formValues.playlist_id,
      start_date: formValues.start_date,
      end_date: formValues.end_date || null,
      start_time: formValues.start_time || null,
      end_time: formValues.end_time || null,
      recurrence_type: formValues.recurrence_type,
      exclude_schedule_id: schedule?.id || null,
    },
    {
      start_date: formValues.start_date,
      end_date: formValues.end_date || null,
      start_time: formValues.start_time || null,
      end_time: formValues.end_time || null,
      recurrence_type: formValues.recurrence_type,
      recurrence_pattern: recurrencePattern,
    },
    schedule?.id
  )

  // Generate preview occurrences
  const previewOccurrences = useSchedulePreview(combinedState.occurrences, color)

  // Form submission
  const handleFormSubmit = (data: ScheduleFormData) => {
    const formData = {
      ...data,
      color: data.color,
      recurrence_pattern: recurrenceType === 'once' ? undefined : recurrencePattern,
      exception_dates: exceptionDates.length > 0 ? exceptionDates : undefined,
    } as any

    if (isEdit) {
      const updateData: UpdateScheduleRequest = {}
      Object.keys(formData).forEach((key) => {
        const k = key as keyof ScheduleFormData
        if (formData[k] !== (schedule as any)[k]) {
          (updateData as any)[k] = formData[k]
        }
      })
      onSubmit(updateData)
    } else {
      onSubmit(formData as CreateScheduleRequest)
    }
  }

  // Field validation indicators
  const getFieldStatus = (fieldName: keyof ScheduleFormData) => {
    if (errors[fieldName]) {
      return { icon: XCircle, color: 'text-red-500', message: errors[fieldName]?.message }
    }
    if (formValues[fieldName]) {
      return { icon: CheckCircle, color: 'text-green-500' }
    }
    return null
  }

  if (loadingData) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin h-8 w-8 border-4 border-purple-500 border-t-transparent rounded-full mx-auto mb-4"></div>
        <p className="text-gray-600 dark:text-gray-400">Loading form data...</p>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
      {/* Validation Summary */}
      {combinedState.hasErrors && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <div className="flex items-start gap-2">
            <XCircle className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-semibold text-red-900 dark:text-red-200">
                Validation Errors
              </h4>
              <ul className="mt-1 text-sm text-red-800 dark:text-red-300 list-disc list-inside">
                {combinedState.validation.errors.map((error, idx) => (
                  <li key={idx}>{error}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {combinedState.hasWarnings && !combinedState.hasErrors && (
        <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
          <div className="flex items-start gap-2">
            <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-semibold text-yellow-900 dark:text-yellow-200">
                Warnings
              </h4>
              <ul className="mt-1 text-sm text-yellow-800 dark:text-yellow-300 list-disc list-inside">
                {combinedState.validation.warnings.map((warning, idx) => (
                  <li key={idx}>{warning}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Basic Information */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Basic Information</h3>

        <FieldWithValidation
          label="Schedule Name"
          error={errors.name?.message}
          required
        >
          <input
            {...register('name')}
            type="text"
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            placeholder="e.g., Morning Playlist Schedule"
            disabled={isLoading}
          />
        </FieldWithValidation>

        <FieldWithValidation label="Description">
          <textarea
            {...register('description')}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            placeholder="Optional description..."
            disabled={isLoading}
          />
        </FieldWithValidation>
      </div>

      {/* Playlist & Devices */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <FieldWithValidation
          label="Playlist"
          error={errors.playlist_id?.message}
          required
        >
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
        </FieldWithValidation>
      </div>

      {/* Date & Time */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <FieldWithValidation
          label="Start Date"
          error={errors.start_date?.message}
          required
        >
          <input
            {...register('start_date')}
            type="date"
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            disabled={isLoading}
          />
        </FieldWithValidation>

        <FieldWithValidation label="End Date">
          <input
            {...register('end_date')}
            type="date"
            min={formValues.start_date}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            disabled={isLoading}
          />
        </FieldWithValidation>

        <FieldWithValidation
          label="Start Time"
          error={errors.start_time?.message}
          required
        >
          <input
            {...register('start_time')}
            type="time"
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            disabled={isLoading}
          />
        </FieldWithValidation>

        <FieldWithValidation
          label="End Time"
          error={errors.end_time?.message}
          required
        >
          <input
            {...register('end_time')}
            type="time"
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            disabled={isLoading}
          />
        </FieldWithValidation>
      </div>

      {/* Timezone */}
      <FieldWithValidation
        label="Timezone"
        error={errors.timezone?.message}
        required
      >
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
      </FieldWithValidation>

      {/* Recurrence Type */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Recurrence Type
        </label>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
          {(['once', 'daily', 'weekly', 'monthly', 'custom'] as RecurrenceType[]).map((type) => (
            <button
              key={type}
              type="button"
              onClick={() => setValue('recurrence_type', type)}
              disabled={isLoading}
              className={`
                p-3 rounded-md border-2 transition-all text-sm font-medium capitalize
                ${
                  recurrenceType === type
                    ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20 text-purple-900 dark:text-purple-200'
                    : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:border-purple-300 dark:hover:border-purple-700'
                }
              `}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Recurrence Pattern Builder */}
      <RecurrencePatternBuilder
        recurrenceType={recurrenceType}
        pattern={recurrencePattern}
        onPatternChange={setRecurrencePattern}
        disabled={isLoading}
      />

      {/* Exception Dates */}
      {recurrenceType !== 'once' && (
        <ExceptionDatesManager
          exceptionDates={exceptionDates}
          onChange={setExceptionDates}
          minDate={formValues.start_date}
          maxDate={formValues.end_date}
          disabled={isLoading}
        />
      )}

      {/* Schedule Color */}
      <div>
        <ColorPicker
          label="Schedule Color"
          value={color}
          onChange={(newColor) => setValue('color', newColor)}
          disabled={isLoading}
          error={errors.color?.message}
        />
        <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
          Color will be displayed in calendar view to differentiate schedules
        </p>
      </div>

      {/* Conflict Detector */}
      <ScheduleConflictDetector
        playlistId={formValues.playlist_id}
        startDate={formValues.start_date}
        endDate={formValues.end_date}
        startTime={formValues.start_time}
        endTime={formValues.end_time}
        recurrenceType={formValues.recurrence_type}
        recurrencePattern={recurrencePattern}
        excludeScheduleId={schedule?.id}
      />

      {/* Preview Toggle */}
      <button
        type="button"
        onClick={() => setShowPreview(!showPreview)}
        className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md transition-colors"
      >
        <Eye className="h-4 w-4" />
        {showPreview ? 'Hide' : 'Show'} Calendar Preview
      </button>

      {/* Preview Calendar */}
      {showPreview && previewOccurrences.length > 0 && (
        <SchedulePreviewCalendar
          occurrences={previewOccurrences}
          playlistName={playlists.find((p) => p.id === formValues.playlist_id)?.name}
          color={color}
          exceptionDates={exceptionDates}
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
          disabled={isLoading || combinedState.hasErrors}
          className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2"
        >
          {isLoading && <Loader2 className="animate-spin h-4 w-4" />}
          {isEdit ? 'Update Schedule' : 'Create Schedule'}
        </button>
      </div>
    </form>
  )
}

// ========================================
// Field with Validation Component
// ========================================

interface FieldWithValidationProps {
  label: string
  error?: string
  required?: boolean
  children: React.ReactNode
}

const FieldWithValidation = ({ label, error, required, children }: FieldWithValidationProps) => {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
        {label} {required && <span className="text-red-500">*</span>}
      </label>
      {children}
      {error && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{error}</p>}
    </div>
  )
}

export default ScheduleFormEnhanced
