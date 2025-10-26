import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { X } from 'lucide-react'
import { contentAPI, devicesAPI, tagsAPI } from '../../../services/api'
import { API_BASE_URL } from '../../../utils/constants'
import { Modal, ModalFooter, Button } from '../../shared'

/**
 * Helper function to get proxy image URL
 */
const getImageUrl = (content) => {
  return `${API_BASE_URL}/api/content/${content.id}/image`
}

/**
 * Helper function to get proxy video URL
 */
const getVideoUrl = (content) => {
  return `${API_BASE_URL}/api/content/${content.id}/video`
}

/**
 * ModalVideoPlayer Component
 * Video player for modal with comprehensive error handling
 */
function ModalVideoPlayer({ content }) {
  const [hasError, setHasError] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const videoUrl = getVideoUrl(content)

  if (hasError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[300px] bg-gray-900 text-white rounded-lg p-8">
        <svg className="w-20 h-20 text-red-400 mb-4" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
        </svg>
        <h3 className="text-xl font-bold mb-2">Cannot Play Video</h3>
        <p className="text-sm text-gray-300 mb-4 text-center max-w-md">{errorMessage}</p>
        <div className="bg-gray-800 p-3 rounded text-xs font-mono text-left w-full max-w-md">
          <p className="text-gray-400 dark:text-gray-500">Proxy URL: {videoUrl}</p>
          <p className="text-gray-400 dark:text-gray-500 mt-1">Original URL: {content.anthias_url}</p>
          <p className="text-gray-400 dark:text-gray-500 mt-1">Type: {content.mime_type || 'unknown'}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="relative bg-black rounded-lg overflow-hidden">
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
          <div className="text-white text-center">
            <svg className="w-12 h-12 mx-auto mb-3 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p className="text-sm">Loading video...</p>
          </div>
        </div>
      )}
      <video
        controls
        autoPlay={false}
        preload="auto"
        className="w-full h-auto max-h-[60vh]"
        style={{ minHeight: '300px' }}
        onLoadStart={() => {
          console.log('Video loading started (proxy):', videoUrl)
          console.log('Original Anthias URL:', content.anthias_url)
          setIsLoading(true)
        }}
        onLoadedMetadata={(e) => {
          console.log('Video metadata loaded:', {
            duration: e.target.duration,
            videoWidth: e.target.videoWidth,
            videoHeight: e.target.videoHeight
          })
          setIsLoading(false)
        }}
        onCanPlay={() => {
          console.log('Video can play')
          setIsLoading(false)
        }}
        onError={(e) => {
          console.error('Video error:', e.target.error)
          console.error('Error code:', e.target.error?.code)
          console.error('Error message:', e.target.error?.message)
          console.error('Proxy Video URL:', videoUrl)
          console.error('Original Anthias URL:', content.anthias_url)

          let errorMsg = 'Unable to load video. '
          if (e.target.error?.code === 4) {
            errorMsg += 'Video format not supported or file not found.'
          } else if (e.target.error?.code === 2) {
            errorMsg += 'Network error while loading video.'
          } else if (e.target.error?.code === 3) {
            errorMsg += 'Video decoding failed.'
          } else {
            errorMsg += 'Unknown error occurred.'
          }

          setErrorMessage(errorMsg)
          setHasError(true)
          setIsLoading(false)
        }}
      >
        <source src={videoUrl} type={content.mime_type || 'video/mp4'} />
        Your browser does not support the video tag.
      </video>
    </div>
  )
}

/**
 * PreviewModal Component
 * Full content preview modal with media display, metadata, and assignments
 *
 * Features:
 * - Image/video preview with error handling
 * - Comprehensive media metadata display (resolution, codec, fps, bitrate, etc.)
 * - File information (size, MIME type, created date)
 * - Assignment information (devices/tags this content is assigned to)
 * - Click outside to close
 * - Responsive layout with scrollable content
 *
 * @param {Object} content - Content object to preview
 * @param {Function} onClose - Callback when modal should close
 */
