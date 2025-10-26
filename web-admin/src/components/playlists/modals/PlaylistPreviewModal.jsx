import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { playlistsAPI } from '../../../services/api'
import { Modal, ModalFooter, Button, Thumbnail } from '../../shared'
import { Play, Pause, SkipForward, SkipBack, Monitor, Clock, Image as ImageIcon, Video, FileText } from 'lucide-react'

/**
 * PlaylistPreviewModal Component
 * Modal for previewing playlist content with simulated playback
 *
 * Features:
 * - Shows all content items in order
 * - Visual preview of current item
 * - Playback controls (play/pause, next/previous)
 * - Duration display and progress
 * - Content type icons
 * - Auto-advance simulation
 *
 * @param {Object} playlist - Playlist object to preview
 * @param {Function} onClose - Callback when modal should close
 */
export default function PlaylistPreviewModal({ playlist, onClose }) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [progress, setProgress] = useState(0)

  // Fetch playlist content
  const { data: contentData, isLoading } = useQuery({
    queryKey: ['playlists', playlist.id, 'content'],  // Match with PlaylistContentModal
    queryFn: () => playlistsAPI.getContent(playlist.id).then(res => res.data),
  })

  const items = contentData?.items || []
  const currentItem = items[currentIndex]

  // Auto-advance simulation
  useEffect(() => {
    if (!isPlaying || !currentItem) return

    const duration = currentItem.duration || 10
    const interval = setInterval(() => {
      setProgress((prev) => {
        const newProgress = prev + (100 / duration)
        if (newProgress >= 100) {
          // Auto advance to next item
          if (currentIndex < items.length - 1) {
            setCurrentIndex((prev) => prev + 1)
            return 0
          } else {
            // End of playlist
            setIsPlaying(false)
            return 100
          }
        }
        return newProgress
      })
    }, 1000)

    return () => clearInterval(interval)
  }, [isPlaying, currentItem, currentIndex, items.length])

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying)
  }

  const handleNext = () => {
    if (currentIndex < items.length - 1) {
      setCurrentIndex(currentIndex + 1)
      setProgress(0)
    }
  }

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1)
      setProgress(0)
    }
  }

  const handleSelectItem = (index) => {
    setCurrentIndex(index)
    setProgress(0)
    setIsPlaying(false)
  }

  const getContentIcon = (type) => {
    switch (type) {
      case 'video':
        return <Video className="w-4 h-4" />
      case 'image':
        return <ImageIcon className="w-4 h-4" />
      case 'html':
        return <FileText className="w-4 h-4" />
      default:
        return <Monitor className="w-4 h-4" />
    }
  }

  const formatDuration = (seconds) => {
    if (!seconds) return '0s'
    if (seconds < 60) return `${seconds}s`
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`
  }

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={
        <div className="flex items-center gap-2">
          <Monitor className="w-6 h-6 text-purple-600" />
          <span>Preview Playlist: {playlist.name}</span>
        </div>
      }
      size="2xl"
    >
      <div className="space-y-4">
        {/* Loading State */}
        {isLoading && (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && items.length === 0 && (
          <div className="text-center py-12">
            <Monitor className="w-16 h-16 text-gray-400 dark:text-gray-500 mx-auto mb-4" />
            <p className="text-gray-600 dark:text-gray-400 mb-2">No content in this playlist</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">Add content to see preview</p>
          </div>
        )}

        {/* Preview Player */}
        {!isLoading && items.length > 0 && (
          <>
            {/* Current Item Display */}
            <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-lg overflow-hidden relative">
              {/* Media Preview */}
              <div className="aspect-video bg-black relative">
                {currentItem && (
                  <Thumbnail
                    content={{
                      id: currentItem.content_id,
                      content_type: currentItem.content_type,
                      title: currentItem.content_name
                    }}
                    size="xl"
                    aspectRatio="video"
                    showPlayIcon={true}
                    className="w-full h-full"
                  />
                )}
              </div>

              {/* Content Info Overlay */}
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4 text-white">
                <div className="flex items-center gap-2 mb-1">
                  {getContentIcon(currentItem?.content_type)}
                  <span className="text-xs text-gray-300 uppercase">
                    {currentItem?.content_type || 'Unknown'}
                  </span>
                </div>
                <h3 className="text-lg font-bold mb-1">
                  {currentItem?.content_name || 'Untitled'}
                </h3>
                <p className="text-sm text-gray-300 flex items-center gap-2">
                  <Clock className="w-3 h-3" />
                  Duration: {formatDuration(currentItem?.duration)}
                </p>
              </div>

              {/* Progress Bar */}
              <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-700">
                <div
                  className="h-full bg-purple-500 transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>

              {/* Item Counter */}
              <div className="absolute top-4 right-4 bg-black bg-opacity-70 px-3 py-1 rounded-full text-sm text-white font-semibold">
                {currentIndex + 1} / {items.length}
              </div>
            </div>

            {/* Playback Controls */}
            <div className="flex items-center justify-center gap-4">
              <Button
                variant="secondary"
                size="sm"
                onClick={handlePrevious}
                disabled={currentIndex === 0}
                leftIcon={<SkipBack className="w-4 h-4" />}
              >
                Previous
              </Button>
              <Button
                variant="primary"
                size="lg"
                onClick={handlePlayPause}
                leftIcon={isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
              >
                {isPlaying ? 'Pause' : 'Play'}
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={handleNext}
                disabled={currentIndex === items.length - 1}
                leftIcon={<SkipForward className="w-4 h-4" />}
              >
                Next
              </Button>
            </div>

            {/* Playlist Items List */}
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
              <div className="bg-gray-50 dark:bg-gray-900 px-4 py-2 border-b border-gray-200 dark:border-gray-700">
                <p className="font-semibold text-gray-700 dark:text-gray-300 text-sm">
                  Playlist Content ({items.length} items)
                </p>
              </div>
              <div className="max-h-64 overflow-y-auto">
                {items.map((item, index) => (
                  <button
                    key={item.id}
                    onClick={() => handleSelectItem(index)}
                    className={`w-full px-4 py-3 flex items-center gap-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-left ${
                      currentIndex === index ? 'bg-purple-50 border-l-4 border-purple-500' : ''
                    }`}
                  >
                    {/* Index */}
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold ${
                      currentIndex === index
                        ? 'bg-purple-500 text-white'
                        : 'bg-gray-200 text-gray-600'
                    }`}>
                      {index + 1}
                    </div>

                    {/* Content Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-gray-400 dark:text-gray-500">
                          {getContentIcon(item.content_type)}
                        </span>
                        <p className="font-medium text-gray-800 dark:text-gray-100 truncate">
                          {item.content_name}
                        </p>
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatDuration(item.duration)}
                      </p>
                    </div>

                    {/* Playing Indicator */}
                    {currentIndex === index && isPlaying && (
                      <div className="flex items-center gap-1">
                        <div className="w-1 h-4 bg-purple-500 animate-pulse"></div>
                        <div className="w-1 h-6 bg-purple-500 animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                        <div className="w-1 h-4 bg-purple-500 animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Info Box */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800">
              <p className="font-semibold mb-1">ℹ️ Preview Information</p>
              <ul className="list-disc list-inside space-y-1 text-xs">
                <li>This is a simulated preview of how content will play</li>
                <li>Actual playback on devices may vary based on device settings</li>
                <li>Use play/pause controls to simulate content transitions</li>
              </ul>
            </div>
          </>
        )}

        {/* Footer */}
        <ModalFooter>
          <Button variant="secondary" onClick={onClose} className="flex-1">
            Close
          </Button>
        </ModalFooter>
      </div>
    </Modal>
  )
}
