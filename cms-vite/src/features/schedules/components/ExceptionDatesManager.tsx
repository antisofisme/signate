/**
 * Exception Dates Manager Component
 * Manage exception dates for recurring schedules
 */

import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Calendar, X, Plus, AlertCircle } from 'lucide-react'

interface ExceptionDatesManagerProps {
  exceptionDates: string[]
  onChange: (dates: string[]) => void
  disabled?: boolean
  minDate?: string
  maxDate?: string
}

export function ExceptionDatesManager({
  exceptionDates,
  onChange,
  disabled = false,
  minDate,
  maxDate,
}: ExceptionDatesManagerProps) {
  const { t } = useTranslation()
  const [newDate, setNewDate] = useState('')
  const [error, setError] = useState('')

  const handleAddDate = () => {
    setError('')

    if (!newDate) {
      setError(t('schedules.exceptionDates.pleaseSelectDate'))
      return
    }

    // Validate min/max date
    if (minDate && newDate < minDate) {
      setError(t('schedules.exceptionDates.dateAfter', { date: formatDate(minDate) }))
      return
    }

    if (maxDate && newDate > maxDate) {
      setError(t('schedules.exceptionDates.dateBefore', { date: formatDate(maxDate) }))
      return
    }

    // Check for duplicate
    if (exceptionDates.includes(newDate)) {
      setError(t('schedules.exceptionDates.alreadyInList'))
      return
    }

    // Add date and sort
    const updatedDates = [...exceptionDates, newDate].sort()
    onChange(updatedDates)
    setNewDate('')
  }

  const handleRemoveDate = (dateToRemove: string) => {
    const updatedDates = exceptionDates.filter(date => date !== dateToRemove)
    onChange(updatedDates)
  }

  const handleClearAll = () => {
    if (confirm(t('schedules.exceptionDates.confirmClearAll'))) {
      onChange([])
    }
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-sm font-medium text-gray-900 dark:text-white flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            {t('schedules.exceptionDates.title')}
          </h4>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {t('schedules.exceptionDates.description')}
          </p>
        </div>
        {exceptionDates.length > 0 && (
          <button
            type="button"
            onClick={handleClearAll}
            disabled={disabled}
            className="text-xs text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {t('schedules.exceptionDates.clearAll')}
          </button>
        )}
      </div>

      {/* Add Date Form */}
      <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 space-y-3">
        <div className="flex gap-2">
          <div className="flex-1">
            <input
              type="date"
              value={newDate}
              onChange={(e) => {
                setNewDate(e.target.value)
                setError('')
              }}
              min={minDate}
              max={maxDate}
              disabled={disabled}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
            />
          </div>
          <button
            type="button"
            onClick={handleAddDate}
            disabled={disabled || !newDate}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 text-sm"
          >
            <Plus className="w-4 h-4" />
            {t('schedules.exceptionDates.add')}
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="flex items-start gap-2 text-xs text-red-600 dark:text-red-400">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Exception Dates List */}
      {exceptionDates.length > 0 ? (
        <div className="space-y-2">
          <div className="text-xs font-medium text-gray-700 dark:text-gray-300">
            {t(
              exceptionDates.length !== 1
                ? 'schedules.exceptionDates.countDates_plural'
                : 'schedules.exceptionDates.countDates',
              { count: exceptionDates.length }
            )}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {exceptionDates.map((date) => (
              <div
                key={date}
                className="flex items-center justify-between bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-2.5 group hover:border-red-300 dark:hover:border-red-700 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {formatDate(date)}
                  </span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    ({getDayName(date)})
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => handleRemoveDate(date)}
                  disabled={disabled}
                  className="opacity-0 group-hover:opacity-100 p-1 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30 rounded transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  title={t('schedules.exceptionDates.removeDate')}
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="text-center py-6 bg-gray-50 dark:bg-gray-900 rounded-lg border-2 border-dashed border-gray-200 dark:border-gray-700">
          <Calendar className="w-8 h-8 text-gray-400 dark:text-gray-500 mx-auto mb-2" />
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {t('schedules.exceptionDates.noExceptionDates')}
          </p>
          <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
            {t('schedules.exceptionDates.addDatesDesc')}
          </p>
        </div>
      )}

      {/* Helper Info */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
        <div className="flex gap-2">
          <AlertCircle className="w-4 h-4 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="text-xs text-blue-800 dark:text-blue-300">
            <strong>{t('schedules.exceptionDates.tip')}</strong> {t('schedules.exceptionDates.tipDescription')}
          </div>
        </div>
      </div>
    </div>
  )
}

// Helper functions
function formatDate(dateString: string): string {
  const date = new Date(dateString + 'T00:00:00')
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

function getDayName(dateString: string): string {
  const date = new Date(dateString + 'T00:00:00')
  return date.toLocaleDateString('en-US', { weekday: 'short' })
}

export default ExceptionDatesManager
