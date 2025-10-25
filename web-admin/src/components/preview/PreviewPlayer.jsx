import { useEffect, useRef, useState } from 'react'
import { Film, Image as ImageIcon, AlertCircle } from 'lucide-react'

/**
 * PreviewPlayer Component
 * Plays video or image content with auto-advance
 *
 * Props:
 * - content: Current content object to display
 * - isPlaying: Whether playback is active
 * - onContentEnd: Callback when content finishes playing
 */
export default function PreviewPlayer({ content, isPlaying, onContentEnd }) {
  const videoRef = useRef(null)
  const [timeRemaining, setTimeRemaining] = useState(0)
  const [error, setError] = useState(null)
  const playbackTimerRef = useRef(null)

  // Handle video playback with duration limit
  useEffect(() => {
    if (!content) return

    if (content.content_type === 'video' && videoRef.current) {
      const video = videoRef.current

      // Clear any existing timer
      if (playbackTimerRef.current) {
        clearTimeout(playbackTimerRef.current)
        playbackTimerRef.current = null
      }

      if (isPlaying) {
        // Set video to start from beginning
        video.currentTime = 0

        // Play video
        video.play().catch(err => {
          console.error('Failed to play video:', err)
        })

        // Set timer to stop video after specified duration
        if (content.duration > 0) {
          playbackTimerRef.current = setTimeout(() => {
            video.pause()
            onContentEnd()
          }, content.duration * 1000)
        }
      } else {
        video.pause()
      }
    }

    // Cleanup timer on unmount or content change
    return () => {
      if (playbackTimerRef.current) {
        clearTimeout(playbackTimerRef.current)
        playbackTimerRef.current = null
      }
    }
  }, [content, isPlaying, onContentEnd])

  // Handle video errors
  const handleVideoError = (e) => {
    console.error('Video error:', e)
    const video = videoRef.current
    if (video && video.error) {
      let errorMsg = 'Failed to load video'
      switch (video.error.code) {
        case 1: errorMsg = 'Video loading aborted'; break
        case 2: errorMsg = 'Network error while loading video'; break
        case 3: errorMsg = 'Video decoding failed'; break
        case 4: errorMsg = 'Video format not supported'; break
      }
      setError(errorMsg)
    } else {
      setError('Failed to load video')
    }
  }

  // Handle image timer
  useEffect(() => {
    if (!content || content.content_type !== 'image') return

    setTimeRemaining(content.duration)

    if (!isPlaying) return

    const timer = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 1) {
          clearInterval(timer)
          onContentEnd()
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [content, isPlaying, onContentEnd])

  if (!content) {
    return (
      <div className="text-gray-400 text-center">
        <Film className="w-16 h-16 mx-auto mb-4" />
        <p>No content selected</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-red-400 text-center p-8">
        <AlertCircle className="w-16 h-16 mx-auto mb-4" />
        <p className="text-xl font-semibold mb-2">Playback Error</p>
        <p className="text-sm">{error}</p>
      </div>
    )
  }

  // Render video
  if (content.content_type === 'video' || content.content_type === 'webpage') {
    return (
      <div className="relative w-full h-full flex items-center justify-center bg-black">
        <video
          ref={videoRef}
          src={content.anthias_url}
          className="w-full h-full object-contain"
          onError={handleVideoError}
          controls={false}
          playsInline
          muted={false}
        />

        {/* Video Info Overlay */}
        <div className="absolute bottom-4 left-4 bg-black/70 px-4 py-2 rounded-lg">
          <p className="text-white text-sm font-medium flex items-center gap-2">
            <Film className="w-4 h-4" />
            {content.title}
          </p>
          <p className="text-white text-xs mt-1 opacity-75">
            Duration: {content.duration}s
          </p>
        </div>
      </div>
    )
  }

  // Render image
  if (content.content_type === 'image') {
    return (
      <div className="relative w-full h-full flex items-center justify-center bg-black">
        <img
          src={content.anthias_url}
          alt={content.title}
          className="w-full h-full object-contain"
          onError={(e) => {
            console.error('Image error:', e)
            setError(`Failed to load image: ${content.title}`)
          }}
        />

        {/* Image Info Overlay */}
        <div className="absolute bottom-4 left-4 bg-black/70 px-4 py-2 rounded-lg">
          <p className="text-white text-sm font-medium flex items-center gap-2">
            <ImageIcon className="w-4 h-4" />
            {content.title}
          </p>
        </div>

        {/* Timer Overlay */}
        {isPlaying && timeRemaining > 0 && (
          <div className="absolute top-4 right-4 bg-black/70 px-4 py-2 rounded-lg">
            <p className="text-white text-sm font-mono">
              {timeRemaining}s
            </p>
          </div>
        )}

        {/* Progress Bar */}
        {isPlaying && content.duration > 0 && (
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-700">
            <div
              className="h-full bg-blue-500 transition-all duration-1000 ease-linear"
              style={{
                width: `${((content.duration - timeRemaining) / content.duration) * 100}%`
              }}
            />
          </div>
        )}
      </div>
    )
  }

  // Unsupported content type
  return (
    <div className="text-gray-400 text-center p-8">
      <AlertCircle className="w-16 h-16 mx-auto mb-4" />
      <p className="text-xl font-semibold mb-2">Unsupported Content Type</p>
      <p className="text-sm">{content.content_type}</p>
    </div>
  )
}
