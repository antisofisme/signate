import { useState } from 'react'
import { API_BASE_URL } from '../../utils/constants'

/**
 * VideoThumbnail Component
 * Displays video thumbnail with error handling and loading states
 *
 * Features:
 * - Shows first frame of video as thumbnail
 * - Play icon overlay
 * - Loading placeholder while video loads
 * - Fallback icon if video fails to load
 * - Error handling for video load failures
 */

// Helper function to get proxy video URL
const getVideoUrl = (content) => {
  // Use backend proxy endpoint which serves videos with correct Content-Type and avoids CORS issues
  return `${API_BASE_URL}/api/content/${content.id}/video`
}

export default function VideoThumbnail({ content }) {
  const [hasError, setHasError] = useState(false)
  const [isLoaded, setIsLoaded] = useState(false)
  const videoUrl = getVideoUrl(content)

  if (hasError) {
    // Show fallback icon if video fails to load
    return (
      <>
        <div className="flex flex-col items-center justify-center">
          <svg className="w-16 h-16 text-gray-400 dark:text-gray-500 mb-2" fill="currentColor" viewBox="0 0 24 24">
            <path d="M17 10.5V7c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4z"/>
          </svg>
          <span className="text-xs text-gray-500 dark:text-gray-400">Video</span>
        </div>
        {/* Play icon overlay */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="bg-black bg-opacity-50 rounded-full p-4">
            <svg className="w-12 h-12 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z"/>
            </svg>
          </div>
        </div>
      </>
    )
  }

  return (
    <>
      {/* Video element with error handling */}
      <video
        src={videoUrl}
        className="w-full h-full object-cover"
        preload="metadata"
        muted
        playsInline
        onLoadedMetadata={(e) => {
          // Successfully loaded metadata, seek to first frame
          try {
            e.target.currentTime = 0.1
            setIsLoaded(true)
          } catch (err) {
            console.error('Error seeking video:', err)
            setHasError(true)
          }
        }}
        onError={(e) => {
          console.error('Video load error for content:', content.id, videoUrl, e)
          setHasError(true)
        }}
        style={{ display: isLoaded || !hasError ? 'block' : 'none' }}
      />

      {/* Loading placeholder while video loads */}
      {!isLoaded && !hasError && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="flex flex-col items-center">
            <svg className="w-12 h-12 text-gray-400 dark:text-gray-500 animate-pulse" fill="currentColor" viewBox="0 0 24 24">
              <path d="M17 10.5V7c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4z"/>
            </svg>
          </div>
        </div>
      )}

      {/* Play icon overlay */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="bg-black bg-opacity-50 rounded-full p-4">
          <svg className="w-12 h-12 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 5v14l11-7z"/>
          </svg>
        </div>
      </div>
    </>
  )
}
