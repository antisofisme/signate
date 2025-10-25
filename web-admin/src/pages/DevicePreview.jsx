import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { devicesAPI } from '../services/api'
import { ArrowLeft, Play, Pause, SkipBack, SkipForward, RotateCcw, AlertCircle } from 'lucide-react'
import PreviewPlayer from '../components/preview/PreviewPlayer'
import SequenceList from '../components/preview/SequenceList'
import { Button } from '../components/shared'

/**
 * DevicePreview Page
 * Full-screen preview of device content playback
 *
 * Features:
 * - Real-time content preview
 * - Auto-advance playback
 * - Sequence list with source badges
 * - Playback controls
 * - Warning/conflict display
 */
export default function DevicePreview() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [currentIndex, setCurrentIndex] = useState(0)
  const [isPlaying, setIsPlaying] = useState(true)

  // Fetch preview data from backend
  const { data: previewData, isLoading, error } = useQuery({
    queryKey: ['devices', id, 'preview'],
    queryFn: () => devicesAPI.preview(id).then(res => res.data),
    refetchInterval: false,
  })

  // Auto-advance to next content
  const handleContentEnd = () => {
    if (previewData?.content_sequence && isPlaying) {
      const nextIndex = (currentIndex + 1) % previewData.content_sequence.length
      setCurrentIndex(nextIndex)
    }
  }

  // Playback controls
  const handlePrev = () => {
    if (previewData?.content_sequence) {
      const prevIndex = currentIndex === 0
        ? previewData.content_sequence.length - 1
        : currentIndex - 1
      setCurrentIndex(prevIndex)
    }
  }

  const handleNext = () => {
    if (previewData?.content_sequence) {
      const nextIndex = (currentIndex + 1) % previewData.content_sequence.length
      setCurrentIndex(nextIndex)
    }
  }

  const handleRestart = () => {
    setCurrentIndex(0)
    setIsPlaying(true)
  }

  const handleJumpTo = (index) => {
    setCurrentIndex(index)
  }

  // Get current content
  const currentContent = previewData?.content_sequence?.[currentIndex]

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading preview...</div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-white text-2xl mb-2">Failed to load preview</h2>
          <p className="text-gray-400 mb-6">{error.message}</p>
          <Button onClick={() => navigate('/devices')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Devices
          </Button>
        </div>
      </div>
    )
  }

  // No content state
  if (!previewData?.content_sequence || previewData.content_sequence.length === 0) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
          <h2 className="text-white text-2xl mb-2">No Content Assigned</h2>
          <p className="text-gray-400 mb-6">
            This device has no content to preview. Please assign content first.
          </p>
          <Button onClick={() => navigate('/devices')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Devices
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/devices')}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-6 h-6" />
            </button>
            <div>
              <h1 className="text-2xl font-bold">
                🎬 Preview: {previewData.device_name}
              </h1>
              <p className="text-sm text-gray-400 mt-1">
                {previewData.content_sequence.length} content items •
                Total duration: {Math.floor(previewData.total_duration_seconds / 60)}m {previewData.total_duration_seconds % 60}s •
                ~{previewData.loops_per_hour} loops/hour
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Warning/Alert Display */}
      {previewData.warnings && previewData.warnings.length > 0 && (
        <div className="bg-yellow-900/50 border-b border-yellow-700/50 px-6 py-3">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-semibold text-yellow-200 mb-1">Warnings</h3>
              <ul className="space-y-1">
                {previewData.warnings.map((warning, idx) => (
                  <li key={idx} className="text-sm text-yellow-100">
                    {warning.message}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex h-[calc(100vh-140px)]">
        {/* Left Side - Preview Player */}
        <div className="flex-1 flex flex-col">
          <div className="flex-1 bg-black flex items-center justify-center">
            <PreviewPlayer
              content={currentContent}
              isPlaying={isPlaying}
              onContentEnd={handleContentEnd}
            />
          </div>

          {/* Playback Controls */}
          <div className="bg-gray-800 border-t border-gray-700 px-6 py-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex-1">
                <h3 className="font-semibold text-lg">
                  {currentContent?.title || 'Unknown Content'}
                </h3>
                <p className="text-sm text-gray-400">
                  Playing: {currentIndex + 1}/{previewData.content_sequence.length} •
                  Duration: {currentContent?.duration}s •
                  Source: {currentContent?.source?.name || 'Unknown'}
                </p>
              </div>
            </div>

            {/* Control Buttons */}
            <div className="flex items-center justify-center gap-4">
              <button
                onClick={handleRestart}
                className="p-3 rounded-full bg-gray-700 hover:bg-gray-600 transition-colors"
                title="Restart from beginning"
              >
                <RotateCcw className="w-5 h-5" />
              </button>
              <button
                onClick={handlePrev}
                className="p-3 rounded-full bg-gray-700 hover:bg-gray-600 transition-colors"
                title="Previous content"
              >
                <SkipBack className="w-5 h-5" />
              </button>
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className="p-4 rounded-full bg-blue-600 hover:bg-blue-700 transition-colors"
                title={isPlaying ? 'Pause' : 'Play'}
              >
                {isPlaying ? (
                  <Pause className="w-6 h-6" />
                ) : (
                  <Play className="w-6 h-6" />
                )}
              </button>
              <button
                onClick={handleNext}
                className="p-3 rounded-full bg-gray-700 hover:bg-gray-600 transition-colors"
                title="Next content"
              >
                <SkipForward className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Right Side - Sequence List */}
        <div className="w-96 bg-gray-800 border-l border-gray-700 overflow-y-auto">
          <SequenceList
            sequence={previewData.content_sequence}
            currentIndex={currentIndex}
            onJumpTo={handleJumpTo}
          />
        </div>
      </div>
    </div>
  )
}
