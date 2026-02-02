/**
 * ATLAS_SEMAR Frontend - Assistant Control Component
 * Follows PANDAWA Clean Architecture standards
 */
import { useState } from 'react'

export default function AssistantControl() {
  const [isRecording, setIsRecording] = useState(false)
  const [transcript, setTranscript] = useState('')

  const handleStartRecording = () => {
    setIsRecording(true)
    // TODO: Implement voice recording logic
    console.log('Recording started')
  }

  const handleStopRecording = () => {
    setIsRecording(false)
    // TODO: Implement stop recording and send to backend
    console.log('Recording stopped')
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold mb-4">Voice Assistant</h2>

        <div className="flex flex-col items-center space-y-4">
          {/* Microphone button */}
          <button
            onClick={isRecording ? handleStopRecording : handleStartRecording}
            className={`w-32 h-32 rounded-full flex items-center justify-center transition-colors ${
              isRecording
                ? 'bg-red-500 hover:bg-red-600'
                : 'bg-blue-500 hover:bg-blue-600'
            }`}
          >
            <svg
              className="w-16 h-16 text-white"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z"
                clipRule="evenodd"
              />
            </svg>
          </button>

          {/* Status */}
          <p className="text-lg font-medium">
            {isRecording ? 'Recording...' : 'Click to start'}
          </p>

          {/* Transcript */}
          {transcript && (
            <div className="w-full mt-4 p-4 bg-gray-50 rounded">
              <h3 className="font-medium mb-2">Transcript:</h3>
              <p className="text-gray-700">{transcript}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
