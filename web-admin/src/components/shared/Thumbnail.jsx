import { useState, useRef } from 'react'
import { FileImage, Film } from 'lucide-react'
import { API_BASE_URL } from '../../utils/constants'

/**
 * Thumbnail Component
 * Reusable thumbnail component for displaying content media (images/videos)
 *
 * Features:
 * - Supports both image and video content types
 * - Multiple size variants (sm, md, lg, xl)
 * - Multiple aspect ratio variants (video, square, portrait, auto)
 * - Loading states with skeleton
 * - Error handling with fallback icons
 * - Play icon overlay for videos
 * - Uses design tokens for consistent styling
 * - Centralized API endpoint
 *
 * @param {Object} content - Content object with id, content_type, title
 * @param {string} size - Size variant: 'sm' | 'md' | 'lg' | 'xl' (default: 'md')
 * @param {string} aspectRatio - Aspect ratio: 'video' | 'square' | 'portrait' | 'auto' (default: 'video')
 * @param {boolean} showPlayIcon - Show play icon overlay for videos (default: true)
 * @param {string} className - Additional CSS classes
 * @param {Function} onClick - Click handler
 */
export default function Thumbnail({
  content,
  size = 'md',
  aspectRatio = 'video',
  showPlayIcon = true,
  className = '',
  onClick
}) {
  const [hasError, setHasError] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isPlaying, setIsPlaying] = useState(false)
  const videoRef = useRef(null)

  // Get media URL based on content type
  const getMediaUrl = () => {
    if (content.content_type === 'video') {
      return `${API_BASE_URL}/api/content/${content.id}/video`
    }
    return `${API_BASE_URL}/api/content/${content.id}/image`
  }

  // Handle video play/pause toggle
  const handleVideoToggle = (e) => {
    e.stopPropagation()
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause()
        setIsPlaying(false)
      } else {
        videoRef.current.play()
        setIsPlaying(true)
      }
    }
  }

  // Size variants using design tokens
  const sizeClasses = {
    sm: 'h-24',      // 96px - Small thumbnails in lists
    md: 'h-32',      // 128px - Default size for cards
    lg: 'h-48',      // 192px - Large thumbnails in modals
    xl: 'h-64',      // 256px - Extra large for preview
  }

  // Aspect ratio variants
  const aspectRatioClasses = {
    video: 'aspect-video',      // 16:9 - Default for video content
    square: 'aspect-square',    // 1:1 - Square thumbnails
    portrait: 'aspect-[3/4]',   // 3:4 - Portrait orientation
    auto: 'h-auto',             // Auto height based on content
  }

  // Fallback icon size based on thumbnail size
  const iconSizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-12 h-12',
    lg: 'w-16 h-16',
    xl: 'w-20 h-20',
  }

  const mediaUrl = getMediaUrl()
  const isVideo = content.content_type === 'video'

  // Error state - show fallback icon
  if (hasError) {
    return (
      <div
        className={`
          relative bg-gradient-to-br from-gray-200 to-gray-300 dark:from-gray-700 dark:to-gray-800
          rounded-lg overflow-hidden flex items-center justify-center
          ${aspectRatioClasses[aspectRatio]}
          ${className}
        `}
        onClick={onClick}
      >
        <div className="flex flex-col items-center justify-center text-gray-500 dark:text-gray-400">
          {isVideo ? (
            <Film className={iconSizeClasses[size]} />
          ) : (
            <FileImage className={iconSizeClasses[size]} />
          )}
          <span className="text-xs mt-2">
            {isVideo ? 'Video' : 'Image'}
          </span>
        </div>

        {/* Play icon overlay for videos */}
        {isVideo && showPlayIcon && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="bg-black bg-opacity-50 rounded-full p-3">
              <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z"/>
              </svg>
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div
      className={`
        relative bg-gradient-to-br from-gray-200 to-gray-300 dark:from-gray-700 dark:to-gray-800
        rounded-lg overflow-hidden
        ${aspectRatioClasses[aspectRatio]}
        ${className}
      `}
      onClick={onClick}
    >
      {/* Loading skeleton */}
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-200 dark:bg-gray-600 animate-pulse">
          <div className="text-gray-400 dark:text-gray-500">
            {isVideo ? (
              <Film className={iconSizeClasses[size]} />
            ) : (
              <FileImage className={iconSizeClasses[size]} />
            )}
          </div>
        </div>
      )}

      {/* Media content */}
      {isVideo ? (
        <video
          ref={videoRef}
          src={mediaUrl}
          className="w-full h-full object-contain"
          preload="metadata"
          muted
          playsInline
          loop
          onLoadedMetadata={(e) => {
            try {
              e.target.currentTime = 0.1 // Load first frame
              setIsLoading(false)
            } catch (err) {
              console.error('Error seeking video:', err)
              setHasError(true)
            }
          }}
          onError={(e) => {
            console.error('Video load error:', e)
            setHasError(true)
            setIsLoading(false)
          }}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          onClick={handleVideoToggle}
        />
      ) : (
        <img
          src={mediaUrl}
          alt={content.title}
          className="w-full h-full object-contain"
          onLoad={() => setIsLoading(false)}
          onError={(e) => {
            console.error('Image load error:', e)
            setHasError(true)
            setIsLoading(false)
          }}
        />
      )}

      {/* Play/Pause icon overlay for videos */}
      {isVideo && showPlayIcon && !isLoading && !hasError && (
        <div
          className="absolute inset-0 flex items-center justify-center cursor-pointer transition-opacity hover:opacity-100"
          style={{ opacity: isPlaying ? 0 : 1 }}
          onClick={handleVideoToggle}
        >
          <div className="bg-black bg-opacity-50 rounded-full p-3 transition-transform hover:scale-110 pointer-events-none">
            {isPlaying ? (
              <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
                <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
              </svg>
            ) : (
              <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z"/>
              </svg>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
