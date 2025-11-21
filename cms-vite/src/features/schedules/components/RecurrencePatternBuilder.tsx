/**
 * Recurrence Pattern Builder Component
 * Visual pattern builder with presets and natural language preview
 */

import { useState, useMemo } from 'react'
import { Calendar, Clock, Repeat, Sparkles } from 'lucide-react'
import type { RecurrenceType, RecurrencePattern, DayOfWeek } from '../types/schedule.types'
import { RECURRENCE_PRESETS } from '../types/advanced'
import { DAYS_OF_WEEK } from '../types/schedule.types'

interface RecurrencePatternBuilderProps {
  recurrenceType: RecurrenceType
  pattern: RecurrencePattern
  onPatternChange: (pattern: RecurrencePattern) => void
  disabled?: boolean
  className?: string
}

export const RecurrencePatternBuilder = ({
  recurrenceType,
  pattern,
  onPatternChange,
  disabled = false,
  className = '',
}: RecurrencePatternBuilderProps) => {
  const [showPresets, setShowPresets] = useState(true)

  // Generate natural language description
  const naturalLanguagePreview = useMemo(() => {
    switch (recurrenceType) {
      case 'once':
        return 'Run once on the specified date'

      case 'daily':
        if (pattern.interval === 1) {
          return 'Run every day'
        }
        return `Run every ${pattern.interval} days`

      case 'weekly':
        if (!pattern.days_of_week || pattern.days_of_week.length === 0) {
          return 'Select days of the week'
        }
        const dayNames = pattern.days_of_week
          .map((day) => DAYS_OF_WEEK[day].label)
          .join(', ')
        return `Run every ${dayNames}`

      case 'monthly':
        if (pattern.last_day_of_month) {
          return 'Run on the last day of each month'
        }
        if (pattern.day_of_month) {
          const suffix = getOrdinalSuffix(pattern.day_of_month)
          return `Run on the ${pattern.day_of_month}${suffix} day of each month`
        }
        return 'Select day of month'

      case 'custom':
        if (pattern.cron_expression) {
          return `Custom pattern: ${pattern.cron_expression}`
        }
        return 'Enter cron expression'

      default:
        return ''
    }
  }, [recurrenceType, pattern])

  // Apply preset
  const applyPreset = (presetId: string) => {
    const preset = RECURRENCE_PRESETS.find((p) => p.id === presetId)
    if (preset) {
      onPatternChange(preset.pattern)
    }
  }

  // Handle pattern changes
  const updatePattern = (updates: Partial<RecurrencePattern>) => {
    onPatternChange({ ...pattern, ...updates })
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Repeat className="h-5 w-5 text-purple-600 dark:text-purple-400" />
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
            Recurrence Pattern
          </h3>
        </div>
        {recurrenceType !== 'once' && (
          <button
            type="button"
            onClick={() => setShowPresets(!showPresets)}
            className="text-xs text-purple-600 dark:text-purple-400 hover:underline"
          >
            {showPresets ? 'Hide' : 'Show'} Presets
          </button>
        )}
      </div>

      {/* Natural Language Preview */}
      <div className="p-3 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-md">
        <div className="flex items-start gap-2">
          <Sparkles className="h-4 w-4 text-purple-600 dark:text-purple-400 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-purple-900 dark:text-purple-200">
            {naturalLanguagePreview}
          </p>
        </div>
      </div>

      {/* Presets */}
      {showPresets && recurrenceType !== 'once' && (
        <div className="space-y-2">
          <label className="text-xs font-medium text-gray-700 dark:text-gray-300">
            Quick Presets
          </label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {RECURRENCE_PRESETS.filter((p) => p.type === recurrenceType).map((preset) => (
              <button
                key={preset.id}
                type="button"
                onClick={() => applyPreset(preset.id)}
                disabled={disabled}
                className="p-3 text-left border border-gray-200 dark:border-gray-700 rounded-md hover:bg-purple-50 dark:hover:bg-purple-900/20 hover:border-purple-300 dark:hover:border-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <div className="text-xs font-medium text-gray-900 dark:text-white">
                  {preset.label}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  {preset.description}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Pattern Builder Based on Type */}
      {recurrenceType === 'daily' && <DailyPatternBuilder pattern={pattern} onChange={updatePattern} disabled={disabled} />}
      {recurrenceType === 'weekly' && <WeeklyPatternBuilder pattern={pattern} onChange={updatePattern} disabled={disabled} />}
      {recurrenceType === 'monthly' && <MonthlyPatternBuilder pattern={pattern} onChange={updatePattern} disabled={disabled} />}
      {recurrenceType === 'custom' && <CustomPatternBuilder pattern={pattern} onChange={updatePattern} disabled={disabled} />}
    </div>
  )
}

// ========================================
// Daily Pattern Builder
// ========================================

const DailyPatternBuilder = ({
  pattern,
  onChange,
  disabled,
}: {
  pattern: RecurrencePattern
  onChange: (updates: Partial<RecurrencePattern>) => void
  disabled: boolean
}) => {
  return (
    <div className="space-y-2">
      <label className="text-xs font-medium text-gray-700 dark:text-gray-300">
        Repeat every N days
      </label>
      <input
        type="number"
        min="1"
        max="365"
        value={pattern.interval || 1}
        onChange={(e) => onChange({ interval: parseInt(e.target.value) || 1 })}
        disabled={disabled}
        className="w-32 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white disabled:opacity-50"
      />
      <p className="text-xs text-gray-500 dark:text-gray-400">
        Enter 1 for every day, 2 for every other day, etc.
      </p>
    </div>
  )
}

// ========================================
// Weekly Pattern Builder
// ========================================

const WeeklyPatternBuilder = ({
  pattern,
  onChange,
  disabled,
}: {
  pattern: RecurrencePattern
  onChange: (updates: Partial<RecurrencePattern>) => void
  disabled: boolean
}) => {
  const selectedDays = pattern.days_of_week || []

  const toggleDay = (day: DayOfWeek) => {
    const newDays = selectedDays.includes(day)
      ? selectedDays.filter((d) => d !== day)
      : [...selectedDays, day]
    onChange({ days_of_week: newDays })
  }

  const orderedDays: DayOfWeek[] = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

  return (
    <div className="space-y-2">
      <label className="text-xs font-medium text-gray-700 dark:text-gray-300">
        Select days of the week
      </label>
      <div className="grid grid-cols-7 gap-1">
        {orderedDays.map((day) => {
          const isSelected = selectedDays.includes(day)
          const dayInfo = DAYS_OF_WEEK[day]

          return (
            <button
              key={day}
              type="button"
              onClick={() => toggleDay(day)}
              disabled={disabled}
              className={`
                p-2 rounded-md text-xs font-medium transition-all
                ${
                  isSelected
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }
                ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
            >
              <div className="text-center">
                <div className="font-bold">{dayInfo.short}</div>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}

// ========================================
// Monthly Pattern Builder
// ========================================

const MonthlyPatternBuilder = ({
  pattern,
  onChange,
  disabled,
}: {
  pattern: RecurrencePattern
  onChange: (updates: Partial<RecurrencePattern>) => void
  disabled: boolean
}) => {
  const [mode, setMode] = useState<'day' | 'last'>(
    pattern.last_day_of_month ? 'last' : 'day'
  )

  const handleModeChange = (newMode: 'day' | 'last') => {
    setMode(newMode)
    if (newMode === 'last') {
      onChange({ last_day_of_month: true, day_of_month: undefined })
    } else {
      onChange({ last_day_of_month: false, day_of_month: 1 })
    }
  }

  return (
    <div className="space-y-3">
      <label className="text-xs font-medium text-gray-700 dark:text-gray-300">
        Day of month
      </label>

      {/* Mode Selection */}
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => handleModeChange('day')}
          disabled={disabled}
          className={`
            flex-1 px-3 py-2 rounded-md text-sm font-medium transition-all
            ${
              mode === 'day'
                ? 'bg-purple-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }
            ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          `}
        >
          Specific Day
        </button>
        <button
          type="button"
          onClick={() => handleModeChange('last')}
          disabled={disabled}
          className={`
            flex-1 px-3 py-2 rounded-md text-sm font-medium transition-all
            ${
              mode === 'last'
                ? 'bg-purple-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }
            ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          `}
        >
          Last Day
        </button>
      </div>

      {/* Day Selector */}
      {mode === 'day' && (
        <div className="space-y-2">
          <input
            type="number"
            min="1"
            max="31"
            value={pattern.day_of_month || 1}
            onChange={(e) => onChange({ day_of_month: parseInt(e.target.value) || 1 })}
            disabled={disabled}
            className="w-32 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white disabled:opacity-50"
          />
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Day 1-31 (Note: Day 29-31 may not exist in all months)
          </p>
        </div>
      )}

      {mode === 'last' && (
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Schedule will run on the last day of each month
        </p>
      )}
    </div>
  )
}

// ========================================
// Custom Pattern Builder
// ========================================

const CustomPatternBuilder = ({
  pattern,
  onChange,
  disabled,
}: {
  pattern: RecurrencePattern
  onChange: (updates: Partial<RecurrencePattern>) => void
  disabled: boolean
}) => {
  return (
    <div className="space-y-2">
      <label className="text-xs font-medium text-gray-700 dark:text-gray-300">
        Cron Expression
      </label>
      <input
        type="text"
        value={pattern.cron_expression || ''}
        onChange={(e) => onChange({ cron_expression: e.target.value })}
        disabled={disabled}
        placeholder="0 0 * * *"
        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white disabled:opacity-50 font-mono text-sm"
      />
      <p className="text-xs text-gray-500 dark:text-gray-400">
        Format: minute hour day month weekday (e.g., "0 9 * * 1-5" = 9 AM on weekdays)
      </p>
      <a
        href="https://crontab.guru/"
        target="_blank"
        rel="noopener noreferrer"
        className="text-xs text-purple-600 dark:text-purple-400 hover:underline"
      >
        Learn more about cron expressions
      </a>
    </div>
  )
}

// ========================================
// Helper Functions
// ========================================

function getOrdinalSuffix(day: number): string {
  if (day >= 11 && day <= 13) return 'th'
  switch (day % 10) {
    case 1:
      return 'st'
    case 2:
      return 'nd'
    case 3:
      return 'rd'
    default:
      return 'th'
  }
}

export default RecurrencePatternBuilder
