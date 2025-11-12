/**
 * Widgets Page
 * Main page for widget management
 */

import { useState } from 'react'
import { useWidgets, useCreateWidget, useUpdateWidget, useDeleteWidget } from '../hooks/useWidgets'
import WidgetList from '../components/WidgetList'
import WidgetForm from '../components/WidgetForm'
import type { Widget, CreateWidgetRequest, UpdateWidgetRequest } from '../types/widget.types'

type ModalMode = 'create' | 'edit' | 'assign' | null

export const WidgetsPage = () => {
  const [modalMode, setModalMode] = useState<ModalMode>(null)
  const [selectedWidget, setSelectedWidget] = useState<Widget | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)

  // Queries
  const { data, isLoading } = useWidgets()

  // Mutations
  const createMutation = useCreateWidget()
  const updateMutation = useUpdateWidget()
  const deleteMutation = useDeleteWidget()

  // Handlers
  const handleCreate = () => {
    setModalMode('create')
    setSelectedWidget(null)
  }

  const handleEdit = (widget: Widget) => {
    setModalMode('edit')
    setSelectedWidget(widget)
  }

  const handleDelete = (widget: Widget) => {
    setSelectedWidget(widget)
    setShowDeleteConfirm(true)
  }

  const handleAssign = (widget: Widget) => {
    setModalMode('assign')
    setSelectedWidget(widget)
  }

  const handleSubmit = async (formData: CreateWidgetRequest | UpdateWidgetRequest) => {
    try {
      if (modalMode === 'create') {
        await createMutation.mutateAsync(formData as CreateWidgetRequest)
      } else if (modalMode === 'edit' && selectedWidget) {
        await updateMutation.mutateAsync({
          id: selectedWidget.id,
          data: formData as UpdateWidgetRequest,
        })
      }
      setModalMode(null)
      setSelectedWidget(null)
    } catch (error) {
      // Error handled by mutation hook
      console.error(error)
    }
  }

  const confirmDelete = async () => {
    if (!selectedWidget) return

    try {
      await deleteMutation.mutateAsync(selectedWidget.id)
      setShowDeleteConfirm(false)
      setSelectedWidget(null)
    } catch (error) {
      // Error handled by mutation hook
      console.error(error)
    }
  }

  const widgets = data?.widgets || []

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Widget Manager</h1>
            <p className="mt-2 text-gray-600">
              Create and manage overlay widgets for your digital signage
            </p>
          </div>
          <button
            onClick={handleCreate}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <span>➕</span>
            <span>Create Widget</span>
          </button>
        </div>
      </div>

      {/* Widget List */}
      <WidgetList
        widgets={widgets}
        isLoading={isLoading}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onAssign={handleAssign}
      />

      {/* Create/Edit Modal */}
      {(modalMode === 'create' || modalMode === 'edit') && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b px-6 py-4">
              <h2 className="text-xl font-semibold text-gray-900">
                {modalMode === 'create' ? 'Create Widget' : 'Edit Widget'}
              </h2>
            </div>
            <div className="p-6">
              <WidgetForm
                widget={selectedWidget || undefined}
                onSubmit={handleSubmit}
                onCancel={() => {
                  setModalMode(null)
                  setSelectedWidget(null)
                }}
                isLoading={createMutation.isPending || updateMutation.isPending}
              />
            </div>
          </div>
        </div>
      )}

      {/* Assign Modal (placeholder) */}
      {modalMode === 'assign' && selectedWidget && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Assign Widget to Playlist
            </h2>
            <p className="text-gray-600 mb-4">
              Selected widget: <strong>{selectedWidget.name}</strong>
            </p>
            <div className="bg-yellow-50 border border-yellow-200 rounded p-4 mb-4">
              <p className="text-sm text-yellow-800">
                ⚠️ Playlist assignment UI will be implemented in next phase.
              </p>
            </div>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => {
                  setModalMode(null)
                  setSelectedWidget(null)
                }}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation */}
      {showDeleteConfirm && selectedWidget && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Delete Widget</h2>
            <p className="text-gray-600 mb-6">
              Are you sure you want to delete{' '}
              <strong className="text-gray-900">{selectedWidget.name}</strong>? This action
              cannot be undone.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowDeleteConfirm(false)
                  setSelectedWidget(null)
                }}
                disabled={deleteMutation.isPending}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
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
    </div>
  )
}

export default WidgetsPage