export default function PreviewModal({ content, onClose }) {
  const imageUrl = getImageUrl(content)
  console.log('PreviewModal - Image URL:', imageUrl)
  console.log('PreviewModal - Content:', content)

  // Fetch assignments for this content
  const { data: assignmentsData } = useQuery({
    queryKey: ['content-assignments', content.id],
    queryFn: () => contentAPI.getAssignments(content.id).then(res => res.data),
  })

  // Fetch devices and tags to show names
  const { data: devicesData } = useQuery({
    queryKey: ['devices', 'active'],
    queryFn: () => devicesAPI.list({ status: 'active' }).then(res => res.data),
  })

  const { data: tagsData } = useQuery({
    queryKey: ['tags'],
    queryFn: () => tagsAPI.list().then(res => res.data),
  })

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      size="4xl"
      showCloseButton={false}
      bodyClassName="flex-1 overflow-hidden flex flex-col p-0"
    >
      {/* Custom Header - Fixed */}
      <div className="flex items-center justify-between px-6 py-4 bg-white dark:bg-gray-800 border-b flex-shrink-0">
        <div>
          <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100">{content.title}</h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            {content.content_type.toUpperCase()} • {content.duration}s • {content.is_active ? 'Active' : 'Inactive'}
          </p>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 dark:text-gray-500 hover:text-gray-600 transition-colors p-1 rounded-lg hover:bg-gray-100"
          aria-label="Close modal"
        >
          <X className="w-6 h-6" />
        </button>
      </div>

      {/* Content Preview - Scrollable */}
      <div className="flex-1 overflow-y-auto p-6">
          {/* Media Display */}
          <div className="mb-6">
            {content.content_type === 'image' ? (
              <div className="bg-gray-100 dark:bg-gray-700 rounded-lg overflow-hidden min-h-[300px] flex items-center justify-center">
                <img
                  src={imageUrl}
                  alt={content.title}
                  className="w-full h-auto max-h-[60vh] object-contain"
                  style={{ minHeight: '200px' }}
                  onLoad={() => console.log('Image loaded successfully')}
                  onError={(e) => {
                    console.error('Image load error:', e)
                    e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300"><rect fill="%23ddd" width="400" height="300"/><text fill="%23999" x="50%" y="50%" text-anchor="middle" dy=".3em">Image not available</text></svg>'
                  }}
                />
              </div>
            ) : (
              <ModalVideoPlayer content={content} />
            )}
          </div>

          {/* Details */}
          <div className="space-y-4">
            {content.description && (
              <div>
                <h3 className="font-semibold text-gray-700 dark:text-gray-300 mb-1">Description</h3>
                <p className="text-gray-600 dark:text-gray-400">{content.description}</p>
              </div>
            )}

            {/* Media Metadata Section */}
            {(content.resolution || content.codec || content.fps || content.bitrate) && (
              <div className="border-t pt-4">
                <h3 className="font-semibold text-gray-700 dark:text-gray-300 mb-3">Media Information</h3>
                <div className="grid grid-cols-2 gap-3">
                  {content.resolution && (
                    <div className="bg-gray-50 dark:bg-gray-900 p-3 rounded">
                      <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Resolution</div>
                      <div className="font-semibold text-gray-800 dark:text-gray-100">{content.resolution}</div>
                    </div>
                  )}
                  {content.codec && (
                    <div className="bg-gray-50 dark:bg-gray-900 p-3 rounded">
                      <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Codec</div>
                      <div className="font-semibold text-gray-800 dark:text-gray-100 uppercase">{content.codec}</div>
                    </div>
                  )}
                  {content.fps && (
                    <div className="bg-gray-50 dark:bg-gray-900 p-3 rounded">
                      <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Frame Rate</div>
                      <div className="font-semibold text-gray-800 dark:text-gray-100">{content.fps} fps</div>
                    </div>
                  )}
                  {content.bitrate && (
                    <div className="bg-gray-50 dark:bg-gray-900 p-3 rounded">
                      <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Bitrate</div>
                      <div className="font-semibold text-gray-800 dark:text-gray-100">{content.bitrate} kbps</div>
                    </div>
                  )}
                  {content.video_duration && (
                    <div className="bg-gray-50 dark:bg-gray-900 p-3 rounded">
                      <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Video Duration</div>
                      <div className="font-semibold text-gray-800 dark:text-gray-100">{content.video_duration.toFixed(2)}s</div>
                    </div>
                  )}
                  {content.audio_codec && (
                    <div className="bg-gray-50 dark:bg-gray-900 p-3 rounded">
                      <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Audio Codec</div>
                      <div className="font-semibold text-gray-800 dark:text-gray-100 uppercase">{content.audio_codec}</div>
                    </div>
                  )}
                  {content.audio_bitrate && (
                    <div className="bg-gray-50 dark:bg-gray-900 p-3 rounded">
                      <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Audio Bitrate</div>
                      <div className="font-semibold text-gray-800 dark:text-gray-100">{content.audio_bitrate} kbps</div>
                    </div>
                  )}
                  {content.audio_sample_rate && (
                    <div className="bg-gray-50 dark:bg-gray-900 p-3 rounded">
                      <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Sample Rate</div>
                      <div className="font-semibold text-gray-800 dark:text-gray-100">{content.audio_sample_rate} Hz</div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* File Information Section */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h3 className="font-semibold text-gray-700 dark:text-gray-300 mb-1">File Size</h3>
                <p className="text-gray-600 dark:text-gray-400">
                  {content.file_size ? `${(content.file_size / 1024 / 1024).toFixed(2)} MB` : 'N/A'}
                </p>
              </div>
              <div>
                <h3 className="font-semibold text-gray-700 dark:text-gray-300 mb-1">MIME Type</h3>
                <p className="text-gray-600 dark:text-gray-400">{content.mime_type || 'N/A'}</p>
              </div>
              <div>
                <h3 className="font-semibold text-gray-700 dark:text-gray-300 mb-1">Anthias Asset ID</h3>
                <p className="text-gray-600 dark:text-gray-400 text-sm font-mono">{content.anthias_asset_id}</p>
              </div>
              <div>
                <h3 className="font-semibold text-gray-700 dark:text-gray-300 mb-1">Created</h3>
                <p className="text-gray-600 dark:text-gray-400 text-sm">
                  {new Date(content.created_at).toLocaleString()}
                </p>
              </div>
            </div>

            {/* URL */}
            <div>
              <h3 className="font-semibold text-gray-700 dark:text-gray-300 mb-1">Image URL</h3>
              <a
                href={getImageUrl(content)}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline text-sm break-all"
              >
                {getImageUrl(content)}
              </a>
            </div>

            {/* Assignments Section */}
            <div>
              <h3 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">Assigned To</h3>
              {assignmentsData && assignmentsData.length > 0 ? (
                <div className="space-y-2">
                  {assignmentsData.map((assignment) => {
                    // Find device or tag name
                    let displayName = 'Unknown'
                    let displayType = ''
                    let displayColor = 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'

                    if (assignment.device_id) {
                      const device = devicesData?.devices?.find(d => d.id === assignment.device_id)
                      displayName = device ? device.device_name : `Device #${assignment.device_id}`
                      displayType = 'Device'
                      displayColor = 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400'
                    } else if (assignment.tag_id) {
                      const tag = tagsData?.items?.find(t => t.id === assignment.tag_id)
                      displayName = tag ? tag.tag_name : `Tag #${assignment.tag_id}`
                      displayType = 'Tag'
                      displayColor = 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                    }

                    return (
                      <div
                        key={assignment.id}
                        className="flex items-center justify-between bg-gray-50 dark:bg-gray-800 dark:bg-gray-900 p-3 rounded-lg"
                      >
                        <div className="flex items-center gap-3">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${displayColor}`}>
                            {displayType}
                          </span>
                          <span className="font-medium text-gray-800 dark:text-gray-100">{displayName}</span>
                          {assignment.priority > 0 && (
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                              Priority: {assignment.priority}
                            </span>
                          )}
                        </div>
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {new Date(assignment.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg text-center text-gray-500 dark:text-gray-400 text-sm">
                  No assignments yet. Click "Assign" button to assign this content to devices or tags.
                </div>
              )}
            </div>
          </div>
      </div>

      {/* Footer Actions - Fixed */}
      <div className="p-6 border-t bg-gray-50 dark:bg-gray-800 dark:bg-gray-900 flex-shrink-0">
        <ModalFooter align="center">
          <Button onClick={onClose} variant="secondary" className="w-full">
            Close
          </Button>
        </ModalFooter>
      </div>
    </Modal>
  )
}
