import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { widgetsAPI } from '../../services/api'
import { Plus, Edit2, Trash2, Monitor, Globe } from 'lucide-react'
import { showToast } from '../../utils/toast'
import { Button } from '../shared'

export default function IFrameTab() {
  const queryClient = useQueryClient()

  const { data: widgetsData, isLoading } = useQuery({
    queryKey: ['widgets', 'iframe'],
    queryFn: () => widgetsAPI.list('iframe').then(res => res.data),
  })

  const deleteMutation = useMutation({
    mutationFn: widgetsAPI.delete,
    onSuccess: () => {
      queryClient.invalidateQueries(['widgets', 'iframe'])
      showToast.success('iFrame widget deleted successfully!')
    }
  })

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-800">iFrame Widgets</h3>
          <p className="text-sm text-gray-600">Embed external websites and web content</p>
        </div>
        <Button variant="primary" leftIcon={<Plus className="w-4 h-4" />}>
          Create iFrame
        </Button>
      </div>

      {isLoading && (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      )}

      {!isLoading && (!widgetsData?.items || widgetsData.items.length === 0) && (
        <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <Globe className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-600 font-medium">No iFrame Widgets</p>
          <p className="text-sm text-gray-500 mb-4">Create your first iFrame widget</p>
          <Button variant="primary" leftIcon={<Plus className="w-4 h-4" />}>
            Create iFrame
          </Button>
        </div>
      )}
    </div>
  )
}
