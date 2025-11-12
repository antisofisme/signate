/**
 * WebSocket Status Indicator
 * Shows connection status in UI
 */

import React from 'react'
import { useWebSocketStatus } from './useWebSocket'

interface WebSocketStatusProps {
  showText?: boolean
  className?: string
}

export function WebSocketStatus({ showText = true, className = '' }: WebSocketStatusProps) {
  const { state, isConnected, isConnecting, isError } = useWebSocketStatus()

  // Determine color based on state
  const getStatusColor = () => {
    if (isConnected) return 'bg-green-500'
    if (isConnecting) return 'bg-yellow-500 animate-pulse'
    if (isError) return 'bg-red-500'
    return 'bg-gray-400'
  }

  // Get status text
  const getStatusText = () => {
    if (isConnected) return 'Real-time Connected'
    if (isConnecting) return 'Connecting...'
    if (isError) return 'Connection Error'
    return 'Disconnected'
  }

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {/* Status dot */}
      <div className="relative">
        <div className={`w-2 h-2 rounded-full ${getStatusColor()}`} />
        {isConnected && (
          <div className="absolute inset-0 w-2 h-2 rounded-full bg-green-500 animate-ping opacity-75" />
        )}
      </div>

      {/* Status text */}
      {showText && (
        <span className="text-xs text-gray-600 dark:text-gray-400">
          {getStatusText()}
        </span>
      )}
    </div>
  )
}
