import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { widgetsAPI } from '../../services/api'
import { Plus, Edit2, Trash2, Monitor, Calendar as CalendarIcon } from 'lucide-react'
import { showToast } from '../../utils/toast'
import { Button } from '../shared'

/**
 * CalendarTab Component
 * Manage calendar event widgets
 *
 * Features:
 * - Create calendar displays
 * - List calendar widgets
 * - Assign to devices
 */
export default function CalendarTab() {
  const queryClient = useQueryClient()
  const [showCreateModal, setShowCreateModal] = useState(false)

  // Fetch calendar widgets
  const { data: widgetsData, isLoading } = useQuery({
    queryKey: ['widgets', 'calendar'],
    queryFn: () => widgetsAPI.list('calendar').then(res => res.data),
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: widgetsAPI.delete,
    onSuccess: () => {
      queryClient.invalidateQueries(['widgets', 'calendar'])
      showToast.success('Calendar widget deleted successfully!')
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Failed to delete widget')
    }
  })

  const handleDelete = (id, name) => {
    if (confirm(`Delete calendar widget "${name}"?`)) {
      deleteMutation.mutate(id)
    }
  }

  return (
    <div>
      {/* Header Actions */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-800">Calendar Widgets</h3>
          <p className="text-sm text-gray-600">Create and manage calendar event displays</p>
        </div>
        <Button
          variant="primary"
          leftIcon={<Plus className="w-4 h-4" />}
          onClick={() => setShowCreateModal(true)}
        >
          Create Calendar
        </Button>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      )}

      {/* Widgets Grid */}
      {!isLoading && widgetsData?.items && widgetsData.items.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {widgetsData.items.map((widget) => (
            <div key={widget.id} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
              {/* Widget Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <CalendarIcon className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-800">{widget.name}</h4>
                    <p className="text-xs text-gray-500">{widget.type}</p>
                  </div>
                </div>
              </div>

              {/* Widget Info */}
              <div className="text-sm text-gray-600 mb-4">
                <p className="truncate">{widget.description || 'No description'}</p>
              </div>

              {/* Widget Actions */}
              <div className="flex items-center gap-2 pt-3 border-t border-gray-200">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => {}}
                  leftIcon={<Edit2 className="w-3 h-3" />}
                >
                  Edit
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => {}}
                  leftIcon={<Monitor className="w-3 h-3" />}
                >
                  Assign
                </Button>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => handleDelete(widget.id, widget.name)}
                >
                  <Trash2 className="w-3 h-3" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && (!widgetsData?.items || widgetsData.items.length === 0) && (
        <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <CalendarIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-600 font-medium">No Calendar Widgets</p>
          <p className="text-sm text-gray-500 mb-4">Create your first calendar widget to get started</p>
          <Button
            variant="primary"
            leftIcon={<Plus className="w-4 h-4" />}
            onClick={() => setShowCreateModal(true)}
          >
            Create Calendar
          </Button>
        </div>
      )}

      {/* Modals - To be created */}
      {/* {showCreateModal && <CalendarFormModal onClose={() => setShowCreateModal(false)} />} */}
    </div>
  )
}
