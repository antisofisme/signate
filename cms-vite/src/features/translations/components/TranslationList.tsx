/**
 * Translation List Component
 * Display translations with filters and actions
 */

import { useState } from 'react'
import { CheckCircle, XCircle, Globe, Edit, Trash2 } from 'lucide-react'
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
  isApproving?: boolean
  isRejecting?: boolean
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
          <div key={i} className="h-24 bg-gray-100 dark:bg-gray-700 rounded-lg animate-pulse" />
        ))}
      </div>
    )
  }

  if (translations.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 dark:bg-gray-800 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600">
        <Globe className="w-16 h-16 mx-auto mb-4 text-gray-400 dark:text-gray-500" />
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">No translations yet</h3>
        <p className="text-gray-600 dark:text-gray-400 mb-4">Create your first translation to get started</p>
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
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          />
        </div>

        {/* Language filter */}
        <select
          value={filterLanguage}
          onChange={(e) => setFilterLanguage(e.target.value as Language | 'all')}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
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
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
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
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
        >
          <option value="all">All Status</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>

      {/* Results count */}
      <div className="text-sm text-gray-600 dark:text-gray-400">
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
              className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                {/* Translation info */}
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    {/* Language badge */}
                    <div className="flex items-center gap-1 px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded-full text-sm font-medium">
                      <span>{lang.flag}</span>
                      <span>{lang.name}</span>
                    </div>

                    {/* Entity type badge */}
                    <div className="flex items-center gap-1 px-3 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300 rounded-full text-sm">
                      <span>{entityType.icon}</span>
                      <span>{entityType.label}</span>
                    </div>

                    {/* Field name */}
                    <div className="px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded text-sm font-mono">
                      {translation.field_name}
                    </div>

                    {/* Status badge */}
                    <div
                      className={`px-3 py-1 rounded-full text-sm font-medium flex items-center gap-1.5 ${
                        translation.status === 'approved'
                          ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                          : translation.status === 'rejected'
                          ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
                          : 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300'
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
                  <div className="bg-gray-50 dark:bg-gray-700 rounded p-3 mb-2">
                    <p className="text-sm text-gray-900 dark:text-gray-100 whitespace-pre-wrap line-clamp-3">
                      {translation.translated_text}
                    </p>
                  </div>

                  {/* Meta info */}
                  <div className="text-xs text-gray-500 dark:text-gray-400">
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
                        className="px-3 py-1.5 text-sm bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded hover:bg-green-100 dark:hover:bg-green-900/50 whitespace-nowrap flex items-center gap-1"
                        title="Approve Translation"
                      >
                        <CheckCircle className="w-4 h-4" />
                        Approve
                      </button>
                      <button
                        onClick={() => onReject(translation)}
                        className="px-3 py-1.5 text-sm bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded hover:bg-red-100 dark:hover:bg-red-900/50 whitespace-nowrap flex items-center gap-1"
                        title="Reject Translation"
                      >
                        <XCircle className="w-4 h-4" />
                        Reject
                      </button>
                    </>
                  )}
                  <button
                    onClick={() => onEdit(translation)}
                    className="px-3 py-1.5 text-sm bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded hover:bg-blue-100 dark:hover:bg-blue-900/50 whitespace-nowrap flex items-center gap-1"
                    title="Edit Translation"
                  >
                    <Edit className="w-4 h-4" />
                    Edit
                  </button>
                  <button
                    onClick={() => onDelete(translation)}
                    className="px-3 py-1.5 text-sm bg-gray-50 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-100 dark:hover:bg-gray-600 whitespace-nowrap flex items-center gap-1"
                    title="Delete Translation"
                  >
                    <Trash2 className="w-4 h-4" />
                    Delete
                  </button>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* No results */}
      {filteredTranslations.length === 0 && (
        <div className="text-center py-8 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <p className="text-gray-600 dark:text-gray-400">No translations match your filters</p>
          <button
            onClick={() => {
              setSearchQuery('')
              setFilterLanguage('all')
              setFilterEntityType('all')
              setFilterStatus('all')
            }}
            className="mt-2 text-sm text-blue-600 dark:text-blue-400 hover:underline"
          >
            Clear filters
          </button>
        </div>
      )}
    </div>
  )
}

export default TranslationList
