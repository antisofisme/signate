/**
 * Decision Types Tab - Configuration Menu
 * CRUD for decision types (system-defined are protected from editing/deletion)
 */

import { useState } from 'react'
import {
  useDecisionTypes,
  useCreateDecisionType,
  useDeleteDecisionType
} from '../hooks/useConfig'
import type { DecisionType, DecisionTypeCreate } from '../types/Config'

export function DecisionTypesTab() {
  const { data, isLoading, error } = useDecisionTypes(false) // Show all including inactive
  const createMutation = useCreateDecisionType()
  const deleteMutation = useDeleteDecisionType()

  const [isCreating, setIsCreating] = useState(false)
  const [formData, setFormData] = useState<DecisionTypeCreate>({
    type_code: '',
    type_name: '',
    description: '',
    context_schema: {},
    is_active: true
  })

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await createMutation.mutateAsync(formData)
      setIsCreating(false)
      setFormData({ type_code: '', type_name: '', description: '', context_schema: {}, is_active: true })
    } catch (err) {
      console.error('Create failed:', err)
    }
  }

  const handleDelete = async (dtype: DecisionType) => {
    if (dtype.is_system_defined) {
      alert('Cannot delete system-defined decision types')
      return
    }
    if (!confirm(`Delete decision type "${dtype.type_name}"? Rules using it will have decision_type_id set to NULL.`)) {
      return
    }
    try {
      await deleteMutation.mutateAsync(dtype.decision_type_id)
    } catch (err) {
      console.error('Delete failed:', err)
    }
  }

  if (isLoading) {
    return <div className="flex items-center justify-center h-64"><div className="text-gray-500">Loading...</div></div>
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded p-4">
        <div className="text-red-800 font-semibold">Error loading decision types</div>
        <div className="text-red-600 text-sm mt-1">{error instanceof Error ? error.message : 'Unknown error'}</div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Decision Types</h2>
          <p className="text-sm text-gray-600 mt-1">
            Decision type contracts that define context schema for rule evaluation
          </p>
        </div>
        <button
          onClick={() => setIsCreating(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded font-semibold hover:bg-blue-700"
        >
          + Add Decision Type
        </button>
      </div>

      {/* Create Form */}
      {isCreating && (
        <div className="bg-gray-50 border rounded p-4">
          <h3 className="font-semibold mb-3">New Decision Type</h3>
          <form onSubmit={handleCreate} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium mb-1">Type Code (uppercase, snake_case)</label>
                <input
                  type="text"
                  value={formData.type_code}
                  onChange={(e) => setFormData({ ...formData, type_code: e.target.value.toUpperCase() })}
                  className="w-full border rounded px-3 py-2"
                  placeholder="PURCHASE_REQUEST"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Type Name</label>
                <input
                  type="text"
                  value={formData.type_name}
                  onChange={(e) => setFormData({ ...formData, type_name: e.target.value })}
                  className="w-full border rounded px-3 py-2"
                  placeholder="Purchase Request"
                  required
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full border rounded px-3 py-2"
                rows={2}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Context Schema (JSON)</label>
              <textarea
                value={JSON.stringify(formData.context_schema, null, 2)}
                onChange={(e) => {
                  try {
                    setFormData({ ...formData, context_schema: JSON.parse(e.target.value) })
                  } catch {
                    // Invalid JSON, ignore
                  }
                }}
                className="w-full border rounded px-3 py-2 font-mono text-sm"
                rows={4}
                placeholder='{"amount": "number", "department": "string"}'
              />
            </div>
            <div className="flex items-center">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="mr-2"
                />
                <span className="text-sm font-medium">Active</span>
              </label>
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={createMutation.isPending}
                className="bg-green-600 text-white px-4 py-2 rounded font-semibold hover:bg-green-700 disabled:opacity-50"
              >
                {createMutation.isPending ? 'Creating...' : 'Create'}
              </button>
              <button
                type="button"
                onClick={() => setIsCreating(false)}
                className="bg-gray-300 text-gray-700 px-4 py-2 rounded font-semibold hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Table */}
      <div className="bg-white border rounded overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Code</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Name</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Description</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Type</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Status</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {data?.decision_types.map((dtype) => (
              <tr key={dtype.decision_type_id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm font-mono">{dtype.type_code}</td>
                <td className="px-4 py-3 text-sm font-semibold">{dtype.type_name}</td>
                <td className="px-4 py-3 text-sm text-gray-600">{dtype.description || '-'}</td>
                <td className="px-4 py-3 text-sm">
                  {dtype.is_system_defined ? (
                    <span className="px-2 py-1 rounded text-xs font-semibold bg-purple-100 text-purple-800">
                      SYSTEM
                    </span>
                  ) : (
                    <span className="px-2 py-1 rounded text-xs font-semibold bg-blue-100 text-blue-800">
                      CUSTOM
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-sm">
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${dtype.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                    {dtype.is_active ? 'ACTIVE' : 'INACTIVE'}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm">
                  {dtype.is_system_defined ? (
                    <span className="text-gray-400 text-xs">Protected</span>
                  ) : (
                    <button
                      onClick={() => handleDelete(dtype)}
                      className="text-red-600 hover:text-red-800 font-medium"
                    >
                      Delete
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {data?.decision_types.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <div className="text-lg font-semibold mb-2">No decision types</div>
            <p className="text-sm">Add your first decision type to get started.</p>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="bg-blue-50 border border-blue-200 rounded p-3 text-sm text-blue-800">
        <strong>Decision Type Contract:</strong> Defines the context schema expected for rule evaluation.
        System-defined types are protected from editing and deletion.
      </div>
    </div>
  )
}
