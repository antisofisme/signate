/**
 * Templates Page
 * Main page for template management
 */

import { useState } from 'react'
import { useTemplates, useCreateTemplate, useUpdateTemplate, useDeleteTemplate } from '../hooks/useTemplates'
import TemplateList from '../components/TemplateList'
import TemplateForm from '../components/TemplateForm'
import TemplatePreview from '../components/TemplatePreview'
import type { Template, CreateTemplateRequest, UpdateTemplateRequest } from '../types/template.types'

type ModalMode = 'create' | 'edit' | 'preview' | null

export const TemplatesPage = () => {
  const [modalMode, setModalMode] = useState<ModalMode>(null)
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)

  // Queries
  const { data, isLoading } = useTemplates()

  // Mutations
  const createMutation = useCreateTemplate()
  const updateMutation = useUpdateTemplate()
  const deleteMutation = useDeleteTemplate()

  // Handlers
  const handleCreate = () => {
    setModalMode('create')
    setSelectedTemplate(null)
  }

  const handleEdit = (template: Template) => {
    setModalMode('edit')
    setSelectedTemplate(template)
  }

  const handleDelete = (template: Template) => {
    setSelectedTemplate(template)
    setShowDeleteConfirm(true)
  }

  const handlePreview = (template: Template) => {
    setModalMode('preview')
    setSelectedTemplate(template)
  }

  const handleSubmit = async (formData: CreateTemplateRequest | UpdateTemplateRequest) => {
    try {
      if (modalMode === 'create') {
        await createMutation.mutateAsync(formData as CreateTemplateRequest)
      } else if (modalMode === 'edit' && selectedTemplate) {
        await updateMutation.mutateAsync({
          id: selectedTemplate.id,
          data: formData as UpdateTemplateRequest,
        })
      }
      setModalMode(null)
      setSelectedTemplate(null)
    } catch (error) {
      // Error handled by mutation hook
      console.error(error)
    }
  }

  const confirmDelete = async () => {
    if (!selectedTemplate) return

    try {
      await deleteMutation.mutateAsync(selectedTemplate.id)
      setShowDeleteConfirm(false)
      setSelectedTemplate(null)
    } catch (error) {
      // Error handled by mutation hook
      console.error(error)
    }
  }

  const templates = data?.templates || []

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Template Editor</h1>
            <p className="mt-2 text-gray-600">
              Create and manage dynamic content templates with variable substitution
            </p>
          </div>
          <button
            onClick={handleCreate}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
          >
            <span>➕</span>
            <span>Create Template</span>
          </button>
        </div>
      </div>

      {/* Template List */}
      <TemplateList
        templates={templates}
        isLoading={isLoading}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onPreview={handlePreview}
      />

      {/* Create/Edit Modal */}
      {(modalMode === 'create' || modalMode === 'edit') && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-white rounded-lg max-w-6xl w-full my-8">
            <div className="sticky top-0 bg-white border-b px-6 py-4 rounded-t-lg">
              <h2 className="text-xl font-semibold text-gray-900">
                {modalMode === 'create' ? 'Create Template' : 'Edit Template'}
              </h2>
            </div>
            <div className="p-6 max-h-[calc(100vh-200px)] overflow-y-auto">
              <TemplateForm
                template={selectedTemplate || undefined}
                onSubmit={handleSubmit}
                onCancel={() => {
                  setModalMode(null)
                  setSelectedTemplate(null)
                }}
                isLoading={createMutation.isPending || updateMutation.isPending}
              />
            </div>
          </div>
        </div>
      )}

      {/* Preview Modal */}
      {modalMode === 'preview' && selectedTemplate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b px-6 py-4 rounded-t-lg">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">
                    Preview: {selectedTemplate.name}
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">
                    {selectedTemplate.description || 'No description'}
                  </p>
                </div>
                <button
                  onClick={() => {
                    setModalMode(null)
                    setSelectedTemplate(null)
                  }}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            <div className="p-6">
              {/* Template Content */}
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">Template Content:</h3>
                <div className="bg-gray-50 rounded p-4 border border-gray-200">
                  <pre className="text-sm whitespace-pre-wrap break-words font-mono">
                    {selectedTemplate.content}
                  </pre>
                </div>
              </div>

              {/* Variables */}
              {Object.keys(selectedTemplate.variables || {}).length > 0 && (
                <div className="mb-6">
                  <h3 className="text-sm font-semibold text-gray-700 mb-2">Variables:</h3>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(selectedTemplate.variables).map(([name, type]) => (
                      <div key={name} className="bg-blue-50 border border-blue-200 rounded px-3 py-2">
                        <code className="text-sm text-blue-700 font-mono">
                          {'{{'}{name}{'}}'}
                        </code>
                        <span className="text-xs text-blue-600 ml-2">({type})</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Preview */}
              <TemplatePreview
                content={selectedTemplate.content}
                variables={selectedTemplate.variables || {}}
                previewData={selectedTemplate.preview_data}
              />
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation */}
      {showDeleteConfirm && selectedTemplate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Delete Template</h2>
            <p className="text-gray-600 mb-6">
              Are you sure you want to delete{' '}
              <strong className="text-gray-900">{selectedTemplate.name}</strong>? This action
              cannot be undone.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowDeleteConfirm(false)
                  setSelectedTemplate(null)
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

export default TemplatesPage
