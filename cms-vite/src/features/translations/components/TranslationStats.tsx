/**
 * Translation Statistics Component
 * Display translation coverage and statistics
 */

import { useTranslationStats } from '../hooks/useTranslations'
import { LANGUAGES, ENTITY_TYPES } from '../types/translation.types'

export const TranslationStats = () => {
  const { data: stats, isLoading } = useTranslationStats()

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-32 bg-gray-100 rounded-lg animate-pulse" />
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
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg p-6 text-white">
          <div className="flex items-center justify-between mb-2">
            <span className="text-3xl">🌐</span>
            <span className="text-2xl font-bold">{stats.total_translations}</span>
          </div>
          <p className="text-sm font-medium opacity-90">Total Translations</p>
        </div>

        {/* Pending */}
        <div className="bg-gradient-to-br from-yellow-500 to-yellow-600 rounded-lg p-6 text-white">
          <div className="flex items-center justify-between mb-2">
            <span className="text-3xl">⏳</span>
            <span className="text-2xl font-bold">{stats.by_status.pending || 0}</span>
          </div>
          <p className="text-sm font-medium opacity-90">Pending Review</p>
        </div>

        {/* Approved */}
        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg p-6 text-white">
          <div className="flex items-center justify-between mb-2">
            <span className="text-3xl">✅</span>
            <span className="text-2xl font-bold">{stats.by_status.approved || 0}</span>
          </div>
          <p className="text-sm font-medium opacity-90">Approved</p>
        </div>

        {/* Completion Rate */}
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg p-6 text-white">
          <div className="flex items-center justify-between mb-2">
            <span className="text-3xl">📊</span>
            <span className="text-2xl font-bold">{stats.completion_rate}%</span>
          </div>
          <p className="text-sm font-medium opacity-90">Completion Rate</p>
        </div>
      </div>

      {/* By Language */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Translations by Language</h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {Object.entries(stats.by_language).map(([langCode, count]) => {
            const lang = LANGUAGES[langCode as keyof typeof LANGUAGES]
            if (!lang) return null

            return (
              <div
                key={langCode}
                className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200"
              >
                <span className="text-2xl">{lang.flag}</span>
                <div>
                  <p className="text-xs text-gray-600">{lang.name}</p>
                  <p className="text-lg font-semibold text-gray-900">{count}</p>
                </div>
              </div>
            )
          })}
        </div>
        {Object.keys(stats.by_language).length === 0 && (
          <p className="text-center text-gray-500 py-4">No translations yet</p>
        )}
      </div>

      {/* By Entity Type */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Translations by Entity Type</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(stats.by_entity_type).map(([entityType, count]) => {
            const type = ENTITY_TYPES[entityType as keyof typeof ENTITY_TYPES]
            if (!type) return null

            return (
              <div
                key={entityType}
                className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg border border-gray-200"
              >
                <span className="text-3xl">{type.icon}</span>
                <div>
                  <p className="text-xs text-gray-600">{type.label}</p>
                  <p className="text-xl font-semibold text-gray-900">{count}</p>
                </div>
              </div>
            )
          })}
        </div>
        {Object.keys(stats.by_entity_type).length === 0 && (
          <p className="text-center text-gray-500 py-4">No translations yet</p>
        )}
      </div>

      {/* By Status */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Translations by Status</h3>
        <div className="space-y-3">
          {/* Pending */}
          <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg border border-yellow-200">
            <div className="flex items-center gap-3">
              <span className="text-2xl">⏳</span>
              <span className="font-medium text-yellow-900">Pending Review</span>
            </div>
            <span className="text-2xl font-bold text-yellow-900">
              {stats.by_status.pending || 0}
            </span>
          </div>

          {/* Approved */}
          <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-200">
            <div className="flex items-center gap-3">
              <span className="text-2xl">✅</span>
              <span className="font-medium text-green-900">Approved</span>
            </div>
            <span className="text-2xl font-bold text-green-900">
              {stats.by_status.approved || 0}
            </span>
          </div>

          {/* Rejected */}
          <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg border border-red-200">
            <div className="flex items-center gap-3">
              <span className="text-2xl">❌</span>
              <span className="font-medium text-red-900">Rejected</span>
            </div>
            <span className="text-2xl font-bold text-red-900">
              {stats.by_status.rejected || 0}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default TranslationStats
