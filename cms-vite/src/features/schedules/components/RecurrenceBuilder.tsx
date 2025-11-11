/**
 * Recurrence Builder Component
 * Visual builder for schedule recurrence patterns
 */

import { RECURRENCE_TYPES, DAYS_OF_WEEK, type RecurrenceType, type RecurrencePattern, type DayOfWeek } from '../types/schedule.types'

interface RecurrenceBuilderProps {
  recurrenceType: RecurrenceType
  recurrencePattern?: RecurrencePattern
  onTypeChange: (type: RecurrenceType) => void
  onPatternChange: (pattern: RecurrencePattern) => void
  disabled?: boolean
}

export const RecurrenceBuilder = ({
  recurrenceType,
  recurrencePattern = {},
  onTypeChange,
  onPatternChange,
  disabled = false,
}: RecurrenceBuilderProps) => {
  const handleTypeClick = (type: RecurrenceType) => {
    if (disabled) return
    onTypeChange(type)
    
    // Reset pattern when changing type
    if (type === 'once') {
      onPatternChange({})
    } else if (type === 'daily') {
      onPatternChange({ interval: 1 })
    } else if (type === 'weekly') {
      onPatternChange({ days_of_week: ['monday'] })
    } else if (type === 'monthly') {
      onPatternChange({ day_of_month: 1 })
    } else if (type === 'custom') {
      onPatternChange({ cron_expression: '0 9 * * *' })
    }
  }

  const handleDayToggle = (day: DayOfWeek) => {
    if (disabled || recurrenceType !== 'weekly') return

    const currentDays = recurrencePattern.days_of_week || []
    const newDays = currentDays.includes(day)
      ? currentDays.filter(d => d !== day)
      : [...currentDays, day]
    
    // Ensure at least one day is selected
    if (newDays.length === 0) return

    onPatternChange({
      ...recurrencePattern,
      days_of_week: newDays,
    })
  }

  return (
    <div className="space-y-4">
      {/* Recurrence Type Selector */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Recurrence Type
        </label>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {Object.values(RECURRENCE_TYPES).map((type) => {
            const selected = recurrenceType === type.type

            return (
              <button
                key={type.type}
                type="button"
                onClick={() => handleTypeClick(type.type)}
                disabled={disabled}
                className={`
                  p-3 rounded-lg border-2 transition-all
                  ${
                    selected
                      ? 'border-purple-500 bg-purple-50 shadow-md'
                      : 'border-gray-200 bg-white hover:border-purple-300 hover:bg-purple-50'
                  }
                  ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                `}
              >
                <div className="flex flex-col items-center gap-1">
                  <span className="text-2xl">{type.icon}</span>
                  <span className="text-xs font-semibold text-gray-900">
                    {type.label}
                  </span>
                </div>
              </button>
            )
          })}
        </div>
        <p className="mt-2 text-xs text-gray-500">
          {RECURRENCE_TYPES[recurrenceType].description}
        </p>
      </div>

      {/* Pattern Configuration */}
      {recurrenceType !== 'once' && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          {/* Daily Pattern */}
          {recurrenceType === 'daily' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Repeat every
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  min="1"
                  max="365"
                  value={recurrencePattern.interval || 1}
                  onChange={(e) => onPatternChange({
                    ...recurrencePattern,
                    interval: parseInt(e.target.value) || 1,
                  })}
                  disabled={disabled}
                  className="w-20 px-3 py-2 border border-gray-300 rounded-md"
                />
                <span className="text-sm text-gray-700">
                  {(recurrencePattern.interval || 1) === 1 ? 'day' : 'days'}
                </span>
              </div>
            </div>
          )}

          {/* Weekly Pattern */}
          {recurrenceType === 'weekly' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Repeat on days
              </label>
              <div className="grid grid-cols-7 gap-2">
                {Object.entries(DAYS_OF_WEEK).map(([key, day]) => {
                  const selected = recurrencePattern.days_of_week?.includes(key as DayOfWeek)
                  
                  return (
                    <button
                      key={key}
                      type="button"
                      onClick={() => handleDayToggle(key as DayOfWeek)}
                      disabled={disabled}
                      className={`
                        p-2 text-xs font-medium rounded transition-all
                        ${
                          selected
                            ? 'bg-purple-500 text-white'
                            : 'bg-white border border-gray-300 text-gray-700 hover:bg-purple-100'
                        }
                        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                      `}
                    >
                      {day.short}
                    </button>
                  )
                })}
              </div>
              {recurrencePattern.days_of_week && recurrencePattern.days_of_week.length > 0 && (
                <p className="mt-2 text-xs text-gray-600">
                  Repeats on: {recurrencePattern.days_of_week
                    .map(d => DAYS_OF_WEEK[d].label)
                    .join(', ')}
                </p>
              )}
            </div>
          )}

          {/* Monthly Pattern */}
          {recurrenceType === 'monthly' && (
            <div className="space-y-3">
              <label className="block text-sm font-medium text-gray-700">
                Repeat on
              </label>
              
              <div className="space-y-2">
                <label className="flex items-center gap-3">
                  <input
                    type="radio"
                    checked={!recurrencePattern.last_day_of_month}
                    onChange={() => onPatternChange({
                      day_of_month: recurrencePattern.day_of_month || 1,
                      last_day_of_month: false,
                    })}
                    disabled={disabled}
                    className="w-4 h-4"
                  />
                  <span className="text-sm text-gray-700">Day</span>
                  <input
                    type="number"
                    min="1"
                    max="31"
                    value={recurrencePattern.day_of_month || 1}
                    onChange={(e) => onPatternChange({
                      day_of_month: parseInt(e.target.value) || 1,
                      last_day_of_month: false,
                    })}
                    disabled={disabled || recurrencePattern.last_day_of_month}
                    className="w-16 px-2 py-1 border border-gray-300 rounded-md"
                  />
                  <span className="text-sm text-gray-700">of the month</span>
                </label>

                <label className="flex items-center gap-3">
                  <input
                    type="radio"
                    checked={!!recurrencePattern.last_day_of_month}
                    onChange={() => onPatternChange({
                      last_day_of_month: true,
                    })}
                    disabled={disabled}
                    className="w-4 h-4"
                  />
                  <span className="text-sm text-gray-700">Last day of the month</span>
                </label>
              </div>
            </div>
          )}

          {/* Custom Pattern */}
          {recurrenceType === 'custom' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Cron Expression
              </label>
              <input
                type="text"
                value={recurrencePattern.cron_expression || ''}
                onChange={(e) => onPatternChange({
                  ...recurrencePattern,
                  cron_expression: e.target.value,
                })}
                placeholder="0 9 * * *"
                disabled={disabled}
                className="w-full px-3 py-2 border border-gray-300 rounded-md font-mono text-sm"
              />
              <div className="mt-2 text-xs text-gray-600 space-y-1">
                <p>Format: minute hour day month weekday</p>
                <p>Examples:</p>
                <ul className="list-disc list-inside ml-2">
                  <li><code className="bg-gray-200 px-1">0 9 * * *</code> - Every day at 9:00 AM</li>
                  <li><code className="bg-gray-200 px-1">0 */2 * * *</code> - Every 2 hours</li>
                  <li><code className="bg-gray-200 px-1">0 9 * * 1-5</code> - Weekdays at 9:00 AM</li>
                </ul>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Recurrence Summary */}
      {recurrenceType !== 'once' && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <p className="text-sm text-blue-900">
            <span className="font-medium">Schedule will repeat:</span>{' '}
            {getRecurrenceSummary(recurrenceType, recurrencePattern)}
          </p>
        </div>
      )}
    </div>
  )
}

// Helper function to generate human-readable summary
function getRecurrenceSummary(type: RecurrenceType, pattern: RecurrencePattern): string {
  switch (type) {
    case 'daily':
      const interval = pattern.interval || 1
      return interval === 1 ? 'Every day' : `Every ${interval} days`
    
    case 'weekly':
      const days = pattern.days_of_week || []
      if (days.length === 0) return 'No days selected'
      if (days.length === 7) return 'Every day of the week'
      return `Every ${days.map(d => DAYS_OF_WEEK[d].label).join(', ')}`
    
    case 'monthly':
      if (pattern.last_day_of_month) return 'Last day of every month'
      return `Day ${pattern.day_of_month || 1} of every month`
    
    case 'custom':
      return pattern.cron_expression || 'No expression defined'
    
    default:
      return 'One time only'
  }
}

export default RecurrenceBuilder