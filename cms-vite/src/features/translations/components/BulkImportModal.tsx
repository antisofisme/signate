/**
 * Bulk Import Modal Component
 * Import translations from JSON array or CSV format
 */

import { useState } from 'react'
import { X, ClipboardList, CheckCircle, AlertTriangle, FastForward } from 'lucide-react'
import { useBulkImportTranslations } from '../hooks/useTranslations'
import type { BulkImportItem } from '../types/translation.types'

interface BulkImportModalProps {
  isOpen: boolean
  onClose: () => void
}

export const BulkImportModal = ({ isOpen, onClose }: BulkImportModalProps) => {
  const [importData, setImportData] = useState('')
  const [skipDuplicates, setSkipDuplicates] = useState(true)
  const [errors, setErrors] = useState<string[]>([])

  const bulkImportMutation = useBulkImportTranslations()

  const handleImport = async () => {
    setErrors([])

    try {
      // Parse JSON input
      const parsed = JSON.parse(importData)

      // Validate format
      if (!Array.isArray(parsed)) {
        setErrors(['Input must be a JSON array'])
        return
      }

      // Validate each item
      const validationErrors: string[] = []
      parsed.forEach((item, index) => {
        if (!item.entity_type || !item.entity_id || !item.language || !item.field_name || !item.translated_text) {
          validationErrors.push(
            `Row ${index + 1}: Missing required fields (entity_type, entity_id, language, field_name, translated_text)`
          )
        }
      })

      if (validationErrors.length > 0) {
        setErrors(validationErrors)
        return
      }

      // Import translations
      const result = await bulkImportMutation.mutateAsync({
        translations: parsed as BulkImportItem[],
        skip_duplicates: skipDuplicates,
      })

      // Show results
      if (result.errors.length > 0) {
        setErrors(result.errors.map((e) => `Row ${e.row}: ${e.error}`))
      } else {
        // Success - close modal
        onClose()
        setImportData('')
        setErrors([])
      }
    } catch (error) {
      if (error instanceof SyntaxError) {
        setErrors(['Invalid JSON format. Please check your input.'])
      } else {
        setErrors(['Import failed. Please try again.'])
      }
    }
  }

  const exampleData = [
    {
      entity_type: 'content',
      entity_id: 1,
      language: 'id',
      field_name: 'title',
      translated_text: 'Judul Konten dalam Bahasa Indonesia',
    },
    {
      entity_type: 'playlist',
      entity_id: 2,
      language: 'zh',
      field_name: 'name',
      translated_text: '播放列表名称',
    },
  ]

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 rounded-t-lg">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Bulk Import Translations</h2>
            <button
              onClick={onClose}
              className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
              disabled={bulkImportMutation.isPending}
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Instructions */}
          <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <div className="flex items-start gap-2 mb-2">
              <ClipboardList className="w-5 h-5 text-blue-900 dark:text-blue-300 flex-shrink-0 mt-0.5" />
              <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-300">Instructions</h3>
            </div>
            <ol className="text-xs text-blue-800 dark:text-blue-200 space-y-1 list-decimal list-inside">
              <li>Paste a JSON array of translations below</li>
              <li>Each translation must have: entity_type, entity_id, language, field_name, translated_text</li>
              <li>Click "Import" to process the translations</li>
              <li>Duplicates will be skipped if the option is enabled</li>
            </ol>
          </div>

          {/* Example */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Example Format:</label>
              <button
                type="button"
                onClick={() => setImportData(JSON.stringify(exampleData, null, 2))}
                className="text-xs px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
              >
                Use Example
              </button>
            </div>
            <pre className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded p-3 text-xs overflow-x-auto text-gray-900 dark:text-gray-100">
              {JSON.stringify(exampleData, null, 2)}
            </pre>
          </div>

          {/* Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              JSON Data *
            </label>
            <textarea
              value={importData}
              onChange={(e) => setImportData(e.target.value)}
              rows={12}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md font-mono text-xs bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
              placeholder="Paste JSON array here..."
              disabled={bulkImportMutation.isPending}
            />
          </div>

          {/* Options */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="skipDuplicates"
              checked={skipDuplicates}
              onChange={(e) => setSkipDuplicates(e.target.checked)}
              disabled={bulkImportMutation.isPending}
              className="w-4 h-4"
            />
            <label htmlFor="skipDuplicates" className="text-sm text-gray-700 dark:text-gray-300">
              Skip duplicate translations (same entity_type, entity_id, language, field_name)
            </label>
          </div>

          {/* Errors */}
          {errors.length > 0 && (
            <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="w-5 h-5 text-red-900 dark:text-red-300" />
                <h4 className="text-sm font-semibold text-red-900 dark:text-red-300">Validation Errors</h4>
              </div>
              <ul className="text-xs text-red-800 dark:text-red-200 space-y-1 list-disc list-inside max-h-40 overflow-y-auto">
                {errors.map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Import Results */}
          {bulkImportMutation.isSuccess && bulkImportMutation.data && (
            <div className="bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle className="w-5 h-5 text-green-900 dark:text-green-300" />
                <h4 className="text-sm font-semibold text-green-900 dark:text-green-300">Import Complete</h4>
              </div>
              <div className="text-xs text-green-800 dark:text-green-200 space-y-1">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4" />
                  <span>Imported: {bulkImportMutation.data.imported}</span>
                </div>
                <div className="flex items-center gap-2">
                  <FastForward className="w-4 h-4" />
                  <span>Skipped: {bulkImportMutation.data.skipped}</span>
                </div>
                {bulkImportMutation.data.errors.length > 0 && (
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4" />
                    <span>Errors: {bulkImportMutation.data.errors.length}</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-6 py-4 rounded-b-lg">
          <div className="flex justify-end gap-3">
            <button
              onClick={onClose}
              disabled={bulkImportMutation.isPending}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleImport}
              disabled={bulkImportMutation.isPending || !importData.trim()}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
            >
              {bulkImportMutation.isPending && (
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
              Import Translations
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default BulkImportModal
