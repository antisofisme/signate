import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { contentAPI, clientAPI } from '../../../services/api'
import { Tv, Monitor, ArrowRight, ArrowLeft, FileImage, X } from 'lucide-react'
import { showToast } from '../../../utils/toast'
import { Modal } from '../../shared'

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
      showToast.error(error.response?.data?.detail || 'Assignment failed')
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
      showToast.error(error.response?.data?.detail || 'Unassignment failed')
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
    <Modal
      isOpen={true}
      onClose={onClose}
      size="full"
      showCloseButton={false}
      bodyClassName="flex-1 overflow-hidden flex flex-col p-0"
    >
      {/* Custom Header - Fixed */}
      <div className="flex items-center justify-between p-6 bg-white dark:bg-gray-800 border-b flex-shrink-0">
        <div className="flex items-center">
          {device.device_uuid ? (
            <Tv className="w-6 h-6 text-blue-600 mr-3" />
          ) : (
            <Monitor className="w-6 h-6 text-green-600 mr-3" />
          )}
          <h2 className="text-2xl font-bold">Assign Content: {device.device_name}</h2>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 dark:text-gray-500 hover:text-gray-600 transition-colors p-1 rounded-lg hover:bg-gray-100"
          aria-label="Close modal"
        >
          <X className="w-6 h-6" />
        </button>
      </div>

        {/* Two-column layout - Scrollable */}
        <div className="flex-1 grid grid-cols-2 gap-6 p-6 overflow-hidden min-h-0">
          {/* Left: Unassigned Content */}
          <div className="flex flex-col min-h-0">
            <div className="flex items-center justify-between mb-4 flex-shrink-0">
              <h3 className="font-bold text-gray-900 dark:text-white text-xl">Available Content</h3>
              <span className="text-sm text-gray-700 dark:text-gray-300 font-medium">
                {unassignedContent.length} items
              </span>
            </div>
            <div className="flex-1 overflow-y-auto space-y-2 pr-2 min-h-0">
              {unassignedContent.map((content) => (
                <div
                  key={content.id}
                  onClick={() => handleAssign(content.id)}
                  className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 dark:bg-gray-900 rounded-lg hover:bg-blue-50 cursor-pointer transition-colors group"
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
                      <p className="font-medium text-gray-800 dark:text-gray-100 truncate">{content.title}</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {content.content_type.toUpperCase()} • {content.duration}s
                      </p>
                      {content.content_type === 'video' && (content.video_start_time > 0 || content.video_end_time) && (
                        <p className="text-xs text-blue-600 mt-0.5">
                          🎬 Segment: {content.video_start_time || 0}s - {content.video_end_time ? `${content.video_end_time}s` : 'end'}
                        </p>
                      )}
                    </div>
                  </div>
                  <ArrowRight className="w-5 h-5 text-gray-400 dark:text-gray-500 group-hover:text-blue-600 transition-colors flex-shrink-0 ml-2" />
                </div>
              ))}
              {unassignedContent.length === 0 && (
                <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                  <FileImage className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>All content assigned</p>
                </div>
              )}
            </div>
          </div>

          {/* Right: Assigned Content */}
          <div className="flex flex-col min-h-0">
            <div className="flex items-center justify-between mb-4 flex-shrink-0">
              <h3 className="font-bold text-gray-900 dark:text-white text-xl">Assigned Content</h3>
              <span className="text-sm text-gray-700 dark:text-gray-300 font-medium">
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
                  <ArrowLeft className="w-5 h-5 text-gray-400 dark:text-gray-500 group-hover:text-red-600 transition-colors flex-shrink-0 mr-2" />
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
                      <p className="font-medium text-gray-800 dark:text-gray-100 truncate">{content.title}</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {content.content_type.toUpperCase()} • {content.duration}s
                      </p>
                      {content.content_type === 'video' && (content.video_start_time > 0 || content.video_end_time) && (
                        <p className="text-xs text-blue-600 mt-0.5">
                          🎬 Segment: {content.video_start_time || 0}s - {content.video_end_time ? `${content.video_end_time}s` : 'end'}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              {assignedContent.length === 0 && (
                <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                  <FileImage className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>No content assigned</p>
                  <p className="text-xs mt-1">Click content from left to assign</p>
                </div>
              )}
            </div>
          </div>
        </div>
    </Modal>
  )
}
