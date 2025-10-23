import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { contentAPI, clientAPI } from '../../../services/api'
import { Tv, Monitor, ArrowRight, ArrowLeft, FileImage } from 'lucide-react'

/**
 * AssignContentModal Component
 * Modal for assigning/unassigning content to/from a specific device
 *
 * Features:
 * - Two-column layout (available content | assigned content)
 * - Drag-like interface with arrow indicators
 * - Real-time playlist synchronization
 * - Video thumbnail preview with HTML5 video
 * - Optimistic UI updates
 * - Visual feedback for hover states
 *
 * @param {Object} device - Device object to assign content to
 * @param {Function} onClose - Callback when modal should close
 */
export default function AssignContentModal({ device, onClose }) {
  const queryClient = useQueryClient()

  // Fetch all content
  const { data: contentData } = useQuery({
    queryKey: ['content'],
    queryFn: () => contentAPI.list().then(res => res.data),
  })

  // Fetch device playlist to see what's assigned
  const { data: playlistData } = useQuery({
    queryKey: ['device-playlist', device.id],
    queryFn: () => clientAPI.getPlaylist(device.id).then(res => res.data),
  })

  // Assign content mutation
  const assignMutation = useMutation({
    mutationFn: ({ contentId }) => contentAPI.assign(contentId, {
      device_id: device.id,
      priority: 0
    }),
    onSuccess: () => {
      queryClient.invalidateQueries(['device-playlist', device.id])
      queryClient.invalidateQueries(['devices'])
    },
    onError: (error) => {
      alert(error.response?.data?.detail || 'Assignment failed')
    }
  })

  // Unassign content mutation
  const unassignMutation = useMutation({
    mutationFn: ({ contentId }) => contentAPI.unassign(contentId, {
      device_id: device.id,
      priority: 0
    }),
    onSuccess: () => {
      queryClient.invalidateQueries(['device-playlist', device.id])
      queryClient.invalidateQueries(['devices'])
    },
    onError: (error) => {
      alert(error.response?.data?.detail || 'Unassignment failed')
    }
  })

  const handleAssign = (contentId) => {
    assignMutation.mutate({ contentId })
  }

  const handleUnassign = (contentId) => {
    unassignMutation.mutate({ contentId })
  }

  const assignedContentIds = playlistData?.playlist?.map(item => item.content_id) || []
  const allContent = contentData?.items || []
  const unassignedContent = allContent.filter(c => !assignedContentIds.includes(c.id))
  const assignedContent = allContent.filter(c => assignedContentIds.includes(c.id))

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center">
            {device.device_uuid ? (
              <Tv className="w-6 h-6 text-blue-600 mr-3" />
            ) : (
              <Monitor className="w-6 h-6 text-green-600 mr-3" />
            )}
            <h2 className="text-2xl font-bold">Assign Content: {device.device_name}</h2>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 text-2xl">
            ✕
          </button>
        </div>

        {/* Two-column layout */}
        <div className="flex-1 grid grid-cols-2 gap-6 p-6 overflow-hidden min-h-0">
          {/* Left: Unassigned Content */}
          <div className="flex flex-col min-h-0">
            <div className="flex items-center justify-between mb-4 flex-shrink-0">
              <h3 className="font-bold text-gray-800 text-lg">Available Content</h3>
              <span className="text-sm text-gray-600">
                {unassignedContent.length} items
              </span>
            </div>
            <div className="flex-1 overflow-y-auto space-y-2 pr-2 min-h-0">
              {unassignedContent.map((content) => (
                <div
                  key={content.id}
                  onClick={() => handleAssign(content.id)}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-blue-50 cursor-pointer transition-colors group"
                >
                  <div className="flex items-center flex-1 min-w-0">
                    <div className="flex-shrink-0 w-16 h-16 bg-gray-200 rounded mr-3 overflow-hidden">
                      {content.content_type === 'video' ? (
                        <video
                          src={`http://192.168.5.12:8001/api/content/${content.id}/image`}
                          className="w-full h-full object-cover"
                          preload="metadata"
                          onLoadedMetadata={(e) => {
                            e.target.currentTime = 0.1
                          }}
                        />
                      ) : (
                        <img
                          src={`http://192.168.5.12:8001/api/content/${content.id}/image`}
                          alt={content.title}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            e.target.style.display = 'none'
                          }}
                        />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-800 truncate">{content.title}</p>
                      <p className="text-sm text-gray-600">
                        {content.content_type.toUpperCase()} • {content.duration}s
                      </p>
                    </div>
                  </div>
                  <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-blue-600 transition-colors flex-shrink-0 ml-2" />
                </div>
              ))}
              {unassignedContent.length === 0 && (
                <div className="text-center py-12 text-gray-500">
                  <FileImage className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>All content assigned</p>
                </div>
              )}
            </div>
          </div>

          {/* Right: Assigned Content */}
          <div className="flex flex-col min-h-0">
            <div className="flex items-center justify-between mb-4 flex-shrink-0">
              <h3 className="font-bold text-gray-800 text-lg">Assigned Content</h3>
              <span className="text-sm text-gray-600">
                {assignedContent.length} items
              </span>
            </div>
            <div className="flex-1 overflow-y-auto space-y-2 pr-2 min-h-0">
              {assignedContent.map((content) => (
                <div
                  key={content.id}
                  onClick={() => handleUnassign(content.id)}
                  className="flex items-center justify-between p-4 bg-green-50 rounded-lg hover:bg-red-50 cursor-pointer transition-colors group"
                >
                  <ArrowLeft className="w-5 h-5 text-gray-400 group-hover:text-red-600 transition-colors flex-shrink-0 mr-2" />
                  <div className="flex items-center flex-1 min-w-0">
                    <div className="flex-shrink-0 w-16 h-16 bg-gray-200 rounded mr-3 overflow-hidden">
                      {content.content_type === 'video' ? (
                        <video
                          src={`http://192.168.5.12:8001/api/content/${content.id}/image`}
                          className="w-full h-full object-cover"
                          preload="metadata"
                          onLoadedMetadata={(e) => {
                            e.target.currentTime = 0.1
                          }}
                        />
                      ) : (
                        <img
                          src={`http://192.168.5.12:8001/api/content/${content.id}/image`}
                          alt={content.title}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            e.target.style.display = 'none'
                          }}
                        />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-800 truncate">{content.title}</p>
                      <p className="text-sm text-gray-600">
                        {content.content_type.toUpperCase()} • {content.duration}s
                      </p>
                    </div>
                  </div>
                </div>
              ))}
              {assignedContent.length === 0 && (
                <div className="text-center py-12 text-gray-500">
                  <FileImage className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>No content assigned</p>
                  <p className="text-xs mt-1">Click content from left to assign</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
