/**
 * Translations Page
 * Main page for translation management
 */

import { useState } from 'react'
import {
  useTranslations,
  useCreateTranslation,
  useUpdateTranslation,
  useDeleteTranslation,
  useApproveTranslation,
  useRejectTranslation,
} from '../hooks/useTranslations'
import TranslationList from '../components/TranslationList'
import TranslationForm from '../components/TranslationForm'
import TranslationStats from '../components/TranslationStats'
import BulkImportModal from '../components/BulkImportModal'
import type {
  Translation,
  CreateTranslationRequest,
  UpdateTranslationRequest,
} from '../types/translation.types'

type ModalMode = 'create' | 'edit' | null

export const TranslationsPage = () => {
  const [modalMode, setModalMode] = useState<ModalMode>(null)
  const [selectedTranslation, setSelectedTranslation] = useState<Translation | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [showBulkImport, setShowBulkImport] = useState(false)
  const [showStats, setShowStats] = useState(false)

  // Queries
  const { data, isLoading } = useTranslations()

  // Mutations
  const createMutation = useCreateTranslation()
  const updateMutation = useUpdateTranslation()
  const deleteMutation = useDeleteTranslation()
  const approveMutation = useApproveTranslation()
  const rejectMutation = useRejectTranslation()

  // Handlers
  const handleCreate = () => {
    setModalMode('create')
    setSelectedTranslation(null)
  }

  const handleEdit = (translation: Translation) => {
    setModalMode('edit')
    setSelectedTranslation(translation)
  }

  const handleDelete = (translation: Translation) => {
    setSelectedTranslation(translation)
    setShowDeleteConfirm(true)
  }

  const handleApprove = async (translation: Translation) => {
    try {
      await approveMutation.mutateAsync(translation.id)
    } catch (error) {
      console.error('Approve error:', error)
    }
  }

  const handleReject = async (translation: Translation) => {
    try {
      await rejectMutation.mutateAsync(translation.id)
    } catch (error) {
      console.error('Reject error:', error)
    }
  }

  const handleSubmit = async (
    formData: CreateTranslationRequest | UpdateTranslationRequest
  ) => {
    try {
      if (modalMode === 'create') {
        await createMutation.mutateAsync(formData as CreateTranslationRequest)
      } else if (modalMode === 'edit' && selectedTranslation) {
        await updateMutation.mutateAsync({
          id: selectedTranslation.id,
          data: formData as UpdateTranslationRequest,
        })
      }
      setModalMode(null)
      setSelectedTranslation(null)
    } catch (error) {
      console.error('Submit error:', error)
    }
  }

  const confirmDelete = async () => {
    if (!selectedTranslation) return

    try {
      await deleteMutation.mutateAsync(selectedTranslation.id)
      setShowDeleteConfirm(false)
      setSelectedTranslation(null)
    } catch (error) {
      console.error('Delete error:', error)
    }
  }

  const translations = data?.translations || []

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Translation Manager</h1>
            <p className="mt-2 text-gray-600">
              Manage multi-language translations for content, playlists, templates, and widgets
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => setShowStats(!showStats)}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 ${
                showStats
                  ? 'bg-purple-600 text-white hover:bg-purple-700'
                  : 'bg-purple-50 text-purple-700 hover:bg-purple-100'
              }`}
            >
              <span>📊</span>
              <span>{showStats ? 'Hide' : 'Show'} Statistics</span>
            </button>
            <button
              onClick={() => setShowBulkImport(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
            >
              <span>📥</span>
              <span>Bulk Import</span>
            </button>
            <button
              onClick={handleCreate}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
            >
              <span>➕</span>
              <span>Create Translation</span>
            </button>
          </div>
        </div>
      </div>

      {/* Statistics */}
      {showStats && (
        <div className="mb-8">
          <TranslationStats />
        </div>
      )}

      {/* Translation List */}
      <TranslationList
        translations={translations}
        isLoading={isLoading}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onApprove={handleApprove}
        onReject={handleReject}
      />

      {/* Create/Edit Modal */}
      {(modalMode === 'create' || modalMode === 'edit') && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-white rounded-lg max-w-4xl w-full my-8">
            <div className="sticky top-0 bg-white border-b px-6 py-4 rounded-t-lg">
              <h2 className="text-xl font-semibold text-gray-900">
                {modalMode === 'create' ? 'Create Translation' : 'Edit Translation'}
              </h2>
            </div>
            <div className="p-6 max-h-[calc(100vh-200px)] overflow-y-auto">
              <TranslationForm
                translation={selectedTranslation || undefined}
                onSubmit={handleSubmit}
                onCancel={() => {
                  setModalMode(null)
                  setSelectedTranslation(null)
                }}
                isLoading={createMutation.isPending || updateMutation.isPending}
              />
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation */}
      {showDeleteConfirm && selectedTranslation && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Delete Translation</h2>
            <p className="text-gray-600 mb-6">
              Are you sure you want to delete this translation? This action cannot be undone.
            </p>
            <div className="bg-gray-50 border border-gray-200 rounded p-3 mb-6">
              <p className="text-sm">
                <strong>Language:</strong> {selectedTranslation.language.toUpperCase()}
              </p>
              <p className="text-sm">
                <strong>Field:</strong> {selectedTranslation.field_name}
              </p>
              <p className="text-sm">
                <strong>Entity:</strong> {selectedTranslation.entity_type} #{selectedTranslation.entity_id}
              </p>
            </div>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowDeleteConfirm(false)
                  setSelectedTranslation(null)
                }}
                disabled={deleteMutation.isPending}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                disabled={deleteMutation.isPending}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 flex items-center gap-2"
              >
                {deleteMutation.isPending && (
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
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Import Modal */}
      <BulkImportModal
        isOpen={showBulkImport}
        onClose={() => setShowBulkImport(false)}
      />
    </div>
  )
}

export default TranslationsPage
