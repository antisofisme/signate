/**
 * Translation Statistics Component
 * Display translation coverage and statistics
 */

import { Globe, Clock, CheckCircle, BarChart3, X } from 'lucide-react'
import { useTranslationStats } from '../hooks/useTranslations'
import { LANGUAGES, ENTITY_TYPES } from '../types/translation.types'

export const TranslationStats = () => {
  const { data: stats, isLoading } = useTranslationStats()

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-32 bg-gray-100 dark:bg-gray-700 rounded-lg animate-pulse" />
        ))}
      </div>
    )
  }

  if (!stats) {
    return null
  }

  return (
    <div className="space-y-6">
      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Total Translations */}
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 dark:from-blue-600 dark:to-blue-700 rounded-lg p-6 text-white">
          <div className="flex items-center justify-between mb-2">
            <Globe className="w-8 h-8" />
            <span className="text-2xl font-bold">{stats.total_translations}</span>
          </div>
          <p className="text-sm font-medium opacity-90">Total Translations</p>
        </div>

        {/* Pending */}
        <div className="bg-gradient-to-br from-yellow-500 to-yellow-600 dark:from-yellow-600 dark:to-yellow-700 rounded-lg p-6 text-white">
          <div className="flex items-center justify-between mb-2">
            <Clock className="w-8 h-8" />
            <span className="text-2xl font-bold">{stats.by_status.pending || 0}</span>
          </div>
          <p className="text-sm font-medium opacity-90">Pending Review</p>
        </div>

        {/* Approved */}
        <div className="bg-gradient-to-br from-green-500 to-green-600 dark:from-green-600 dark:to-green-700 rounded-lg p-6 text-white">
          <div className="flex items-center justify-between mb-2">
            <CheckCircle className="w-8 h-8" />
            <span className="text-2xl font-bold">{stats.by_status.approved || 0}</span>
          </div>
          <p className="text-sm font-medium opacity-90">Approved</p>
        </div>

        {/* Completion Rate */}
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 dark:from-purple-600 dark:to-purple-700 rounded-lg p-6 text-white">
          <div className="flex items-center justify-between mb-2">
            <BarChart3 className="w-8 h-8" />
            <span className="text-2xl font-bold">{stats.completion_rate}%</span>
          </div>
          <p className="text-sm font-medium opacity-90">Completion Rate</p>
        </div>
      </div>

      {/* By Language */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Translations by Language</h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {Object.entries(stats.by_language).map(([langCode, count]) => {
            const lang = LANGUAGES[langCode as keyof typeof LANGUAGES]
            if (!lang) return null

            return (
              <div
                key={langCode}
                className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600"
              >
                <span className="text-2xl">{lang.flag}</span>
                <div>
                  <p className="text-xs text-gray-600 dark:text-gray-400">{lang.name}</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">{count}</p>
                </div>
              </div>
            )
          })}
        </div>
        {Object.keys(stats.by_language).length === 0 && (
          <p className="text-center text-gray-500 dark:text-gray-400 py-4">No translations yet</p>
        )}
      </div>

      {/* By Entity Type */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Translations by Entity Type</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(stats.by_entity_type).map(([entityType, count]) => {
            const type = ENTITY_TYPES[entityType as keyof typeof ENTITY_TYPES]
            if (!type) return null

            return (
              <div
                key={entityType}
                className="flex items-center gap-3 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600"
              >
                <span className="text-3xl">{type.icon}</span>
                <div>
                  <p className="text-xs text-gray-600 dark:text-gray-400">{type.label}</p>
                  <p className="text-xl font-semibold text-gray-900 dark:text-white">{count}</p>
                </div>
              </div>
            )
          })}
        </div>
        {Object.keys(stats.by_entity_type).length === 0 && (
          <p className="text-center text-gray-500 dark:text-gray-400 py-4">No translations yet</p>
        )}
      </div>

      {/* By Status */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Translations by Status</h3>
        <div className="space-y-3">
          {/* Pending */}
          <div className="flex items-center justify-between p-3 bg-yellow-50 dark:bg-yellow-900/30 rounded-lg border border-yellow-200 dark:border-yellow-800">
            <div className="flex items-center gap-3">
              <Clock className="w-6 h-6 text-yellow-900 dark:text-yellow-300" />
              <span className="font-medium text-yellow-900 dark:text-yellow-300">Pending Review</span>
            </div>
            <span className="text-2xl font-bold text-yellow-900 dark:text-yellow-300">
              {stats.by_status.pending || 0}
            </span>
          </div>

          {/* Approved */}
          <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/30 rounded-lg border border-green-200 dark:border-green-800">
            <div className="flex items-center gap-3">
              <CheckCircle className="w-6 h-6 text-green-900 dark:text-green-300" />
              <span className="font-medium text-green-900 dark:text-green-300">Approved</span>
            </div>
            <span className="text-2xl font-bold text-green-900 dark:text-green-300">
              {stats.by_status.approved || 0}
            </span>
          </div>

          {/* Rejected */}
          <div className="flex items-center justify-between p-3 bg-red-50 dark:bg-red-900/30 rounded-lg border border-red-200 dark:border-red-800">
            <div className="flex items-center gap-3">
              <X className="w-6 h-6 text-red-900 dark:text-red-300" />
              <span className="font-medium text-red-900 dark:text-red-300">Rejected</span>
            </div>
            <span className="text-2xl font-bold text-red-900 dark:text-red-300">
              {stats.by_status.rejected || 0}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default TranslationStats
