/**
 * Translation List Component
 * Display translations with filters and actions
 */

import { useState } from 'react'
import { CheckCircle, XCircle } from 'lucide-react'
import {
  LANGUAGES,
  ENTITY_TYPES,
  type Translation,
  type EntityType,
  type Language,
  type TranslationStatus,
} from '../types/translation.types'
import { formatDateTime } from '@/shared/utils/formatters'

interface TranslationListProps {
  translations: Translation[]
  isLoading?: boolean
  onEdit: (translation: Translation) => void
  onDelete: (translation: Translation) => void
  onApprove: (translation: Translation) => void
  onReject: (translation: Translation) => void
}

export const TranslationList = ({
  translations,
  isLoading,
  onEdit,
  onDelete,
  onApprove,
  onReject,
}: TranslationListProps) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [filterLanguage, setFilterLanguage] = useState<Language | 'all'>('all')
  const [filterEntityType, setFilterEntityType] = useState<EntityType | 'all'>('all')
  const [filterStatus, setFilterStatus] = useState<TranslationStatus | 'all'>('all')

  // Filter translations
  const filteredTranslations = translations.filter((translation) => {
    const matchesSearch = translation.translated_text
      .toLowerCase()
      .includes(searchQuery.toLowerCase())

    const matchesLanguage =
      filterLanguage === 'all' || translation.language === filterLanguage

    const matchesEntityType =
      filterEntityType === 'all' || translation.entity_type === filterEntityType

    const matchesStatus = filterStatus === 'all' || translation.status === filterStatus

    return matchesSearch && matchesLanguage && matchesEntityType && matchesStatus
  })

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-24 bg-gray-100 rounded-lg animate-pulse" />
        ))}
      </div>
    )
  }

  if (translations.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <div className="text-4xl mb-4">🌐</div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">No translations yet</h3>
        <p className="text-gray-600 mb-4">Create your first translation to get started</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-3">
        {/* Search */}
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search translations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg"
          />
        </div>

        {/* Language filter */}
        <select
          value={filterLanguage}
          onChange={(e) => setFilterLanguage(e.target.value as Language | 'all')}
          className="px-4 py-2 border border-gray-300 rounded-lg"
        >
          <option value="all">All Languages</option>
          {Object.values(LANGUAGES).map((lang) => (
            <option key={lang.code} value={lang.code}>
              {lang.flag} {lang.name}
            </option>
          ))}
        </select>

        {/* Entity type filter */}
        <select
          value={filterEntityType}
          onChange={(e) => setFilterEntityType(e.target.value as EntityType | 'all')}
          className="px-4 py-2 border border-gray-300 rounded-lg"
        >
          <option value="all">All Types</option>
          {Object.values(ENTITY_TYPES).map((type) => (
            <option key={type.type} value={type.type}>
              {type.icon} {type.label}
            </option>
          ))}
        </select>

        {/* Status filter */}
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value as TranslationStatus | 'all')}
          className="px-4 py-2 border border-gray-300 rounded-lg"
        >
          <option value="all">All Status</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>

      {/* Results count */}
      <div className="text-sm text-gray-600">
        Showing {filteredTranslations.length} of {translations.length} translations
      </div>

      {/* Translation cards */}
      <div className="space-y-3">
        {filteredTranslations.map((translation) => {
          const lang = LANGUAGES[translation.language]
          const entityType = ENTITY_TYPES[translation.entity_type]

          return (
            <div
              key={translation.id}
              className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                {/* Translation info */}
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    {/* Language badge */}
                    <div className="flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                      <span>{lang.flag}</span>
                      <span>{lang.name}</span>
                    </div>

                    {/* Entity type badge */}
                    <div className="flex items-center gap-1 px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm">
                      <span>{entityType.icon}</span>
                      <span>{entityType.label}</span>
                    </div>

                    {/* Field name */}
                    <div className="px-3 py-1 bg-gray-100 text-gray-700 rounded text-sm font-mono">
                      {translation.field_name}
                    </div>

                    {/* Status badge */}
                    <div
                      className={`px-3 py-1 rounded-full text-sm font-medium flex items-center gap-1.5 ${
                        translation.status === 'approved'
                          ? 'bg-green-100 text-green-700'
                          : translation.status === 'rejected'
                          ? 'bg-red-100 text-red-700'
                          : 'bg-yellow-100 text-yellow-700'
                      }`}
                    >
                      {translation.status === 'approved' && (
                        <>
                          <CheckCircle className="w-4 h-4" />
                          <span>Approved</span>
                        </>
                      )}
                      {translation.status === 'rejected' && (
                        <>
                          <XCircle className="w-4 h-4" />
                          <span>Rejected</span>
                        </>
                      )}
                      {translation.status === 'pending' && (
                        <span>Pending</span>
                      )}
                    </div>
                  </div>

                  {/* Translation content */}
                  <div className="bg-gray-50 rounded p-3 mb-2">
                    <p className="text-sm text-gray-900 whitespace-pre-wrap line-clamp-3">
                      {translation.translated_text}
                    </p>
                  </div>

                  {/* Meta info */}
                  <div className="text-xs text-gray-500">
                    Entity ID: {translation.entity_id} • Created {formatDateTime(translation.created_at)}
                    {translation.updated_at !== translation.created_at && (
                      <> • Updated {formatDateTime(translation.updated_at)}</>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex flex-col gap-2 ml-4">
                  {translation.status === 'pending' && (
                    <>
                      <button
                        onClick={() => onApprove(translation)}
                        className="px-3 py-1.5 text-sm bg-green-50 text-green-700 rounded hover:bg-green-100 whitespace-nowrap"
                        title="Approve Translation"
                      >
                        ✅ Approve
                      </button>
                      <button
                        onClick={() => onReject(translation)}
                        className="px-3 py-1.5 text-sm bg-red-50 text-red-700 rounded hover:bg-red-100 whitespace-nowrap"
                        title="Reject Translation"
                      >
                        ❌ Reject
                      </button>
                    </>
                  )}
                  <button
                    onClick={() => onEdit(translation)}
                    className="px-3 py-1.5 text-sm bg-blue-50 text-blue-700 rounded hover:bg-blue-100 whitespace-nowrap"
                    title="Edit Translation"
                  >
                    ✏️ Edit
                  </button>
                  <button
                    onClick={() => onDelete(translation)}
                    className="px-3 py-1.5 text-sm bg-gray-50 text-gray-700 rounded hover:bg-gray-100 whitespace-nowrap"
                    title="Delete Translation"
                  >
                    🗑️ Delete
                  </button>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* No results */}
      {filteredTranslations.length === 0 && (
        <div className="text-center py-8 bg-gray-50 rounded-lg">
          <p className="text-gray-600">No translations match your filters</p>
          <button
            onClick={() => {
              setSearchQuery('')
              setFilterLanguage('all')
              setFilterEntityType('all')
              setFilterStatus('all')
            }}
            className="mt-2 text-sm text-blue-600 hover:underline"
          >
            Clear filters
          </button>
        </div>
      )}
    </div>
  )
}

export default TranslationList
